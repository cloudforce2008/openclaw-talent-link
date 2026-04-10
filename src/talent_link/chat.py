# -*- coding: utf-8 -*-
"""
对话入口 - 数字人才市场
使用 talent-link 本地分析引擎（快） + workspace 全球市场数据（真）
"""

import sys
import json
import subprocess
from pathlib import Path

WORKSPACE_UTILS = '/root/.openclaw/workspace/skills/stock-analyzer-v2/utils'


def chat(message: str) -> dict:
    """
    主对话流程
    1. NLP解析 - 提取股票代码和意图
    2. 执行分析（技术面用talent-link，全球信号用workspace）
    3. 生成对话回复
    """
    from talent_link.skills.nlp_parser import parse as parse_query
    from talent_link.skills.chat_response import generate_response
    from talent_link.agents.stock_analyst import StockAnalyst

    # Step 1: NLP解析
    parsed = parse_query(message)

    if not parsed.symbol:
        return {
            "reply": "我需要知道您想分析哪只股票。请告诉我股票代码或名称，比如「2513.HK」或「智谱AI」。",
            "intent": "clarify",
            "symbol": None,
            "needs_more_info": True,
        }

    # Step 2: 执行分析（使用 talent-link 本地引擎，速度快）
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

    # Step 2b: 注入 workspace 全球市场信号（真实数据）
    report = _inject_global_signals(report)

    # Step 3: 生成对话回复
    result = generate_response(message, report)
    return result


def _inject_global_signals(report: dict) -> dict:
    """
    用 workspace 的 global_market_fetcher 注入真实全球市场信号
    覆盖 sentiment.global_signals
    """
    try:
        if WORKSPACE_UTILS not in sys.path:
            sys.path.insert(0, WORKSPACE_UTILS)
        from global_market_fetcher import get_full_global_signals
        gs = get_full_global_signals()

        sent = report.get("sentiment", {})
        sent["global_signals"] = gs

        # 添加可读信号文本
        signals = gs.get("signals") or []
        if signals:
            sent["_market_signals_text"] = " | ".join(signals[:5])

        # 中东局势单独标注
        geo = gs.get("geopolitics", {}).get("iran_israel", {})
        if geo:
            sent["_geopolitical_note"] = f"中东局势({geo.get('status')})：{geo.get('description','')[:50]}"

        return report
    except Exception as e:
        print(f"[chat] global signals injection failed: {e}")
        return report


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python chat.py <message>")
        sys.exit(1)

    result = chat(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))
