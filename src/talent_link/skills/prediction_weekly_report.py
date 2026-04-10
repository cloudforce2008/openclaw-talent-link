# -*- coding: utf-8 -*-
"""
Prediction Weekly Report - 每周预测胜率报告
每周一早上9点自动运行：
1. 检查所有到期的预测
2. 获取最新实际价格
3. 评分并计算胜率
4. 生成飞书卡片报告
"""

import sys
from pathlib import Path

# 确保 talent_link 可导入
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from talent_link.skills.prediction_tracker import (
    get_summary,
    get_predictions_by_symbol,
    _load,
    _save,
)
from talent_link.skills.data_fetcher import DataFetcher


def fetch_actual_prices(symbols: list) -> dict:
    """获取各股票当前/最新价格"""
    fetcher = DataFetcher()
    prices = {}
    for sym in set(symbols):
        try:
            data = fetcher.fetch(sym, "港股")
            prices[sym] = data.get("current_price", 0)
        except Exception:
            prices[sym] = 0
    return prices


def auto_check_predictions(actual_prices: dict, prediction_type: str = None) -> dict:
    """
    自动核查所有已到期且未核查的预测
    用传入的实际价格评分
    """
    from datetime import datetime

    data = _load()
    now = datetime.now()
    checked = []
    results = []

    for pred in data["predictions"]:
        if pred["status"] != "active":
            continue

        # 未到检查日期
        check_at = datetime.fromisoformat(pred["check_at"])
        if check_at > now:
            continue

        sym = pred["symbol"]
        actual = actual_prices.get(sym, 0)
        if actual <= 0:
            # 无法获取价格，标记为过期
            pred["status"] = "expired"
            pred["notes"] = "到期但无法获取实际价格"
            checked.append(pred["id"])
            results.append({"pred": pred, "score": None, "verdict": "⚪ 无法验证"})
            continue

        # 计算得分
        entry = pred["price_at_prediction"]
        target = pred["target_price"]
        stop = pred["stop_loss"]
        direction = pred["direction"]

        if direction == "long":
            if actual <= stop:
                score, verdict = 0.0, "❌ 止损亏"
            elif actual >= target:
                score, verdict = 1.0, "✅ 止盈赚"
            else:
                ratio = (actual - entry) / (target - entry) if target != entry else 0.5
                score, verdict = max(0.0, min(1.0, ratio)), "⚠️ 区间内"
        else:  # short
            if actual >= stop:
                score, verdict = 0.0, "❌ 止损亏"
            elif actual <= target:
                score, verdict = 1.0, "✅ 做空赚"
            else:
                ratio = (entry - actual) / (entry - target) if entry != target else 0.5
                score, verdict = max(0.0, min(1.0, ratio)), "⚠️ 区间内"

        pred["status"] = "checked"
        pred["checked_at"] = now.isoformat()
        pred["actual_price"] = actual
        pred["score"] = round(score, 3)
        pred["deviation_pct"] = round(abs(actual - entry) / entry * 100, 2)
        pred["verdict"] = verdict

        checked.append(pred["id"])
        results.append({"pred": pred, "score": score, "verdict": verdict})

    if checked:
        _save(data)

    return {
        "checked_count": len(checked),
        "results": results,
        "summary": get_summary(),
    }


def generate_report_text(report_data: dict) -> str:
    """生成文字报告（双轨）"""
    s = report_data.get("summary", {})
    results = report_data.get("results", [])

    def _rate_str(r):
        return f"{r.get('win_rate', 0):.1f}%（{r.get('correct',0)}/{r.get('total',0)}）"

    def _acceptable_str(r):
        return f"{r.get('acceptable_rate', 0):.1f}%（{r.get('correct',0)+r.get('acceptable',0)}/{r.get('total',0)}）"

    lines = [
        "📊 **预测胜率周报**",
        "",
        f"本周核查：{report_data['checked_count']} 条（含每日+中期轨道）",
        "",
        "**【每日趋势】** 次日收盘价核查，追踪方向对错",
        f"  胜率（严格）：{_rate_str(s.get('daily', {}))}",
        f"  胜率（宽松）：{_acceptable_str(s.get('daily', {}))}",
        "",
        "**【中期趋势】** 30天核查，追踪目标价/止损",
        f"  胜率（严格）：{_rate_str(s.get('monthly', {}))}",
        f"  胜率（宽松）：{_acceptable_str(s.get('monthly', {}))}",
        "",
    ]

    # 分轨道显示详情
    if results:
        by_type = {}
        for r in results:
            pt = r['pred'].get('prediction_type', 'monthly')
            by_type.setdefault(pt, []).append(r)

        for ptype in ['daily', 'monthly']:
            if ptype not in by_type:
                continue
            label = "每日趋势" if ptype == 'daily' else "中期趋势"
            lines.append(f"**【{label}】详情：**")
            for r in by_type[ptype][-5:]:
                p = r['pred']
                icon = "📅" if ptype == 'daily' else "📆"
                direction = "📈" if p['direction'] == 'long' else "📉"
                score = f"{r['score']:.0%}" if r.get('score') is not None else "—"
                actual = p.get('actual_price', '?')
                entry = p['price_at_prediction']
                lines.append(
                    f"{icon}{direction} {p['name']}({p['symbol']}) "
                    f"{entry}→{actual} | {r.get('verdict', '?')} | 得分{score}"
                )
            lines.append("")
    else:
        lines.append("本周无到期预测待核查。\n")

    # 全局汇总
    all_s = s.get('all', {})
    lines.append(
        f"_历史累计 {all_s.get('total', 0)} 条 ｜ "
        f"正确 {all_s.get('correct', 0)} ｜ "
        f"可接受 {all_s.get('acceptable', 0)} ｜ "
        f"错误 {all_s.get('wrong', 0)}_\n"
    )
    lines.append("_*仅供参考，不构成投资建议*_")

    return "\n".join(lines)


def run(prediction_type: str = None) -> dict:
    """
    核查到期预测 + 生成报告
    prediction_type: None=全部 | 'daily'=每日趋势 | 'monthly'=中期趋势
    """
    data = _load()
    active_preds = [
        p for p in data["predictions"]
        if p["status"] == "active"
        and (prediction_type is None or p.get("prediction_type") == prediction_type)
    ]
    symbols = list(set(p["symbol"] for p in active_preds))
    prices = fetch_actual_prices(symbols)
    report_data = auto_check_predictions(prices, prediction_type)
    report_text = generate_report_text(report_data)
    print(report_text)
    return report_data


if __name__ == "__main__":
    import sys
    pt = sys.argv[1] if len(sys.argv) > 1 else None
    run(pt)
