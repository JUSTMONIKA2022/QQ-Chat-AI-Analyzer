import os
import json
import time
import threading
import uuid
import logging
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from src.parser import QQChatParser
from src.analyzer import ChatAnalyzer
from src.renderer import HTMLRenderer as ReportRenderer
from src.llm_client import LLMClient
from src.generator import ReportGenerator
from src.history import HistoryManager

# --- Config ---
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'
HISTORY_FILE = 'history.json'
CONFIG_FILE = 'config.json'
ALLOWED_EXTENSIONS = {'json'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# --- Flask App ---
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB limit

# --- Global State for Tasks ---
# In a production app, use Redis/Celery. Here we use a simple dict for local usage.
tasks = {}

history_manager = HistoryManager(HISTORY_FILE)

# --- Helpers ---
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class TaskLogger:
    def __init__(self, task_id):
        self.task_id = task_id
    
    def info(self, msg):
        if self.task_id in tasks:
            tasks[self.task_id]['logs'].append(msg)
            print(f"[Task {self.task_id}] {msg}")

    def progress(self, percent, status_text):
        if self.task_id in tasks:
            tasks[self.task_id]['progress'] = percent
            tasks[self.task_id]['status_text'] = status_text

def smart_sample(df, max_tokens, logger=None):
    """
    智能采样函数，确保不超过 Token 预算。
    """
    # 估算字符限制 (1 Token ≈ 1.5 Chars)
    target_chars = int(max_tokens * 1.5)
    
    # 预处理消息格式
    if 'formatted_msg' not in df.columns:
        df['formatted_msg'] = df.apply(
            lambda x: f"[{str(x['datetime'])[:16]}] {x.get('user_name', 'Unknown')}: {str(x['content'])[:100]}", 
            axis=1
        )
    
    full_text_list = df['formatted_msg'].tolist()
    total_msgs = len(full_text_list)
    
    if total_msgs == 0:
        return ""

    avg_len = sum(len(m) for m in full_text_list[:100]) / min(total_msgs, 100)
    if avg_len == 0: avg_len = 50
    
    estimated_total_chars = total_msgs * avg_len
    
    if estimated_total_chars <= target_chars:
        sampled_msgs = full_text_list
        if logger: logger.info(f"数据量较小 ({estimated_total_chars} chars)，全量发送")
    else:
        target_msg_count = int(target_chars / avg_len)
        step = max(1, total_msgs // target_msg_count)
        sampled_msgs = full_text_list[::step]
        if logger: logger.info(f"数据量过大，执行均匀采样 (Step={step})。从 {total_msgs} 条中抽取 {len(sampled_msgs)} 条。")
        
    return "\n".join(sampled_msgs)

# --- Analysis Worker ---
def run_analysis_task(task_id, file_path, config):
    logger = TaskLogger(task_id)
    try:
        tasks[task_id]['state'] = 'processing'
        logger.progress(5, "正在初始化组件...")
        
        # 1. Parse
        logger.info(f"正在解析文件: {os.path.basename(file_path)}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            parser = QQChatParser()
            df, meta = parser.parse_json(content)
        except Exception as e:
            raise ValueError(f"文件解析失败: {str(e)}")
        
        logger.progress(20, f"解析完成，共加载 {len(df)} 条消息")
        logger.info(f"解析成功: {len(df)} messages")

        # 2. Analyze (Stats)
        logger.progress(30, "正在进行统计分析...")
        analyzer = ChatAnalyzer(df)
        stats = analyzer.get_basic_stats()
        # Merge meta into stats if needed, or keep separate. 
        # analyzer.get_basic_stats() returns dict. 
        # meta contains chat_name.
        stats.update(meta)
        
        daily_activity = analyzer.get_daily_activity()
        logger.progress(40, "统计分析完成")
        logger.info("基础统计完成")

        # 3. AI Analysis (Map-Reduce)
        logger.progress(45, "正在初始化 AI 分析组件...")
        
        llm_config = {}
        # Base config for LLMClient (acts as default)
        if config.get('mode') == 'custom':
            llm_config = {
                'api_key': config.get('api_key'),
                'base_url': config.get('base_url'),
                'model': config.get('model') # Default model
            }
        else:
            logger.info("使用内置演示模式 (Mock)")
            
        # Get specific models for each phase
        model_map = config.get('model_map') or llm_config.get('model')
        model_reduce = config.get('model_reduce') or llm_config.get('model')
        model_refine = config.get('model_refine') or llm_config.get('model')

        client = LLMClient(**llm_config)
        generator = ReportGenerator(client)
        max_tokens = int(config.get('max_tokens', 128000))

        # Step 1: Map (Quarterly/Periodic Analysis)
        logger.info("正在进行切分...")
        splits = analyzer.get_quarterly_splits()
        
        # Detect if it's a periodic split (non-full year)
        is_periodic = False
        if splits and any(k.startswith("Period_") for k in splits.keys()):
            is_periodic = True
            logger.info("检测到非完整年度数据，启用阶段性分析模式")
        
        quarterly_results = []
        
        total_quarters = len(splits)
        if total_quarters == 0:
            logger.info("切分失败，降级为全量分析")
            splits = {"Whole_Year": df}
            total_quarters = 1

        processed_count = 0
        for q_name, q_df in splits.items():
            processed_count += 1
            progress_start = 50 + int((processed_count - 1) / total_quarters * 30) # 50% -> 80%
            logger.progress(progress_start, f"正在分析 {q_name} ({processed_count}/{total_quarters})...")
            
            if q_df.empty:
                logger.info(f"分块 {q_name} 数据为空，跳过")
                continue
                
            # Sample using Adaptive Strategy (Phase 2 - 3.3)
            # Use smart_sample from global scope instead of q_analyzer method
            sample_text = smart_sample(q_df, max_tokens, logger)
            
            # Generate
            logger.info(f"发送 AI 请求: {q_name} (Model: {model_map})")
            res = generator.generate_quarterly_analysis(q_name, sample_text, model=model_map, is_periodic=is_periodic)
            quarterly_results.append(res)
            
        # Step 2: Reduce (Annual/Periodic Report)
        logger.progress(85, "正在生成汇总报告...")
        
        # Prepare Global Stats for Reduce
        global_stats_simple = {
            'total_messages': stats.get('total_messages'),
            'total_users': stats.get('total_users'),
            'year': analyzer.get_target_year(),
            'active_users_count': stats.get('active_users_count', 0), # Added safely
            'silent_users_count': stats.get('silent_users_count', 0), # Added safely
            'top_talkers': stats.get('top_talkers', []), # Added safely
            'top_repeaters': stats.get('top_repeaters', []), # Added safely
            'hardcore': analyzer.get_hardcore_stats()
        }
        
        # 获取小剧场配置
        anime_theme = config.get('anime_theme', 'default')
        custom_theme_prompt = config.get('custom_theme_prompt', '')
        
        logger.info(f"发送 AI 请求: 汇总报告 (Model: {model_reduce})")
        final_html = generator.generate_annual_report(
            quarterly_results, 
            global_stats_simple,
            anime_theme=anime_theme,
            custom_theme_prompt=custom_theme_prompt,
            model=model_reduce,
            is_periodic=is_periodic
        )
        logger.info("报告生成完成")

        # 4. Render
        logger.progress(95, "正在渲染 HTML...")
        renderer = ReportRenderer()
        chat_name = stats.get('title', 'QQ聊天记录')
        report_filename = f"report_{task_id}.html"
        report_path = os.path.join(OUTPUT_FOLDER, report_filename)
        
        # Get Hardcore Stats
        rankings = analyzer.get_user_rankings()
        
        renderer.render(
            stats=stats,
            daily_activity=daily_activity,
            summary=final_html, 
            rankings=rankings,
            output_path=report_path
        )
        
        # 4.1 Enhance HTML (Optional)
        if config.get('enhance_mode', False):
            logger.progress(98, "正在进行最终输出增强 (HTML Refine)...")
            logger.info(f"启动 HTML 修复与 CSS 优化... (Model: {model_refine})")
            
            try:
                with open(report_path, 'r', encoding='utf-8') as f:
                    raw_html = f.read()
                
                refined_html = generator.refine_report_html(raw_html, model=model_refine)
                
                if refined_html and len(refined_html) > 100:
                    with open(report_path, 'w', encoding='utf-8') as f:
                        f.write(refined_html)
                    logger.info("HTML 增强完成并已保存")
                else:
                    logger.info("HTML 增强结果异常，保留原文件")
                    
            except Exception as e:
                logger.info(f"HTML 增强失败: {e}")
        
        # 5. Save History
        history_manager.add_record(
            chat_name=chat_name,
            messages_count=stats['total_messages'],
            report_path=report_path
        )

        tasks[task_id]['result_url'] = f"/download/{report_filename}"
        tasks[task_id]['state'] = 'completed'
        logger.progress(100, "分析完成！")

    except Exception as e:
        logger.info(f"Error: {str(e)}")
        tasks[task_id]['state'] = 'failed'
        tasks[task_id]['error'] = str(e)
    finally:
        # Clean up uploaded file
        if os.path.exists(file_path):
            os.remove(file_path)

# --- Routes ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/analyze', methods=['POST'])
def analyze():
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'No file part'})
    
    file = request.files['file']
    config_str = request.form.get('config', '{}')
    
    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'No selected file'})
    
    if file and allowed_file(file.filename):
        try:
            config = json.loads(config_str)
            filename = secure_filename(file.filename)
            task_id = str(uuid.uuid4())
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{task_id}_{filename}")
            file.save(save_path)
            
            # Initialize Task
            tasks[task_id] = {
                'state': 'queued',
                'progress': 0,
                'status_text': '等待队列...',
                'logs': [],
                'result_url': None,
                'error': None
            }
            
            # Start Thread
            thread = threading.Thread(target=run_analysis_task, args=(task_id, save_path, config))
            thread.daemon = True
            thread.start()
            
            return jsonify({'status': 'success', 'task_id': task_id})
            
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)})
            
    return jsonify({'status': 'error', 'message': 'Invalid file type'})

@app.route('/api/status/<task_id>')
def task_status(task_id):
    if task_id not in tasks:
        return jsonify({'status': 'error', 'message': 'Task not found'}), 404
    
    task = tasks[task_id]
    # Return logs and clear them from server memory to avoid duplication if client polls?
    # Actually simple polling: client maintains offset or we just send all?
    # For simplicity, send all logs but client filters? Or we pop?
    # Let's just send last 5 logs or new logs.
    # To keep it stateless for client: client just displays what it gets.
    # We will implement a simple "read and clear" for logs here?
    # No, multiple polls might miss. Let's just send all logs and client appends unique? 
    # Or simpler: send "new_logs" by keeping track of read index? Too complex.
    # Let's just return all logs for now, client clears box and re-renders or appends diff.
    # Optimization: Client clears and appends.
    
    # Better: return "new_logs" by checking an optional "last_log_index" param?
    # Let's keep it extremely simple: Send all logs, client handles it. 
    # Or actually, we pop logs! Because logs are ephemeral stream.
    logs_to_send = list(task['logs']) # Copy
    task['logs'] = [] # Clear sent logs
    
    return jsonify({
        'state': task['state'],
        'progress': task['progress'],
        'status_text': task['status_text'],
        'new_logs': logs_to_send,
        'result_url': task['result_url'],
        'error': task['error']
    })

@app.route('/api/history')
def get_history():
    return jsonify(history_manager.get_records())

@app.route('/api/config', methods=['GET', 'POST'])
def handle_config():
    if request.method == 'POST':
        try:
            config_data = request.json
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2)
            return jsonify({'status': 'success', 'message': 'Config saved'})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)})
    else:
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    return jsonify(json.load(f))
            return jsonify({})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)})

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(OUTPUT_FOLDER, filename, as_attachment=True)

if __name__ == '__main__':
    print("Starting Flask Server at http://localhost:5000")
    app.run(debug=True, port=5000)
