# QQ群聊天记录年度报告生成器 (QQ Chat History Annual Report Generator)

## 1. 项目概述 (Project Overview)

**QQ群聊天记录年度报告生成器** 是一款基于大语言模型（LLM）的深度聊天记录分析工具。本项目旨在解决传统聊天记录分析工具仅停留在“数量统计”层面的痛点，通过引入先进的生成式 AI 技术，实现对聊天内容的**语义理解、情感分析、话题总结**以及**ACGN风格化呈现**。

本项目专门针对 **QQChatExporter** 导出的 JSON 格式数据进行优化，采用 **Map-Reduce** 分布式分析架构，能够高效处理长达一整年的海量聊天记录，并最终生成一份包含精美图表、深度文本总结及趣味互动的 HTML 年度报告。

---

## 2. 核心功能 (Core Features)

### 2.1 多维数据统计 (Multi-dimensional Statistics)
项目内置了强大的统计引擎，能够从非结构化的聊天数据中提取多维度的硬指标：
- **基础概览**：总消息数、活跃人数、总图片数、撤回消息数、跨越天数。
- **用户画像**：
  - **话痨榜 (Top Talkers)**：基于消息数量的活跃度排名。
  - **图王争霸 (Image Kings)**：基于图片发送量的排名。
  - **守夜人 (Night Owls)**：深夜（00:00-05:00）活跃用户排名。
  - **早起鸟 (Early Birds)**：清晨（05:00-08:00）活跃用户排名。
- **时间分布**：
  - **24小时热力图**：分析群聊在一天中各个时段的活跃趋势。
  - **每日活跃度**：展示全年的聊天热度曲线。
- **内容分析**：
  - **高频词云**：基于 `jieba` 分词和停用词过滤，提取群聊核心关键词。

### 2.2 AI 深度语义分析 (AI Semantic Analysis)
区别于传统工具，本项目利用 LLM 进行深度内容理解：
- **年度/阶段性总结**：不仅仅是数字，更是对群聊氛围、核心话题的文字总结。
- **季度/分期复盘**：将漫长的时间线切分为多个阶段，分别回顾每个阶段的“高光时刻”。
- **群友锐评 (Roasts)**：模仿群友口吻，对这一年的群聊进行幽默风趣的点评。
- **颁奖典礼 (Awards)**：AI 自动根据用户行为颁发趣味奖项（如“潜水王”、“表情包大户”等）。
- **小剧场生成 (Anime Theater)**：基于群友的性格特征，生成一段虚构的 ACGN 主题小剧场（如“赛博朋克篇”、“异世界篇”）。

### 2.3 智能路由与自适应采样 (Smart Routing & Adaptive Sampling)
针对 LLM 上下文窗口（Context Window）的限制，项目设计了一套复杂的**自适应数据处理管线**：
- **智能切分 (Smart Splitting)**：自动判断数据的时间跨度和分布密度，动态选择“按季度切分”或“按消息量等分”策略。
- **自适应采样 (Adaptive Sampling)**：根据配置的模型 Token 预算，自动在“无损模式”和“均匀采样模式”之间切换，确保在预算范围内最大化信息保留量。

### 2.4 高度可定制化 (High Customizability)
- **多模型支持**：支持 OpenAI 兼容格式的 API（如 GPT-4, DeepSeek, Claude 等），并允许为 Map、Reduce、Refine 不同阶段配置不同的模型。
- **主题定制**：用户可选择预设的动漫主题（如 BanG Dream!, GBC），或自定义 Prompt 进行风格化输出。
- **隐私安全**：核心统计在本地完成，仅将脱敏后的文本摘要发送给 LLM，且支持用户自定义 API 端点。

---

## 3. 系统架构 (System Architecture)

本项目采用经典的 **Client-Server** 架构，前端负责交互与展示，后端负责核心逻辑处理。

### 3.1 前端 (Frontend)
前端采用原生 **HTML5 + CSS3 + JavaScript (ES6+)** 构建，坚持“轻量化、无依赖”的设计原则。
- **UI 框架**：自定义 CSS 变量系统（Inter字体，扁平化设计），支持响应式布局。
- **交互逻辑**：
  - **File API**：支持拖拽上传大文件（JSON）。
  - **Fetch API**：与后端进行异步通信，通过轮询（Polling）机制获取任务进度。
  - **Markdown 渲染**：集成 `marked.js` 实现教程和日志的富文本展示。
  - **ECharts**：虽然报告是静态 HTML，但生成的报告内部集成了 ECharts 库用于图表渲染。

### 3.2 后端 (Backend)
后端基于 **Python Flask** 框架，采用分层架构设计：
- **API 层 (Controller)**：处理 HTTP 请求，进行参数校验和任务分发。
- **服务层 (Service)**：
  - `Task Manager`：基于简单的内存字典和线程（Threading）实现异步任务队列。
  - `LLM Client`：封装 HTTP 请求，处理与大模型的流式/非流式对话。
- **核心逻辑层 (Core)**：
  - `Parser`：ETL 引擎，负责 JSON 解析与清洗。
  - `Analyzer`：基于 Pandas 的统计分析引擎。
  - `Generator`：Map-Reduce 流程控制器。
  - `Renderer`：Jinja2 模板渲染引擎。

### 3.3 目录结构 (Directory Structure)
```
Project.Z/
├── app.py                 # Flask 主入口
├── config.json            # 用户配置文件
├── src/                   # 核心源码目录
│   ├── parser.py          # 数据解析 (ETL)
│   ├── analyzer.py        # 统计分析 (Pandas)
│   ├── generator.py       # 报告生成 (Map-Reduce)
│   ├── llm_client.py      # LLM 客户端
│   ├── prompts.py         # 提示词管理
│   ├── registry.py        # 常量注册表
│   └── renderer.py        # HTML 渲染
├── static/                # 静态资源
│   ├── css/               # 样式表
│   └── js/                # 前端脚本
├── templates/             # Jinja2 模板
│   ├── index.html         # 主页
│   └── report.html        # 报告模板
└── uploads/               # 上传文件暂存区
```

---

## 4. 核心机制与算法原理 (Mechanism & Algorithms)

### 4.1 ETL 数据清洗管线 (ETL Pipeline)
数据处理是分析的基础，`src/parser.py` 实现了严谨的 ETL 流程：
1.  **加载 (Load)**：读取 QQChatExporter 导出的 JSON 文件。
2.  **标准化 (Normalize)**：
    -   **用户标识**：优先使用 `uin` (QQ号) 作为唯一 ID，解决用户频繁改名的问题。
    -   **名称映射**：建立 `ID -> 显示名称` 的映射表。优先使用群名片 (`card`)，其次是昵称 (`name`)，最后回退到 ID。
3.  **预处理 (Preprocess)**：
    -   **时间转换**：将 Unix 时间戳转换为 Python `datetime` 对象，并处理时区问题。
    -   **类型识别**：解析消息体，区分 `Text`、`Image`、`Video`、`Mixed` 等类型。
    -   **分词**：引入 `jieba` 进行中文分词，加载自定义停用词表（Stop Words），去除“的、了、么”等无意义虚词，保留情感强烈的语气词。

### 4.2 Map-Reduce 分析架构 (Map-Reduce Strategy)
面对长达一年的聊天记录（可能包含数十万条消息），直接将其输入 LLM 会导致两个问题：
1.  **Context Window Overflow**：超过模型上下文上限。
2.  **Lost in the Middle**：模型在处理过长文本时容易遗忘中间信息。

为此，本项目引入了 Map-Reduce 架构：

#### Phase 1: 切分 (Splitting) - 智能路由算法
`src/analyzer.py` 中的 `get_quarterly_splits` 函数实现了智能切分逻辑：
- **默认策略**：按自然季度（Q1, Q2, Q3, Q4）切分。
- **异常检测**：
  - 计算数据的时间分布集中度。如果某一个季度的数据量占比超过 80%（例如群聊在年底才建立），则判定为“分布极度不均”。
  - 计算总时间跨度。如果跨度小于 200 天，则按季度切分可能导致某些分块为空或过小。
- **降级策略**：一旦触发异常检测，系统自动切换为 **“动态等量切分” (Dynamic Equal Splitting)** 模式，将所有消息按数量均匀切分为 4 个 `Period`，确保每个分块的负载均衡。

#### Phase 2: 映射 (Map) - 分块分析
`src/generator.py` 遍历每个分块，调用 LLM 进行独立分析。
- **输入**：该分块内的压缩文本摘要 + 统计数据。
- **Prompt**：要求 LLM 扮演数据分析师，提取该时间段的：
  - **关键事件 (Key Events)**
  - **活跃人物 (Active Characters)**
  - **梗/流行语 (Memes)**
  - **整体氛围 (Vibe)**
- **输出**：结构化的 JSON 数据。

#### Phase 3: 归约 (Reduce) - 全局汇总
收集所有 Map 阶段的 JSON 输出，结合全年的统计数据，再次调用 LLM。
- **输入**：`[Q1结果, Q2结果, Q3结果, Q4结果] + 全局Top10榜单`。
- **Prompt**：要求 LLM 扮演年度报告主编，进行：
  - **去重与融合**：合并跨季度的相似话题。
  - **升华总结**：生成年度总结语、颁奖词和小剧场剧本。
  - **风格化**：应用用户选择的 ACGN 主题风格。

### 4.3 Token 预算管理与自适应采样 (Token Budget & Adaptive Sampling)
为了防止 API 调用费用超支或超出模型限制，`app.py` 中的 `smart_sample` 函数实现了精细的 Token 管理：
1.  **预算估算**：根据用户配置的 `max_tokens`（如 128k），预留一部分给 Prompt 模板（约 8k），剩余部分作为 **数据预算 (Data Budget)**。
2.  **字符转换**：按 `1 Token ≈ 1.5 chars` 的经验公式，将 Token 预算转换为字符数预算。
3.  **采样决策**：
    -   **Scenario A (数据量 < 预算)**：**无损模式**。直接发送全量文本。
    -   **Scenario B (数据量 > 预算)**：**均匀采样模式**。
        -   计算采样步长 `Step = Total_Msgs / (Budget / Avg_Msg_Len)`。
        -   执行 `msgs[::step]` 切片操作。
        -   **优化点**：代码逻辑保证了采样的均匀性，从而保留了时间维度的连续性，避免出现“只看开头不看结尾”的情况。

### 4.4 提示词工程 (Prompt Engineering)
`src/prompts.py` 是本项目的灵魂所在。采用了以下高级 Prompt 技巧：
- **Few-Shot Learning**：虽然主要依赖 Zero-Shot，但在 Instruction 中通过具体的 JSON 示例（Schema）来约束输出格式。
- **Role Persona (角色扮演)**：
  - *Analyzer*: 冷静客观的数据分析师。
  - *Editor*: 幽默风趣、熟悉二次元文化的报告主编。
  - *CSS Expert*: 精通前端美学的工程师（用于 Refine 阶段）。
- **Context Injection (上下文注入)**：
  - 将 Pandas 计算出的“硬统计数据”（如 Top5 话痨）直接嵌入 Prompt，**禁止** LLM 自己去数数（避免幻觉），而是让 LLM 解释这些数据背后的含义。
- **Chain of Thought (思维链)**：在复杂的 Reduce 阶段，引导 LLM 先思考各个季度的关联，再生成最终总结。

---

## 5. 部署与使用 (Deployment & Usage)

### 5.1 环境要求
- Windows / macOS / Linux
- Python 3.10 或更高版本
- 建议使用虚拟环境 (venv / conda)

### 5.2 安装步骤
1.  **克隆仓库**：
    ```bash
    git clone https://github.com/YourRepo/Project.Z.git
    cd Project.Z
    ```
2.  **安装依赖**：
    ```bash
    pip install -r requirements.txt
    ```
    *核心依赖包括：`flask`, `pandas`, `jieba`, `openai`, `requests`*

### 5.3 运行项目
1.  **启动服务**：
    - Windows 用户可直接运行 `start.bat`。
    - 或命令行运行：
      ```bash
      python app.py
      ```
2.  **访问界面**：
    打开浏览器访问 `http://127.0.0.1:5000`。

### 5.4 配置指南
在网页左侧边栏进行配置：
- **LLM 模式**：选择 `Custom`。
- **Base URL**：填入模型服务商的 API 地址（如 `https://api.deepseek.com/v1`）。
- **API Key**：填入你的密钥。
- **Model Name**：填入模型名称（如 `deepseek-chat`）。
- **Token 预算**：根据模型支持的上下文长度调整（推荐 100k-200k）。

### 5.5 生成报告
1.  将导出的 JSON 文件拖入上传区域。
2.  等待后台完成 ETL -> Map -> Reduce 流程。
3.  点击下载生成的 HTML 报告。

---

## 6. 开发规范与贡献 (Development)

本项目遵循模块化开发规范：
- **SRP (单一职责原则)**：Parser 只管解析，Analyzer 只管统计，Generator 只管生成。
- **Type Hinting**：Python 代码全量覆盖类型注解，增强可读性与健壮性。
- **Error Handling**：关键路径（如 API 调用、文件解析）均包含 Try-Catch 块，确保服务不崩溃。

欢迎提交 Issue 和 PR 共同完善本项目！
PS:该文档由Gemini-3-pro-preview自主生成，部分内容可能存在谬误，请注意辨别。