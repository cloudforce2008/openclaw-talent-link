# -*- coding: utf-8 -*-
"""
对话响应生成器 - 数字人才市场
基于分析结果生成自然语言回复
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from talent_link.skills.nlp_parser import parse as parse_query


def generate_response(query: str, report: dict) -> dict:
    """
    根据用户输入和分析报告，生成对话式回复

    Returns:
        dict with keys: reply, intent, symbol, needs_more_info
    """
    parsed = parse_query(query)

    if not parsed.symbol:
        return {
            "reply": "我需要知道您想分析哪只股票。请告诉我股票代码或名称，比如「2513.HK」或「智谱AI」。",
            "intent": "clarify",
            "symbol": None,
            "needs_more_info": True,
        }

    m = report.get("market_data", {})
    final = report.get("final_recommendation", {})
    signal = report.get("signal", {})
    risk = report.get("risk", {})
    tech = report.get("technical", {})
    bull = report.get("bull_case", {})
    bear = report.get("bear_case", {})
    sentiment = report.get("sentiment", {})

    price = m.get("current_price", 0)
    change = m.get("change_percent", 0)
    change_str = f"+{change:.2f}%" if change >= 0 else f"{change:.2f}%"
    name = m.get("name") or parsed.name or parsed.symbol
    action = final.get("action", "hold")
    confidence = final.get("confidence", 0) * 100
    target = final.get("target_price", 0)
    stop = final.get("stop_loss", 0)
    reason = final.get("reason", "")

    # 根据不同意图生成不同风格的回复
    if parsed.intent == "buy":
        reply = _generate_buy_reply(name, price, change_str, action, confidence, reason, target, stop, risk)
    elif parsed.intent == "sell":
        reply = _generate_sell_reply(name, price, change_str, action, confidence, reason, target, stop)
    elif parsed.intent == "hold":
        reply = _generate_hold_reply(name, price, change_str, confidence, reason)
    else:
        reply = _generate_analyze_reply(name, price, change_str, action, confidence, reason, target, stop, tech, sentiment)

    return {
        "reply": reply,
        "intent": parsed.intent,
        "symbol": parsed.symbol,
        "name": name,
        "needs_more_info": False,
        "report": report,
    }


def _format_price(p):
    """格式化价格"""
    if not p:
        return "—"
    return f"{p:.2f}"


def _generate_analyze_reply(name, price, change_str, action, confidence, reason, target, stop, tech, sentiment):
    """分析型回复"""
    action_emoji = {"buy": "📈", "sell": "📉", "hold": "⏸️", "wait": "👀"}.get(action, "📊")
    action_text = {"buy": "建议买入", "sell": "建议卖出", "hold": "建议持仓", "wait": "建议观望"}.get(action, "待定")

    trend = tech.get("trend", "震荡")
    sentiment_text = sentiment.get("market_sentiment", "中性") if sentiment else "中性"

    lines = [
        f"{action_emoji} **{name}** 现在 {price} 元，今日涨跌 {change_str}",
        f"",
        f"**我的判断：**{action_text}（信心 {confidence:.0f}%）",
        f"",
    ]

    if reason:
        lines.append(f"理由：{reason}")

    lines.append(f"")
    lines.append(f"**当前技术面：**{trend}")
    lines.append(f"**市场情绪：**{sentiment_text}")

    if target and target != price:
        lines.append(f"")
        lines.append(f"📍 目标价 {_format_price(target)} | 止损 {_format_price(stop)}")

    lines.append(f"")
    lines.append(f"_你可以问我「能不能买」或「要不要卖」，我会给出更具体的操作建议。_")

    return "\n".join(lines)


def _generate_buy_reply(name, price, change_str, action, confidence, reason, target, stop, risk):
    """买入咨询回复"""
    if action == "buy":
        lines = [
            f"📈 **{name}** {price} 元 ({change_str})",
            f"",
            f"**我的建议：可以买**",
            f"",
        ]
        if reason:
            lines.append(f"理由：{reason}")
        lines.append(f"")
        if target:
            lines.append(f"入场价：{price} → 目标 {_format_price(target)} → 止损 {_format_price(stop)}")
        risk_level = risk.get("risk_level", "medium") if risk else "medium"
        lines.append(f"风险等级：{risk_level}，建议仓位 {final.get('max_position', '10%')}")
        return "\n".join(lines)

    elif action == "sell":
        lines = [
            f"📉 **{name}** {price} 元 ({change_str})",
            f"",
            f"**我的建议：现在不建议买入**",
            f"",
        ]
        if reason:
            lines.append(f"理由：{reason}")
        lines.append(f"")
        lines.append(f"如果你已经持有，可以考虑继续持有或逢高减仓。")
        return "\n".join(lines)

    else:  # hold / wait
        lines = [
            f"👀 **{name}** {price} 元 ({change_str})",
            f"",
            f"**我的建议：再等等**",
            f"",
        ]
        if reason:
            lines.append(f"理由：{reason}")
        lines.append(f"")
        lines.append(f"当前信号不够强，建议等待更明确的买入机会。")
        return "\n".join(lines)


def _generate_sell_reply(name, price, change_str, action, confidence, reason, target, stop):
    """卖出咨询回复"""
    if action == "sell":
        lines = [
            f"📉 **{name}** {price} 元 ({change_str})",
            f"",
            f"**我的建议：可以考虑卖出**",
            f"",
        ]
        if reason:
            lines.append(f"理由：{reason}")
        return "\n".join(lines)
    elif action == "hold" or action == "buy":
        lines = [
            f"📈 **{name}** {price} 元 ({change_str})",
            f"",
            f"**我的建议：继续持有**",
            f"",
        ]
        if reason:
            lines.append(f"理由：{reason}")
        lines.append(f"")
        lines.append(f"目前没有出现明显的卖出信号，建议继续持有。")
        return "\n".join(lines)
    else:
        return f"👀 **{name}** {price} 元 ({change_str})\n\n**我的建议：观望为主**，等待更明确的信号。\n\n理由：{reason or '当前市场信号不明确，建议谨慎。'}"


def _generate_hold_reply(name, price, change_str, confidence, reason):
    """持仓咨询回复"""
    lines = [
        f"📊 **{name}** {price} 元 ({change_str})",
        f"",
        f"**建议：继续持有**",
        f"",
    ]
    if reason:
        lines.append(f"理由：{reason}")
    lines.append(f"")
    lines.append(f"信心度 {confidence:.0f}%，继续持有等待机会。")
    return "\n".join(lines)


if __name__ == "__main__":
    # 测试
    test_queries = [
        "帮我看看 2513.HK",
        "智谱AI现在能买吗",
        "持仓要不要卖",
    ]
    print("测试对话响应生成器")
    print("=" * 40)
    for q in test_queries:
        parsed = parse_query(q)
        print(f"输入: {q}")
        print(f"解析: symbol={parsed.symbol}, intent={parsed.intent}")
        print()
