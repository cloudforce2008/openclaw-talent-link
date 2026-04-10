# -*- coding: utf-8 -*-
"""
对话响应生成器 - 数字人才市场
基于真实分析数据，生成有依据、有判断的对话式回复
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from talent_link.skills.nlp_parser import parse as parse_query


def generate_response(query: str, report: dict) -> dict:
    """根据用户意图 + 真实分析数据，生成有依据的回复"""
    parsed = parse_query(query)

    if not parsed.symbol:
        return {
            "reply": "我需要知道您想分析哪只股票。请告诉我股票代码或名称，比如「2513.HK」或「智谱AI」。",
            "intent": "clarify",
            "symbol": None,
            "needs_more_info": True,
        }

    # 提取各维度真实数据
    m = report.get("market_data", {})
    tech = report.get("technical", {})
    fund = report.get("fundamental", {})
    sent = report.get("sentiment", {})
    bull = report.get("bull_case", {})
    bear = report.get("bear_case", {})
    signal = report.get("signal", {})
    risk = report.get("risk", {})
    final = report.get("final_recommendation", {})

    price = m.get("current_price", 0)
    change = m.get("change_percent", 0)
    change_str = f"+{change:.2f}%" if change >= 0 else f"{change:.2f}%"
    name = m.get("name") or parsed.name or parsed.symbol

    # 根据意图生成不同风格的回复
    if parsed.intent == "buy":
        reply = _buy_reply(name, price, change_str, tech, fund, sent, signal, final, risk)
    elif parsed.intent == "sell":
        reply = _sell_reply(name, price, change_str, tech, fund, sent, signal, final, risk)
    elif parsed.intent == "hold":
        reply = _hold_reply(name, price, change_str, tech, signal, final)
    elif parsed.intent == "compare":
        reply = _compare_reply(name, price, change_str, tech, fund, bull, bear, signal, final)
    else:
        reply = _analyze_reply(name, price, change_str, m, tech, fund, sent, bull, bear, signal, risk, final, symbol=parsed.symbol)

    return {
        "reply": reply,
        "intent": parsed.intent,
        "symbol": parsed.symbol,
        "name": name,
        "needs_more_info": False,
    }


def _fmt_price(p):
    return f"{p:.2f}" if p else "—"

def _trend_label(t):
    labels = {
        "strong_upward": "强势上涨 ↑↑",
        "upward": "上涨 ↑",
        "sideways": "横盘震荡 →",
        "downward": "下跌 ↓",
        "strong_downward": "弱势下跌 ↓↓",
    }
    return labels.get(t, t)

def _rsi_desc(rsi):
    if rsi < 30: return f"RSI {rsi:.0f}（超卖，可能反弹）"
    if rsi < 50: return f"RSI {rsi:.0f}（偏弱）"
    if rsi < 70: return f"RSI {rsi:.0f}（偏强）"
    return f"RSI {rsi:.0f}（超买，留意回调）"

def _macd_desc(macd):
    labels = {
        "bullish_cross": "MACD 金叉（看多信号）",
        "bearish_cross": "MACD 死叉（看空信号）",
        "bullish": "MACD 多头（上升动能）",
        "bearish": "MACD 空头（下降动能）",
        "neutral": "MACD 中性",
    }
    return labels.get(macd, f"MACD {macd}")

def _action_emoji(a):
    return {"buy": "📈", "sell": "📉", "hold": "⏸️", "wait": "👀"}.get(a, "📊")

def _action_text(a):
    return {"buy": "建议买入", "sell": "建议卖出", "hold": "建议持仓", "wait": "建议观望"}.get(a, "待定")


def _analyze_reply(name, price, change_str, m, tech, fund, sent, bull, bear, signal, risk, final, symbol=None):
    """分析型回复 - 完整的判断依据"""
    action = final.get("action", "wait")
    confidence = final.get("confidence", 0) * 100
    target = final.get("target_price")
    stop = final.get("stop_loss")
    reason = final.get("reason", "")

    # 技术面核心数据
    ind = tech.get("indicators", {})
    rsi = ind.get("rsi", 50)
    macd = ind.get("macd", "neutral")
    ma5 = ind.get("ma5")
    ma20 = ind.get("ma20")
    sup = tech.get("support_levels", [])
    res = tech.get("resistance_levels", [])

    lines = [
        f"{_action_emoji(action)} **{name}** {price} 元（{change_str}）",
        f"",
    ]

    # 技术面依据
    lines.append(f"【技术面】")
    lines.append(f"  趋势：{_trend_label(tech.get('trend', 'unknown'))}")
    lines.append(f"  {_rsi_desc(rsi)}")
    lines.append(f"  {_macd_desc(macd)}")
    if ma5 and ma20:
        if ma5 > ma20:
            lines.append(f"  均线：MA5({_fmt_price(ma5)}) > MA20({_fmt_price(ma20)})，多头排列")
        else:
            lines.append(f"  均线：MA5({_fmt_price(ma5)}) < MA20({_fmt_price(ma20)})，空头排列")
    if sup:
        lines.append(f"  支撑位：{', '.join(_fmt_price(s) for s in sup)}")
    if res:
        lines.append(f"  阻力位：{', '.join(_fmt_price(r) for r in res[:2])}")

    # 基本面（如果有的话）
    fund_analysis = fund.get("analysis", "")
    if fund_analysis and fund_analysis != "基于有限数据的基础分析。":
        lines.append(f"")
        lines.append(f"【基本面】")
        lines.append(f"  {fund_analysis}")
        key_factors = fund.get("key_factors", [])
        if key_factors:
            for f in key_factors[:3]:
                lines.append(f"  · {f}")

    # 情绪面
    sent_text = sent.get("market_sentiment", "neutral")
    if sent_text != "neutral":
        lines.append(f"")
        lines.append(f"【市场情绪】{sent_text}")

    # 全球宏观信号 → 因果分析（不只是罗列数据）
    gs = sent.get("global_signals") or {}
    if gs:
        us_ai = gs.get("us_ai_leaders", {})
        nasdaq = us_ai.get("nasdaq") or {}
        nvda = us_ai.get("nvda") or {}
        gold = (gs.get("commodities") or {}).get("gold") or {}
        oil = (gs.get("commodities") or {}).get("crude_oil") or {}
        geo = (gs.get("geopolitics") or {}).get("iran_israel") or {}
        signals = gs.get("signals") or []

        macro_judgments = []

        # 纳指
        nasdaq_chg = nasdaq.get("change_percent")
        if nasdaq_chg is not None:
            if nasdaq_chg > 1:
                macro_judgments.append(f"纳指+{nasdaq_chg:.2f}%→港股科技情绪支撑，利好映射")
            elif nasdaq_chg < -1:
                macro_judgments.append(f"纳指{nasdaq_chg:.2f}%→情绪传导偏空，港股科技承压")
            else:
                macro_judgments.append(f"纳指{nasdaq_chg:.2f}%→美股平稳，影响中性")

        # NVDA（AI芯片情绪锚）
        nvda_chg = nvda.get("change_percent")
        is_ai_stock = any(k in (symbol or '') for k in ['2513', '0100', 'AI'])
        if nvda_chg is not None:
            if is_ai_stock:
                if nvda_chg > 1:
                    macro_judgments.append(f"NVDA+{nvda_chg:.2f}%→AI板块情绪向好，直接利好")
                elif nvda_chg < -1:
                    macro_judgments.append(f"NVDA{nvda_chg:.2f}%→AI上游情绪拖累，对{parsed.name or 'AI股'}偏利空")

        # 黄金（避险 + 利率预期）
        gold_chg = gold.get("change_percent", 0)
        gold_price = gold.get("price")
        if gold_price and gold_chg:
            if gold_chg > 1:
                macro_judgments.append(f"黄金${gold_price:.0f}(+{gold_chg:.2f}%)→避险升温+利率预期下降，成长股估值承压")
            elif gold_chg < -1:
                macro_judgments.append(f"黄金${gold_price:.0f}({gold_chg:.2f}%)→避险降温度+风险偏好回升，科技股受益")

        # 原油（成本端 + 通胀）
        oil_chg = oil.get("change_percent", 0)
        oil_price = oil.get("price")
        if oil_price and oil_chg:
            if oil_chg > 3:
                macro_judgments.append(f"原油${oil_price:.1f}(+{oil_chg:.2f}%)→通胀压力+成本上行，抑制科技股估值扩张")
            elif oil_chg < -3:
                macro_judgments.append(f"原油${oil_price:.1f}({oil_chg:.2f}%)→大宗商品回调→通胀压力缓解，利好科技")

        # 地缘（风险资产折价）
        geo_status = geo.get("status", "")
        geo_desc_cn = geo.get("description_cn", "") or geo.get("description", "")
        geo_impact = geo.get("impact", "")
        if geo_status and geo_status.upper() not in ['CEASEFIRE', 'COLD']:
            if geo_impact == 'risk_on':
                macro_judgments.append(f"中东局势升温→全球风险资产短期承压，港股外资流向偏紧")
            elif geo_impact == 'negative':
                macro_judgments.append(f"地缘压力持续→风险偏好抑制，高估值成长股折价")
            else:
                macro_judgments.append(f"地缘【{geo_status.upper()}】{geo_desc_cn[:25]}→增加港股短线波动风险")

        if macro_judgments:
            lines.append(f"")
            lines.append(f"【全球宏观 → 逻辑判断】")
            for j in macro_judgments:
                lines.append(f"  → {j}")

    # 多空观点对比
    lines.append(f"")
    lines.append(f"【多空观点】")
    bull_t = bull.get("target_price")
    bear_t = bear.get("target_price")
    if bull_t:
        lines.append(f"  看多目标：{_fmt_price(bull_t)}（置信 {bull.get('confidence',0)*100:.0f}%）")
    if bear_t:
        lines.append(f"  看空目标：{_fmt_price(bear_t)}（置信 {bear.get('confidence',0)*100:.0f}%）")

    # 交易信号
    lines.append(f"")
    lines.append(f"【综合建议】{_action_text(action)}")
    lines.append(f"  置信度：{confidence:.0f}%")
    if reason:
        lines.append(f"  理由：{reason}")
    if target and target != price:
        lines.append(f"  目标价：{_fmt_price(target)}")
    if stop:
        lines.append(f"  止损位：{_fmt_price(stop)}")

    # 风险提示
    risk_level = risk.get("risk_level", "")
    if risk_level:
        lines.append(f"  风险等级：{risk_level}")

    lines.append(f"")
    lines.append(f"---\n_技术面：Yahoo Finance 3个月K线 | 全球宏观：实时市场数据 | 分析仅供参考，不构成投资建议_")

    return "\n".join(lines)


def _buy_reply(name, price, change_str, tech, fund, sent, signal, final, risk):
    """买入咨询回复"""
    action = final.get("action", "wait")
    confidence = final.get("confidence", 0) * 100
    target = final.get("target_price")
    stop = final.get("stop_loss")

    ind = tech.get("indicators", {})
    rsi = ind.get("rsi", 50)
    macd = ind.get("macd", "neutral")

    lines = [
        f"📈 **{name}** {price} 元（{change_str}）",
        f"",
    ]

    if action == "buy":
        # 检查是否真的应该买
        bullish_signals = []
        if rsi < 40: bullish_signals.append(f"RSI={rsi:.0f} 接近超卖，入场风险较小")
        if macd in ["bullish", "bullish_cross"]: bullish_signals.append("MACD 处于多头或金叉状态")
        if tech.get("trend") in ["upward", "strong_upward"]: bullish_signals.append(f"趋势向上（{_trend_label(tech.get('trend'))})")

        risk_warnings = []
        if rsi > 65: risk_warnings.append(f"RSI={rsi:.0f} 已偏高，追高风险大")
        if macd == "bearish": risk_warnings.append("MACD 仍为空头，动能不足")
        if tech.get("trend") in ["downward", "strong_downward"]: risk_warnings.append("当前趋势向下，不宜逆势买入")

        lines.append(f"**我的建议：可以买入**")
        lines.append(f"")
        if bullish_signals:
            lines.append(f"支持买入的依据：")
            for s in bullish_signals:
                lines.append(f"  ✅ {s}")

        if risk_warnings:
            lines.append(f"")
            lines.append(f"需要注意的风险：")
            for w in risk_warnings:
                lines.append(f"  ⚠️ {w}")

        lines.append(f"")
        lines.append(f"入场价：{_fmt_price(price)} → 目标 {_fmt_price(target)} → 止损 {_fmt_price(stop)}")
        lines.append(f"建议仓位：{final.get('max_position', '待定')} | 置信度：{confidence:.0f}%")
        lines.append(f"风险等级：{risk.get('risk_level', 'unknown')}")

    elif action in ["hold", "wait"]:
        # 还没到最佳买点
        bullish = []
        bearish = []
        if rsi < 30: bullish.append(f"RSI {rsi:.0f} 已超卖")
        elif rsi > 60: bearish.append(f"RSI {rsi:.0f} 偏高")
        if macd == "bullish_cross": bullish.append("MACD 形成金叉")
        if macd == "bearish_cross": bearish.append("MACD 尚未形成金叉")

        lines.append(f"**我的建议：再等等，不急**")
        lines.append(f"")
        if bullish:
            lines.append(f"多头信号：{'，'.join(bullish)}")
        if bearish:
            lines.append(f"当前顾虑：{'，'.join(bearish)}")
        lines.append(f"")
        lines.append(f"理由：{final.get('reason', '当前价格未达到理想入场条件')}")
        if sup := tech.get("support_levels", []):
            lines.append(f"建议关注支撑位 {_fmt_price(sup[0])} 附近是否能企稳，企稳后再考虑买入。")
        lines.append(f"置信度：{confidence:.0f}%")

    else:  # sell
        lines.append(f"**我的建议：现在不建议买入**")
        lines.append(f"理由：{final.get('reason', '当前不适合买入')}")
        if sup := tech.get("support_levels", []):
            lines.append(f"如果已持有，可关注 {_fmt_price(sup[0])} 支撑位能否守住。")

    return "\n".join(lines)


def _sell_reply(name, price, change_str, tech, fund, sent, signal, final, risk):
    """卖出咨询回复"""
    action = final.get("action", "wait")
    confidence = final.get("confidence", 0) * 100
    target = final.get("target_price")
    stop = final.get("stop_loss")

    ind = tech.get("indicators", {})
    rsi = ind.get("rsi", 50)
    macd = ind.get("macd", "neutral")
    sup = tech.get("support_levels", [])

    lines = [
        f"📉 **{name}** {price} 元（{change_str}）",
        f"",
    ]

    if action == "sell":
        bearish_signals = []
        if rsi > 65: bearish_signals.append(f"RSI={rsi:.0f} 处于超买区域")
        if macd in ["bearish", "bearish_cross"]: bearish_signals.append("MACD 空头或死叉")
        if tech.get("trend") in ["downward", "strong_downward"]: bearish_signals.append(f"趋势向下（{_trend_label(tech.get('trend'))})")

        lines.append(f"**我的建议：可以考虑卖出**")
        lines.append(f"")
        if bearish_signals:
            lines.append(f"支持卖出的依据：")
            for s in bearish_signals:
                lines.append(f"  ✅ {s}")
        lines.append(f"")
        lines.append(f"理由：{final.get('reason', '出现明确卖出信号')}")
        if target:
            lines.append(f"目标价 {_fmt_price(target)} 已基本达到，建议获利了结。")
        lines.append(f"置信度：{confidence:.0f}%")

    elif action == "hold":
        lines.append(f"**我的建议：继续持有**")
        lines.append(f"理由：{final.get('reason', '尚未出现明确卖出信号')}")
        if rsi > 70:
            lines.append(f"")
            lines.append(f"⚠️ 但需注意：RSI={rsi:.0f} 已超买，可分批减仓锁定利润。")
        if target:
            lines.append(f"目标价 {_fmt_price(target)} 尚未到达，趋势仍在可持有阶段。")

    else:  # wait or buy
        lines.append(f"**我的建议：持仓不动**")
        lines.append(f"理由：{final.get('reason', '当前信号不明确，不宜仓促决策')}")
        if sup:
            lines.append(f"重要支撑位 {_fmt_price(sup[0])}，跌破后再考虑减仓。")

    return "\n".join(lines)


def _hold_reply(name, price, change_str, tech, signal, final):
    """持仓咨询回复"""
    action = final.get("action", "wait")
    lines = [
        f"📊 **{name}** {price} 元（{change_str}）",
        f"",
        f"**建议：继续持有**",
        f"理由：{final.get('reason', '趋势未变，继续等待机会')}",
    ]
    sup = tech.get("support_levels", [])
    if sup:
        lines.append(f"关键支撑 {_fmt_price(sup[0])}，跌破需警惕。")
    lines.append(f"置信度 {final.get('confidence',0)*100:.0f}%")
    return "\n".join(lines)


def _compare_reply(name, price, change_str, tech, fund, bull, bear, signal, final):
    """对比型回复"""
    lines = [
        f"⚖️ **{name}** {price} 元（{change_str}）",
        f"",
    ]
    bull_t = bull.get("target_price")
    bear_t = bear.get("target_price")
    upside = (bull_t - price) / price * 100 if bull_t else 0
    downside = (price - bear_t) / price * 100 if bear_t else 0

    lines.append(f"多方视角（看涨）：")
    lines.append(f"  目标 {_fmt_price(bull_t)}（潜在上涨 {upside:.1f}%）")
    lines.append(f"  {bull.get('thesis', bull.get('analysis',''))}")
    lines.append(f"")
    lines.append(f"空方视角（看跌）：")
    lines.append(f"  目标 {_fmt_price(bear_t)}（潜在下跌 {downside:.1f}%）")
    lines.append(f"  {bear.get('thesis', bear.get('analysis',''))}")
    lines.append(f"")
    lines.append(f"综合建议：{_action_text(final.get('action','wait'))}（置信度 {final.get('confidence',0)*100:.0f}%）")
    lines.append(f"盈亏比：{upside:.1f}% / {downside:.1f}% = {upside/downside:.1f}x")
    return "\n".join(lines)


if __name__ == "__main__":
    import json
    from talent_link.agents.stock_analyst import StockAnalyst
    from talent_link.skills.nlp_parser import parse as parse_query

    tests = [
        ("腾讯走势怎么样", "analyze"),
        ("腾讯现在建议买入吗", "buy"),
        ("持仓的腾讯要不要卖", "sell"),
    ]
    for msg, expected_intent in tests:
        print(f"\n{'='*55}")
        print(f"输入: {msg}")
        a = StockAnalyst("0700.HK")
        r = a.analyze()
        result = generate_response(msg, r)
        print(f"意图: {result['intent']} (expected: {expected_intent})")
        print(f"回复预览:\n{result['reply'][:300]}")
