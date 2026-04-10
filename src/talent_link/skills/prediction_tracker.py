# -*- coding: utf-8 -*-
"""
Prediction Tracker V2 - 双轨预测追踪系统

两条独立预测轨道：
1. 每日趋势（daily）  → 次日核查，追踪短期方向胜率
2. 中期趋势（monthly）→ 30天核查，追踪目标价/止损胜率

各轨道独立统计胜率，独立置信度校准
"""

import json
import time as _time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Literal

TRACKER_FILE = Path(__file__).parent.parent / "data" / "predictions.json"
TRACKER_FILE.parent.mkdir(exist_ok=True)


def _load() -> dict:
    if TRACKER_FILE.exists():
        with open(TRACKER_FILE) as f:
            return json.load(f)
    return {
        "predictions": [],
        "summary": {"total": 0, "correct": 0, "wrong": 0, "acceptable": 0},
        "by_type": {
            "daily": {"total": 0, "correct": 0, "wrong": 0, "acceptable": 0},
            "monthly": {"total": 0, "correct": 0, "wrong": 0, "acceptable": 0},
        },
    }


def _save(data: dict):
    with open(TRACKER_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def record_prediction(
    symbol: str,
    name: str,
    price_at_prediction: float,
    direction: str,  # "long" | "short"
    target_price: float,
    stop_loss: float,
    confidence: float,
    thesis_summary: str,
    market_state: str,
    prediction_type: Literal["daily", "monthly"] = "monthly",
    valid_days: int = None,
) -> str:
    """
    记录一条预测（自动根据类型设置验证期）
    - daily: 验证期1天（次日收盘价核查）
    - monthly: 验证期30天
    """
    data = _load()
    now = datetime.now()

    if valid_days is None:
        valid_days = 1 if prediction_type == "daily" else 30

    pred = {
        "id": f"{symbol}_{prediction_type[0]}_{int(_time.time() * 1000000) % (16**8):08x}",
        "symbol": symbol,
        "name": name,
        "prediction_type": prediction_type,
        "predicted_at": now.isoformat(),
        "check_at": (now + timedelta(days=valid_days)).isoformat(),
        "price_at_prediction": price_at_prediction,
        "direction": direction,
        "target_price": target_price,
        "stop_loss": stop_loss,
        "confidence": confidence,
        "thesis_summary": thesis_summary[:100],
        "market_state": market_state,
        "status": "active",  # active | checked | expired
        "actual_price": None,
        "score": None,
        "verdict": None,
        "deviation_pct": None,
        "notes": "",
    }

    data["predictions"].append(pred)
    data["summary"]["total"] += 1

    if prediction_type not in data["by_type"]:
        data["by_type"][prediction_type] = {"total": 0, "correct": 0, "wrong": 0, "acceptable": 0}
    data["by_type"][prediction_type]["total"] += 1

    _save(data)
    return pred["id"]


def _score_prediction(pred: dict, actual_price: float) -> tuple[float, str]:
    """
    计算预测得分和判定
    返回 (score, verdict_str)
    """
    entry = pred["price_at_prediction"]
    target = pred["target_price"]
    stop = pred["stop_loss"]
    direction = pred["direction"]
    pred_type = pred.get("prediction_type", "monthly")

    if entry <= 0:
        return 0.5, "⚠️ 数据异常"

    deviation_pct = abs(actual_price - entry) / entry * 100

    if pred_type == "daily":
        # 每日趋势：看方向对不对
        # 买入→次日涨=对，买入→次日跌=错
        expected_return = (target - entry) / entry  # 预期方向
        actual_return = (actual_price - entry) / entry  # 实际方向

        if direction == "long":
            if actual_return > 0.005:  # 涨超0.5%算正确
                score = 1.0
                verdict = "✅ 正确（次日上涨）"
            elif actual_return > -0.005:  # ±0.5%内算可接受
                score = 0.5
                verdict = "⚠️ 可接受（区间震荡）"
            else:
                score = 0.0
                verdict = f"❌ 错误（次日下跌{actual_return * 100:.1f}%）"
        else:  # short
            if actual_return < -0.005:
                score = 1.0
                verdict = "✅ 正确（次日下跌）"
            elif actual_return < 0.005:
                score = 0.5
                verdict = "⚠️ 可接受（区间震荡）"
            else:
                score = 0.0
                verdict = f"❌ 错误（次日上涨{actual_return * 100:.1f}%）"

    else:
        # 月度趋势：看目标/止损是否到达
        if direction == "long":
            if actual_price <= stop:
                score, verdict = 0.0, "❌ 止损亏"
            elif actual_price >= target:
                score, verdict = 1.0, "✅ 止盈赚"
            else:
                # 在区间内：实际涨幅/预期涨幅
                ratio = (actual_price - entry) / (target - entry) if target != entry else 0.5
                score = max(0.0, min(1.0, ratio))
                verdict = f"⚠️ 区间内（实际涨幅{(actual_price/entry-1)*100:.1f}%，预期{ratio*100:.1f}%）"
        else:  # short
            if actual_price >= stop:
                score, verdict = 0.0, "❌ 止损亏"
            elif actual_price <= target:
                score, verdict = 1.0, "✅ 做空赚"
            else:
                ratio = (entry - actual_price) / (entry - target) if entry != target else 0.5
                score = max(0.0, min(1.0, ratio))
                verdict = f"⚠️ 区间内"

    return score, verdict


def check_prediction(
    prediction_id: str,
    actual_price: float,
    notes: str = "",
) -> dict:
    """核查一条预测并打分"""
    data = _load()

    for pred in data["predictions"]:
        if pred["id"] != prediction_id:
            continue
        if pred["status"] == "checked":
            return {"error": "already checked", "prediction": pred}
        if pred["status"] == "expired":
            return {"error": "already expired", "prediction": pred}

        score, verdict = _score_prediction(pred, actual_price)
        now = datetime.now().isoformat()

        pred["status"] = "checked"
        pred["checked_at"] = now
        pred["actual_price"] = actual_price
        pred["score"] = round(score, 3)
        pred["verdict"] = verdict
        pred["deviation_pct"] = round(
            abs(actual_price - pred["price_at_prediction"]) / pred["price_at_prediction"] * 100, 2
        )
        pred["notes"] = notes

        # 更新各层 summary
        def _update_summary(s):
            s["total"] = s.get("total", 0) + 1
            if score >= 0.7:
                s["correct"] = s.get("correct", 0) + 1
            elif score >= 0.4:
                s["acceptable"] = s.get("acceptable", 0) + 1
            else:
                s["wrong"] = s.get("wrong", 0) + 1

        _update_summary(data["summary"])
        ptype = pred.get("prediction_type", "monthly")
        _update_summary(data["by_type"].get(ptype, {"total": 0, "correct": 0, "wrong": 0, "acceptable": 0}))

        _save(data)
        return {"prediction": pred, "verdict": verdict, "score": score}

    return {"error": "prediction not found"}


def auto_check_expired(prediction_type: str = None) -> list:
    """自动核查所有已到期的预测（可按类型过滤）"""
    data = _load()
    now = datetime.now()
    checked = []

    for pred in data["predictions"]:
        if pred["status"] != "active":
            continue
        if prediction_type and pred.get("prediction_type") != prediction_type:
            continue

        check_at = datetime.fromisoformat(pred["check_at"])
        if check_at > now:
            continue

        pred["status"] = "expired"
        pred["notes"] = "验证期到期，未获取到实际价格"
        checked.append(pred["id"])

    if checked:
        _save(data)

    return checked


def get_summary(by_type: bool = True) -> dict:
    """获取胜率统计，可按类型分开"""
    data = _load()
    s = data.get("summary", {})

    def _rate(s):
        total = s.get("total", 0)
        correct = s.get("correct", 0)
        acceptable = s.get("acceptable", 0)
        wrong = s.get("wrong", 0)
        win_rate = round(correct / total * 100, 1) if total > 0 else 0
        acceptable_rate = round((correct + acceptable) / total * 100, 1) if total > 0 else 0
        return {
            "total": total,
            "correct": correct,
            "acceptable": acceptable,
            "wrong": wrong,
            "win_rate": win_rate,
            "acceptable_rate": acceptable_rate,
        }

    result = {
        "all": _rate(s),
    }

    if by_type:
        result["daily"] = _rate(data.get("by_type", {}).get("daily", {}))
        result["monthly"] = _rate(data.get("by_type", {}).get("monthly", {}))

    # 最近10条
    result["recent"] = [
        {**p, "score": p.get("score")}
        for p in sorted(data["predictions"], key=lambda x: x["predicted_at"], reverse=True)[:10]
    ]

    return result


def get_calibrated_confidence(
    base_confidence: float,
    symbol: str,
    prediction_type: Literal["daily", "monthly"],
    market_state: str,
) -> dict:
    """
    基于对应轨道的胜率为新预测置信度加权
    - daily 和 monthly 各用各的历史胜率
    """
    data = _load()

    # 该股票在该轨道的胜率
    preds = [
        p for p in data["predictions"]
        if p["symbol"] == symbol
        and p.get("prediction_type") == prediction_type
        and p["status"] == "checked"
    ]
    if preds:
        avg_score = sum(p["score"] for p in preds) / len(preds)
        symbol_adj = (avg_score - 0.5) * 0.1
    else:
        avg_score = None
        symbol_adj = 0

    # 该轨道全局胜率
    type_data = data.get("by_type", {}).get(prediction_type, {})
    total = type_data.get("total", 0)
    if total >= 3:
        global_rate = (type_data.get("correct", 0) + type_data.get("acceptable", 0) * 0.5) / total
        global_adj = (global_rate - 0.5) * 0.05
    else:
        global_adj = 0

    total_adj = symbol_adj + global_adj
    calibrated = base_confidence + total_adj
    calibrated = max(0.3, min(0.95, calibrated))

    return {
        "calibrated_confidence": round(calibrated, 3),
        "adjustments": {
            "symbol_history": round(symbol_adj, 4) if avg_score is not None else "N/A",
            "global_adjustment": round(global_adj, 4),
        },
        "source_data": {
            "symbol_history_avg": round(avg_score, 3) if avg_score is not None else None,
            "symbol_count": len(preds),
            "track_total": total,
        },
    }


# ── CLI ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("summary")
    sub.add_parser("list")
    args = parser.parse_args()

    if args.cmd == "summary":
        s = get_summary()
        print(f"\n{'='*50}")
        print("  预测胜率统计")
        print(f"{'='*50}")
        for track in ["all", "daily", "monthly"]:
            if track not in s:
                continue
            r = s[track]
            label = {"all": "综合", "daily": "每日趋势", "monthly": "中期趋势"}[track]
            print(f"\n  【{label}】({r['total']}条)")
            print(f"    ✅ 正确: {r['correct']}  ⚠️ 可接受: {r['acceptable']}  ❌ 错误: {r['wrong']}")
            print(f"    胜率（严格): {r['win_rate']}%  胜率（宽松): {r['acceptable_rate']}%")
        print(f"{'='*50}\n")

    elif args.cmd == "list":
        for p in get_summary()["recent"]:
            icon = {"active": "🟡", "checked": "🟢", "expired": "⚪"}.get(p["status"], "⚪")
            track_icon = "📅" if p.get("prediction_type") == "daily" else "📆"
            score = f"{p['score']:.0%}" if p.get("score") is not None else "—"
            print(f"{icon}{track_icon} {p['name']}({p['symbol']}) {p['predicted_at'][:10]} "
                  f"| {p['direction']} | {p.get('verdict', '待验证')} | {score}")
