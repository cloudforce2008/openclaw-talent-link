# -*- coding: utf-8 -*-
"""
对话入口 - 数字人才市场
自然语言 → NLP解析 → 分析 → 对话回复
"""

import sys
import json
from pathlib import Path

# 确保 talent_link 包可导入（cwd=src/ 时也需要）
_project_root = Path(__file__).parent.parent
sys.path.insert(0, str(_project_root))

from talent_link.skills.nlp_parser import parse as parse_query
from talent_link.skills.chat_response import generate_response
from talent_link.agents.stock_analyst import StockAnalyst


def chat(message: str) -> dict:
    """主对话流程"""
    parsed = parse_query(message)

    if not parsed.symbol:
        return {
            "reply": "我需要知道您想分析哪只股票。请告诉我股票代码或名称，比如「2513.HK」或「智谱AI」。",
            "intent": "clarify",
            "symbol": None,
            "needs_more_info": True,
        }

    try:
        analyst = StockAnalyst(parsed.symbol, parsed.name)
        report = analyst.analyze()
    except Exception as e:
        return {
            "reply": f"抱歉，分析时遇到了问题：{str(e)}",
            "intent": parsed.intent,
            "symbol": parsed.symbol,
            "needs_more_info": True,
            "error": str(e),
        }

    if not report or report.get("error"):
        return {
            "reply": f"抱歉，没能获取到 {parsed.symbol} 的数据。请确认代码是否正确。",
            "intent": parsed.intent,
            "symbol": parsed.symbol,
            "needs_more_info": True,
            "error": report.get("error") if report else "unknown",
        }

    result = generate_response(message, report)
    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python chat.py <message>")
        sys.exit(1)
    result = chat(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))
