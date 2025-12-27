# src/registry.py

"""
Registry Module
===============
本模块集中管理项目中的所有常量、配置项及命名定义。
遵循 Phase 5 编程规范：模块化、标准化、封装化。
"""

# 意义: 定义项目中使用的所有常量和配置项，避免硬编码。
# 作用: 提供统一的配置管理，方便后续修改和维护。
# 关联: 被 src/parser.py, src/analyzer.py, src/llm_client.py 等模块引用。

# --- JSON 字段映射 (Field Mapping) ---
JSON_FIELD_MESSAGES = "messages"
JSON_FIELD_TIMESTAMP = "timestamp"
JSON_FIELD_SENDER = "sender"
JSON_FIELD_SENDER_UIN = "uin"
JSON_FIELD_SENDER_UID = "uid"
JSON_FIELD_SENDER_NAME = "name"
JSON_FIELD_SENDER_CARD = "card"
JSON_FIELD_CONTENT = "content"
JSON_FIELD_TEXT = "text"
JSON_FIELD_RESOURCES = "resources"
JSON_FIELD_IS_RECALLED = "isRecalled"
JSON_FIELD_MENTIONS = "mentions"
JSON_FIELD_CHAT_INFO = "chatInfo"
JSON_FIELD_CHAT_NAME = "name"
JSON_FIELD_STATISTICS = "statistics"
JSON_FIELD_TOTAL_MESSAGES = "totalMessages"
JSON_FIELD_TIME_RANGE = "timeRange"
JSON_FIELD_START = "start"
JSON_FIELD_END = "end"

# --- 默认配置 (Default Config) ---
DEFAULT_TOP_N = 10
DEFAULT_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
UNKNOWN_USER_NAME = "Unknown"
UNKNOWN_GROUP_NAME = "Unknown Group"

# --- Phase 3: Prompt Templates ---
# Map 阶段：季度分析
PROMPT_MAP_QUARTERLY = """
你是一位冷静但透着冷幽默的资深群聊观察员，同时也是一位资深的 ACGN（动画、漫画、游戏、小说）爱好者。请分析以下群聊记录片段（{quarter}），并提取关键信息。
这是一个 Map-Reduce 任务的中间步骤，你的输出将被用于生成年度总结。

**风格要求**：
1. **冷静的戏谑**：用一种“看透一切”的旁观者口吻进行分析，语言要精准、犀利。
2. **深度叙述**：对于每个分析点，生成一段连贯、有细节的描述。
3. **二次元浓度**：请尽可能多地、合适地融入 ACGN 圈的梗、成句与语气（如“MyGO语录”、“败犬”、“世界线变动”、“可以，这很xxx”等）。让分析报告读起来像是在看番剧评论，但不要影响核心信息的清晰度。

请返回 JSON 格式数据，包含以下字段：
1. "summary": (str) 本季度群聊风云录。请用一段详实的文字（100-200字）复盘本季度的核心话题演变，像写纪录片旁白一样串联起各个碎片话题。
2. "vibe": (str) 本季度群内氛围关键词及详细解读。
3. "active_members": (list) 本季度活跃用户名单。
4. "inactive_members": (list) 本季度潜水/不说话的用户名单。
5. "events": (list) 本季度的大事件。详细描述起因、经过和结果。
6. "memes_born": (list) 本季度诞生的梗。解释来源和用法。
7. "memes_died": (list) 本季度消失或过气的梗。
8. "mvp": (str) 本季度的 MVP 用户。50-100字详细论述“丰功伟绩”。
9. "characters": (dict) 活跃用户行为特征。key为用户名，value为人物画像（50字左右），描述说话风格和担当。
10. "relations": (list) 发现的用户间羁绊关系（如“CP感”、“宿敌”等）。

注意：
- 必须详细挖掘，拒绝流水账。
- 重点关注“梗”的诞生过程和群友间微妙的情感/权力流动。
"""

# Map 阶段：阶段分析 (非完整年度/动态切分)
PROMPT_MAP_PERIODIC = """
你是一位冷静但透着冷幽默的资深群聊观察员，同时也是一位资深的 ACGN（动画、漫画、游戏、小说）爱好者。请分析以下群聊记录片段（{quarter}），并提取关键信息。
这是一个 Map-Reduce 任务的中间步骤，你的输出将被用于生成整体分析报告。

**风格要求**：
1. **冷静的戏谑**：用一种“看透一切”的旁观者口吻进行分析，语言要精准、犀利。
2. **深度叙述**：对于每个分析点，生成一段连贯、有细节的描述。
3. **二次元浓度**：请尽可能多地、合适地融入 ACGN 圈的梗、成句与语气。

请返回 JSON 格式数据，包含以下字段：
1. "summary": (str) 本阶段群聊风云录。请用一段详实的文字（100-200字）复盘本阶段的核心话题演变。
2. "vibe": (str) 本阶段群内氛围关键词及详细解读。
3. "active_members": (list) 本阶段活跃用户名单。
4. "inactive_members": (list) 本阶段潜水/不说话的用户名单。
5. "events": (list) 本阶段的大事件。详细描述起因、经过和结果。
6. "memes_born": (list) 本阶段诞生的梗。解释来源和用法。
7. "memes_died": (list) 本阶段消失或过气的梗。
8. "mvp": (str) 本阶段的 MVP 用户。50-100字详细论述“丰功伟绩”。
9. "characters": (dict) 活跃用户行为特征。
10. "relations": (list) 发现的用户间羁绊关系。

注意：
- 必须详细挖掘，拒绝流水账。
"""

# Reduce 阶段：年度汇总
PROMPT_REDUCE_ANNUAL = """
你是一位既幽默又深刻的群聊观察员，擅长通过数据洞察群聊的灵魂，且深谙 ACGN 文化。基于以下4个季度的分析摘要，生成一份年度群聊报告。

输入数据：
{quarterly_data}

全局统计数据：
{stats_data}

**任务要求**：
1. **风格自适应**：请先分析该群聊的整体氛围，并据此决定报告的**视觉配色方案**和**文案风格**。
2. **ACGN 风格**：全篇文案请尽量使用 ACGN 风格的语言和梗。让读者感觉这不仅仅是一份报告，更像是一部“年度番剧”的设定集或回顾。
3. **深度与广度**：挖掘“情感温度”和“隐形关系网”。

请返回 JSON 格式数据，包含以下字段：

1. "style_config": (dict) **视觉风格配置**。请根据群聊氛围生成一套 CSS 颜色代码。
   - "primary_color": (str) 主色调（标题、重点）。
   - "secondary_color": (str) 辅助色（高亮、装饰）。
   - "background_color": (str) 页面背景色。
   - "card_bg": (str) 内容卡片背景色。
   - "text_color": (str) 正文文字颜色。
   - "font_family": (str) 推荐字体栈。

2. "keywords": (list) **年度十大关键词**。请提取 10 个最能代表本年度群聊精神的词汇。

3. "portrait": (str) <h3>年度群画像</h3> 
   - 给本群贴标签，并解释原因。
   - 分析群聊的“人格类型”（如 MBTI）或“番剧类型”（如“日常系”、“战斗系”、“胃痛系”）。
 
 4. "timeline": (str) <h3>年度大事件时间线</h3>
   - 以时间轴的形式串联全年的关键事件（HTML 列表格式 `<ul>...</ul>`）。

5. "quarterly_review": (str) <h3>季度深度复盘</h3> 
   - 针对 Q1-Q4，生成详细分析。
   - 包含：聊天内容、氛围、活跃/潜水人员、突发事件、梗的生灭、阶段 MVP。

6. "roasts": (str) <h3>群成员锐评</h3> 
   - 对各个群成员进行调侃。
   - 要求：有理有据，语言风趣毒舌。

7. "awards": (str) <h3>年度颁奖典礼</h3> 
   - 颁发奖项（如“最佳捧哏”、“节奏大师”、“年度潜水员”等），附颁奖词。

8. "anime_theater": (str) <h3>全年度动漫IP小剧场</h3> 
   {anime_instruction}
   - 编写一段全年度的小剧场脚本。

9. "moments": (str) <h3>社死/搞笑时刻回顾</h3> 
   - 挖掘尴尬或爆笑瞬间。

10. "essay": (str) <h3>年度总结小作文</h3> 
   - 基于 {year} 年的经历，写一篇感性或深刻的小作文（非打油诗）。

风格要求：
- 语言犀利但不失温情，充满网络梗和 ACGN 梗。
- 必须包含具体的用户名和事件。
- HTML 内容不要包含 markdown 代码块标记。
"""

# Reduce 阶段：通用/阶段性汇总
PROMPT_REDUCE_PERIODIC = """
你是一位既幽默又深刻的群聊观察员，擅长通过数据洞察群聊的灵魂，且深谙 ACGN 文化。基于以下分段分析摘要，生成一份深度群聊分析报告。

输入数据：
{quarterly_data}

全局统计数据：
{stats_data}

**任务要求**：
1. **风格自适应**：请先分析该群聊的整体氛围，并据此决定报告的**视觉配色方案**和**文案风格**。
2. **ACGN 风格**：全篇文案请尽量使用 ACGN 风格的语言和梗。让读者感觉这不仅仅是一份报告，更像是一部“番剧”的设定集或回顾。
3. **深度与广度**：挖掘“情感温度”和“隐形关系网”。

请返回 JSON 格式数据，包含以下字段：

1. "style_config": (dict) **视觉风格配置**。请根据群聊氛围生成一套 CSS 颜色代码。
   - "primary_color": (str) 主色调（标题、重点）。
   - "secondary_color": (str) 辅助色（高亮、装饰）。
   - "background_color": (str) 页面背景色。
   - "card_bg": (str) 内容卡片背景色。
   - "text_color": (str) 正文文字颜色。
   - "font_family": (str) 推荐字体栈。

2. "keywords": (list) **十大关键词**。请提取 10 个最能代表这段时间群聊精神的词汇。

3. "portrait": (str) <h3>群聊画像</h3> 
   - 给本群贴标签，并解释原因。
   - 分析群聊的“人格类型”（如 MBTI）或“番剧类型”。
 
 4. "timeline": (str) <h3>关键事件时间线</h3>
   - 以时间轴的形式串联关键事件（HTML 列表格式 `<ul>...</ul>`）。

5. "quarterly_review": (str) <h3>阶段深度复盘</h3> 
   - 针对各个时间段，生成详细分析。
   - 包含：聊天内容、氛围、活跃/潜水人员、突发事件、梗的生灭、阶段 MVP。

6. "roasts": (str) <h3>群成员锐评</h3> 
   - 对各个群成员进行调侃。

7. "awards": (str) <h3>荣誉颁奖典礼</h3> 
   - 颁发趣味奖项（如“最佳捧哏”、“节奏大师”等），附颁奖词。

8. "anime_theater": (str) <h3>动漫IP小剧场</h3> 
   {anime_instruction}
   - 编写一段小剧场脚本。

9. "moments": (str) <h3>社死/搞笑时刻回顾</h3> 
   - 挖掘尴尬或爆笑瞬间。

10. "essay": (str) <h3>总结小作文</h3> 
   - 基于这段时间的经历，写一篇感性或深刻的小作文。

风格要求：
- 语言犀利但不失温情，充满网络梗和 ACGN 梗。
- 必须包含具体的用户名和事件。
- HTML 内容不要包含 markdown 代码块标记。
"""

# 额外功能：HTML 优化
PROMPT_REFINE_HTML = """
请你检查并修复这个html形式的年度报告中可能存在的格式错误，确保无误的同时发挥你的自由想象力，对css样式进行优化使之更符合主题，要求样式主题符合报告主题，效果越炫酷越好。
请直接返回修复和优化后的完整 HTML 代码，不要包含 ```html 标记，也不要包含其他解释性文字。
"""

# --- 消息类型 (Message Types) ---
MSG_TYPE_TEXT = "text"
MSG_TYPE_IMAGE = "image"
MSG_TYPE_VIDEO = "video"
MSG_TYPE_FILE = "file"
MSG_TYPE_MIXED = "mixed"
MSG_TYPE_RECALLED = "recalled"

# --- LLM Configuration (Phase 2 & 4) ---
LLM_MODE_DEFAULT = "default"
LLM_MODE_CUSTOM = "custom"
DEFAULT_API_BASE = "https://api.openai.com/v1"
DEFAULT_MODEL = "gpt-4o"
DEFAULT_TEMPERATURE = 0.7

# --- Sampling Levels (Phase 2) ---
LEVEL_1_LOSSLESS = "lossless"
LEVEL_2_LIGHT = "light_compression"
LEVEL_3_SMART = "smart_focus"
LEVEL_4_EXTREME = "extreme_summary"

# --- Token Limits (Phase 2 - Estimated) ---
# Assuming ~1.5 chars per token for Chinese/Mixed text conservatively
TOKENS_PER_CHAR_ESTIMATE = 1.5 
MAX_CONTEXT_WINDOW = 16000 # Example for 16k context
TARGET_INPUT_TOKENS = 12000 # Safety buffer

# --- 列名定义 (DataFrame Columns) ---
COL_DATETIME = "datetime"
COL_DATE = "date"
COL_TIME = "time"
COL_HOUR = "hour"
COL_USER_ID = "user_id"
COL_USER_NAME = "user_name"
COL_CONTENT = "content"
COL_TYPE = "type"
COL_IS_RECALLED = "is_recalled"
COL_MENTIONS = "mentions"
COL_IMAGE_COUNT = "image_count"
