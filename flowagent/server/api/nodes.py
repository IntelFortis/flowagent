"""Node definitions API."""

from __future__ import annotations

from fastapi import APIRouter
from typing import Any, Dict, List

router = APIRouter(tags=["nodes"])


NODE_DEFINITIONS = [
    # Triggers
    {
        "type": "manual_trigger",
        "label": "手动触发",
        "category": "trigger",
        "description": "手动启动工作流",
        "icon": "play",
        "color": "#10b981",
        "inputs": [],
        "outputs": [{"id": "output", "label": "输出"}],
        "output_hint": "{triggered: true, time: \"...\"}",
        "config": [],
    },
    {
        "type": "webhook_trigger",
        "label": "Webhook 触发",
        "category": "trigger",
        "description": "通过 HTTP 请求触发",
        "icon": "webhook",
        "color": "#10b981",
        "inputs": [],
        "outputs": [{"id": "output", "label": "输出"}],
        "output_hint": "{triggered: true, url_path: \"/webhook\", method: \"POST\"}",
        "config": [
            {"key": "url_path", "label": "URL 路径", "type": "text", "default": "/webhook"},
            {"key": "method", "label": "HTTP 方法", "type": "select", "options": ["GET", "POST", "PUT"], "default": "POST"},
        ],
    },
    {
        "type": "schedule_trigger",
        "label": "定时触发",
        "category": "trigger",
        "description": "按时间计划触发",
        "icon": "clock",
        "color": "#10b981",
        "inputs": [],
        "outputs": [{"id": "output", "label": "输出"}],
        "output_hint": "{triggered: true, cron: \"0 * * * *\"}",
        "config": [
            {"key": "cron", "label": "Cron 表达式", "type": "text", "default": "0 * * * *"},
        ],
    },

    # Data
    {
        "type": "http_request",
        "label": "HTTP 请求",
        "category": "data",
        "description": "发送 HTTP 请求",
        "icon": "globe",
        "color": "#3b82f6",
        "inputs": [{"id": "input", "label": "输入"}],
        "outputs": [{"id": "output", "label": "响应"}],
        "output_hint": "{status_code: 200, body: {...}, headers: {...}, success: true}",
        "config": [
            {"key": "url", "label": "URL", "type": "text", "default": ""},
            {"key": "method", "label": "方法", "type": "select", "options": ["GET", "POST", "PUT", "DELETE", "PATCH"], "default": "GET"},
            {"key": "headers", "label": "请求头 (JSON)", "type": "textarea", "default": "{}"},
            {"key": "body", "label": "请求体", "type": "textarea", "default": ""},
        ],
    },
    {
        "type": "json_parse",
        "label": "JSON 解析",
        "category": "data",
        "description": "解析 JSON 数据",
        "icon": "braces",
        "color": "#3b82f6",
        "inputs": [{"id": "input", "label": "输入"}],
        "outputs": [{"id": "output", "label": "输出"}],
        "output_hint": "{value: ...}",
        "config": [
            {"key": "path", "label": "JSON 路径", "type": "text", "default": ""},
        ],
    },
    {
        "type": "data_filter",
        "label": "数据过滤",
        "category": "data",
        "description": "按条件过滤数据",
        "icon": "filter",
        "color": "#3b82f6",
        "inputs": [{"id": "input", "label": "输入"}],
        "outputs": [{"id": "output", "label": "输出"}],
        "output_hint": "{filtered: {...}, matched: true, field_value: ...}",
        "config": [
            {"key": "field", "label": "字段名", "type": "text", "default": ""},
            {"key": "operator", "label": "操作符", "type": "select", "options": ["equals", "not_equals", "contains", "gt", "lt"], "default": "equals"},
            {"key": "value", "label": "值", "type": "text", "default": ""},
        ],
    },
    {
        "type": "data_transform",
        "label": "数据转换",
        "category": "data",
        "description": "转换数据格式",
        "icon": "shuffle",
        "color": "#3b82f6",
        "inputs": [{"id": "input", "label": "输入"}],
        "outputs": [{"id": "output", "label": "输出"}],
        "output_hint": "{transformed: ...}",
        "config": [
            {"key": "expression", "label": "转换表达式", "type": "textarea", "default": ""},
        ],
    },
    {
        "type": "set_variable",
        "label": "设置变量",
        "category": "data",
        "description": "设置工作流变量",
        "icon": "variable",
        "color": "#3b82f6",
        "inputs": [],
        "outputs": [{"id": "output", "label": "输出"}],
        "output_hint": "{variable_name: value}",
        "config": [
            {"key": "name", "label": "变量名", "type": "text", "default": ""},
            {"key": "value", "label": "值", "type": "textarea", "default": ""},
        ],
    },
    {
        "type": "csv_parse",
        "label": "CSV 解析",
        "category": "data",
        "description": "解析 CSV 文本数据",
        "icon": "table",
        "color": "#3b82f6",
        "inputs": [{"id": "input", "label": "输入"}],
        "outputs": [{"id": "output", "label": "输出"}],
        "output_hint": "{rows: [{...}, ...], count: 10}",
        "config": [
            {"key": "delimiter", "label": "分隔符", "type": "text", "default": ","},
            {"key": "has_header", "label": "包含表头", "type": "select", "options": ["true", "false"], "default": "true"},
        ],
    },
    {
        "type": "text_join",
        "label": "文本拼接",
        "category": "data",
        "description": "用分隔符拼接文本",
        "icon": "link",
        "color": "#3b82f6",
        "inputs": [{"id": "input", "label": "输入"}],
        "outputs": [{"id": "output", "label": "输出"}],
        "output_hint": "{result: \"a,b,c\", count: 3}",
        "config": [
            {"key": "separator", "label": "分隔符", "type": "text", "default": ", "},
            {"key": "field", "label": "提取字段 (可选)", "type": "text", "default": ""},
        ],
    },
    {
        "type": "text_split",
        "label": "文本分割",
        "category": "data",
        "description": "按分隔符分割文本",
        "icon": "scissors",
        "color": "#3b82f6",
        "inputs": [{"id": "input", "label": "输入"}],
        "outputs": [{"id": "output", "label": "输出"}],
        "output_hint": "{items: [\"a\", \"b\", \"c\"], count: 3}",
        "config": [
            {"key": "delimiter", "label": "分隔符", "type": "text", "default": ","},
            {"key": "trim", "label": "去除空白", "type": "select", "options": ["true", "false"], "default": "true"},
        ],
    },
    {
        "type": "aggregate",
        "label": "数据聚合",
        "category": "data",
        "description": "对列表数据进行聚合计算",
        "icon": "bar-chart",
        "color": "#3b82f6",
        "inputs": [{"id": "input", "label": "输入"}],
        "outputs": [{"id": "output", "label": "输出"}],
        "output_hint": "{result: 42, input_count: 10, operation: \"count\"}",
        "config": [
            {"key": "operation", "label": "操作", "type": "select", "options": ["count", "sum", "avg", "min", "max", "first", "last"], "default": "count"},
            {"key": "field", "label": "数值字段 (可选)", "type": "text", "default": ""},
        ],
    },

    # AI
    {
        "type": "llm_chat",
        "label": "LLM 对话",
        "category": "ai",
        "description": "调用大语言模型",
        "icon": "brain",
        "color": "#8b5cf6",
        "inputs": [{"id": "input", "label": "输入"}],
        "outputs": [{"id": "output", "label": "输出"}],
        "output_hint": "{response: \"AI 回复内容\", model: \"gpt-4o\"}",
        "config": [
            {"key": "model", "label": "模型", "type": "text", "default": "gpt-4o"},
            {"key": "system_prompt", "label": "系统提示词", "type": "textarea", "default": ""},
            {"key": "user_prompt", "label": "用户提示词", "type": "textarea", "default": ""},
            {"key": "temperature", "label": "温度", "type": "number", "default": 0.7},
            {"key": "max_tokens", "label": "最大 Token", "type": "number", "default": 4096},
        ],
    },
    {
        "type": "text_summarize",
        "label": "文本摘要",
        "category": "ai",
        "description": "AI 生成文本摘要",
        "icon": "file-text",
        "color": "#8b5cf6",
        "inputs": [{"id": "input", "label": "输入"}],
        "outputs": [{"id": "output", "label": "摘要"}],
        "output_hint": "{summary: \"摘要文本...\"}",
        "config": [
            {"key": "model", "label": "模型", "type": "text", "default": "gpt-4o"},
            {"key": "max_length", "label": "最大长度", "type": "number", "default": 200},
        ],
    },
    {
        "type": "text_translate",
        "label": "文本翻译",
        "category": "ai",
        "description": "AI 翻译文本",
        "icon": "languages",
        "color": "#8b5cf6",
        "inputs": [{"id": "input", "label": "输入"}],
        "outputs": [{"id": "output", "label": "翻译结果"}],
        "output_hint": "{translation: \"Translated text\", target_language: \"English\"}",
        "config": [
            {"key": "model", "label": "模型", "type": "text", "default": "gpt-4o"},
            {"key": "target_language", "label": "目标语言", "type": "select", "options": ["中文", "English", "日本語", "한국어", "Français", "Deutsch", "Español"], "default": "English"},
        ],
    },
    {
        "type": "text_classify",
        "label": "文本分类",
        "category": "ai",
        "description": "AI 文本分类",
        "icon": "tags",
        "color": "#8b5cf6",
        "inputs": [{"id": "input", "label": "输入"}],
        "outputs": [{"id": "output", "label": "分类结果"}],
        "output_hint": "{category: \"正面\", simulated: true}",
        "config": [
            {"key": "model", "label": "模型", "type": "text", "default": "gpt-4o"},
            {"key": "categories", "label": "分类列表 (逗号分隔)", "type": "text", "default": "正面,负面,中性"},
        ],
    },
    {
        "type": "agent",
        "label": "AI Agent",
        "category": "ai",
        "description": "自主决策的 AI Agent，支持工具调用",
        "icon": "robot",
        "color": "#8b5cf6",
        "inputs": [{"id": "input", "label": "输入"}],
        "outputs": [{"id": "output", "label": "输出"}],
        "output_hint": "{response: \"Agent 回复\", steps: 2, tools_used: [...]}",
        "config": [
            {"key": "api_key", "label": "API Key", "type": "text", "default": ""},
            {"key": "api_base", "label": "API Base URL", "type": "text", "default": "https://api.openai.com/v1"},
            {"key": "model", "label": "模型", "type": "text", "default": "gpt-4o"},
            {"key": "system_prompt", "label": "系统提示词", "type": "textarea", "default": "你是一个有用的AI助手。你可以使用提供的工具来完成任务。"},
            {"key": "tools", "label": "可用工具 (JSON)", "type": "textarea", "default": '[{"name":"http_get","description":"发送HTTP GET请求","parameters":{"url":"string"}},{"name":"python_exec","description":"执行Python代码","parameters":{"code":"string"}}]'},
            {"key": "max_steps", "label": "最大推理步数", "type": "number", "default": 5},
        ],
    },
    {
        "type": "knowledge_base",
        "label": "知识库检索",
        "category": "ai",
        "description": "从知识库中检索相关信息 (RAG)",
        "icon": "book",
        "color": "#8b5cf6",
        "inputs": [{"id": "input", "label": "查询"}],
        "outputs": [{"id": "output", "label": "检索结果"}],
        "output_hint": "{results: [{content: \"...\", score: 5}], total_docs: 10}",
        "config": [
            {"key": "documents", "label": "文档内容", "type": "textarea", "default": ""},
            {"key": "top_k", "label": "返回条数", "type": "number", "default": 3},
            {"key": "separator", "label": "文档分隔符", "type": "text", "default": "---"},
        ],
    },

    # Logic
    {
        "type": "condition",
        "label": "条件判断",
        "category": "logic",
        "description": "根据条件分流",
        "icon": "git-branch",
        "color": "#f59e0b",
        "inputs": [{"id": "input", "label": "输入"}],
        "outputs": [
            {"id": "true", "label": "True"},
            {"id": "false", "label": "False"},
        ],
        "output_hint": "{condition_result: true/false, branch: \"true\"/\"false\", field_value: ...}",
        "config": [
            {"key": "field", "label": "字段", "type": "text", "default": ""},
            {"key": "operator", "label": "操作符", "type": "select", "options": ["equals", "not_equals", "contains", "gt", "lt", "is_empty", "is_not_empty"], "default": "equals"},
            {"key": "value", "label": "值", "type": "text", "default": ""},
        ],
    },
    {
        "type": "delay",
        "label": "延迟",
        "category": "logic",
        "description": "等待指定时间",
        "icon": "timer",
        "color": "#f59e0b",
        "inputs": [{"id": "input", "label": "输入"}],
        "outputs": [{"id": "output", "label": "输出"}],
        "output_hint": "{waited_seconds: 1, input: ...}",
        "config": [
            {"key": "seconds", "label": "等待秒数", "type": "number", "default": 1},
        ],
    },
    {
        "type": "loop",
        "label": "循环",
        "category": "logic",
        "description": "遍历列表数据",
        "icon": "repeat",
        "color": "#f59e0b",
        "inputs": [{"id": "input", "label": "输入"}],
        "outputs": [{"id": "item", "label": "当前项"}, {"id": "done", "label": "完成"}],
        "output_hint": "{items: [...], count: 5}",
        "config": [
            {"key": "items_path", "label": "列表字段路径", "type": "text", "default": ""},
        ],
    },
    {
        "type": "code",
        "label": "自定义代码",
        "category": "logic",
        "description": "运行自定义 Python 代码",
        "icon": "code",
        "color": "#f59e0b",
        "inputs": [{"id": "input", "label": "输入"}],
        "outputs": [{"id": "output", "label": "输出"}],
        "output_hint": "{output: main() 返回值, stdout: \"print 输出\"}",
        "config": [
            {"key": "code", "label": "Python 代码", "type": "textarea", "default": "# input_data 变量包含输入\ndef main(input_data):\n    return input_data"},
        ],
    },

    # Output
    {
        "type": "send_email",
        "label": "发送邮件",
        "category": "output",
        "description": "发送电子邮件",
        "icon": "mail",
        "color": "#ef4444",
        "inputs": [{"id": "input", "label": "输入"}],
        "outputs": [],
        "config": [
            {"key": "to", "label": "收件人", "type": "text", "default": ""},
            {"key": "subject", "label": "主题", "type": "text", "default": ""},
            {"key": "body", "label": "正文", "type": "textarea", "default": ""},
        ],
    },
    {
        "type": "webhook_response",
        "label": "Webhook 回调",
        "category": "output",
        "description": "发送 Webhook 回调",
        "icon": "send",
        "color": "#ef4444",
        "inputs": [{"id": "input", "label": "输入"}],
        "outputs": [],
        "config": [
            {"key": "url", "label": "回调 URL", "type": "text", "default": ""},
            {"key": "method", "label": "方法", "type": "select", "options": ["POST", "PUT"], "default": "POST"},
        ],
    },
    {
        "type": "save_file",
        "label": "保存文件",
        "category": "output",
        "description": "保存数据到文件",
        "icon": "download",
        "color": "#ef4444",
        "inputs": [{"id": "input", "label": "输入"}],
        "outputs": [],
        "config": [
            {"key": "filename", "label": "文件名", "type": "text", "default": "output.json"},
            {"key": "format", "label": "格式", "type": "select", "options": ["json", "csv", "txt"], "default": "json"},
        ],
    },
    {
        "type": "log_output",
        "label": "日志输出",
        "category": "output",
        "description": "输出到日志",
        "icon": "terminal",
        "color": "#ef4444",
        "inputs": [{"id": "input", "label": "输入"}],
        "outputs": [],
        "config": [
            {"key": "message", "label": "日志消息", "type": "textarea", "default": ""},
        ],
    },
]


@router.get("/nodes")
async def list_nodes() -> List[Dict[str, Any]]:
    """List all available node types."""
    return NODE_DEFINITIONS


@router.get("/nodes/categories")
async def list_categories() -> List[Dict[str, Any]]:
    """List node categories."""
    categories = {}
    for node in NODE_DEFINITIONS:
        cat = node["category"]
        if cat not in categories:
            categories[cat] = {
                "id": cat,
                "label": {
                    "trigger": "触发器",
                    "data": "数据",
                    "ai": "AI",
                    "logic": "逻辑",
                    "output": "输出",
                }.get(cat, cat),
                "nodes": [],
            }
        categories[cat]["nodes"].append(node)
    return list(categories.values())
