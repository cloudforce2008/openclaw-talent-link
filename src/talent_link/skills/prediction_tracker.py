# -*- coding: utf-8 -*-
"""
Prediction Tracker - 预测追踪与胜率反馈系统

记录每次分析产生的预测（目标价/止损/方向）
定期验证预测准确性，计算胜率
用历史胜率校准后续置信度
"""

import json
import sys
import time as _time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

TRACKER_FILE = Path(__file__).parent.parent / "data" / "predictions.json"
TRACKER_FILE.parent.mkdir(exist_ok=True)


def _load() -> dict:
    if TRACKER_FILE.exists():
        with open(TRACKER_FILE) as f:
            return json.load(f)
    return {"predictions": [], "summary": {"total": 0, "correct": 0, "wrong": 0}}


def _save(data: dict):
    with open(TRACKER_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def record_prediction(
    symbol: str,
    name: str,
    price_at_prediction: float,
    direction: str,  # "long" | "short" | "hold"
    target_price: float,
    stop_loss: float,
    confidence: float,
    thesis_summary: str,
    market_state: str,
    valid_days: int = 30,
) -> str:
    """
    记录一次预测，供后续验证
    返回 prediction_id
    """
    data = _load()
    now = datetime.now()

    pred = {
        "id": f"{symbol}_{int(_time.time()*1000000) % (16**8):08x}",
        "symbol": symbol,
        "name": name,
        "predicted_at": now.isoformat(),
        "check_at": (now + timedelta(days=valid_days)).isoformat(),
        "price_at_prediction": price_at_prediction,
        "direction": direction,
        "target_price": target_price,
        "stop_loss": stop_loss,
        "confidence": confidence,
        "thesis_summary": thesis_summary,
        "market_state": market_state,
        "status": "active",  # active | checked | expired
        "outcome": None,
        "score": None,  # 1.0=完全正确, 0.5=偏差可接受, 0=错误
        "notes": "",
    }

    data["predictions"].append(pred)
    data["summary"]["total"] += 1
    _save(data)

    return pred["id"]


def check_and_score_prediction(
    prediction_id: str,
    actual_price: float,
    notes: str = "",
) -> dict:
    """
    手工核查一条预测（理想情况下定时任务自动核查）
    计算得分并更新 summary
    """
    data = _load()

    for pred in data["predictions"]:
        if pred["id"] != prediction_id:
            continue

        if pred["status"] == "checked":
            return {"error": "already checked", "prediction": pred}

        entry_price = pred["price_at_prediction"]
        target = pred["target_price"]
        stop = pred["stop_loss"]
        direction = pred["direction"]

        # 计算偏离度
        if entry_price > 0:
            deviation_pct = abs(actual_price - entry_price) / entry_price
        else:
            deviation_pct = 1.0

        # 打分逻辑
        if direction == "hold":
            # 持仓建议：止损是否被触达
            if actual_price <= stop:
                score = 1.0  # 止损保护有效
            elif actual_price >= target:
                score = 1.0  # 目标达成
            else:
                # 仍在区间，保守给0.6
                score = 0.6

        elif direction == "long":
            if actual_price <= stop:
                score = 0.0  # 止损亏
            elif actual_price >= target:
                score = 1.0  # 止盈赚
            else:
                # 未到目标但未止损 → 偏差评分
                # 预期涨 X%，实际涨 Y%
                expected_return = (target - entry_price) / entry_price
                actual_return = (actual_price - entry_price) / entry_price
                if expected_return > 0:
                    ratio = actual_return / expected_return
                    score = max(0.0, min(1.0, ratio))
                else:
                    score = 0.5

        else:  # short
            if actual_price >= stop:
                score = 0.0
            elif actual_price <= target:
                score = 1.0
            else:
                expected_return = (entry_price - target) / entry_price
                actual_return = (entry_price - actual_price) / entry_price
                if expected_return > 0:
                    ratio = actual_return / expected_return
                    score = max(0.0, min(1.0, ratio))
                else:
                    score = 0.5

        # 判断对错（阈值0.5）
        if score >= 0.7:
            verdict = "✅ 正确"
        elif score >= 0.4:
            verdict = "⚠️ 可接受"
        else:
            verdict = "❌ 错误"

        pred["status"] = "checked"
        pred["checked_at"] = datetime.now().isoformat()
        pred["actual_price"] = actual_price
        pred["outcome"] = verdict
        pred["score"] = round(score, 3)
        pred["deviation_pct"] = round(deviation_pct * 100, 2)
        pred["notes"] = notes

        # 更新 summary
        data["summary"]["total"] = data["summary"].get("total", 1)
        data["summary"]["correct"] = data["summary"].get("correct", 0)
        data["summary"]["wrong"] = data["summary"].get("wrong", 0)
        data["summary"]["acceptable"] = data["summary"].get("acceptable", 0)

        if score >= 0.7:
            data["summary"]["correct"] += 1
        elif score >= 0.4:
            data["summary"]["acceptable"] += 1
        else:
            data["summary"]["wrong"] += 1

        _save(data)

        return {
            "prediction": pred,
            "verdict": verdict,
            "score": score,
            "deviation_pct": pred["deviation_pct"],
        }

    return {"error": "prediction not found"}


def get_summary() -> dict:
    """获取胜率统计摘要"""
    data = _load()
    s = data.get("summary", {})
    total = s.get("total", 0)
    correct = s.get("correct", 0)
    acceptable = s.get("acceptable", 0)
    wrong = s.get("wrong", 0)

    win_rate = round(correct / total * 100, 1) if total > 0 else 0
    acceptable_rate = round((correct + acceptable) / total * 100, 1) if total > 0 else 0

    return {
        "total_predictions": total,
        "correct": correct,
        "acceptable": acceptable,
        "wrong": wrong,
        "win_rate": win_rate,
        "acceptable_rate": acceptable_rate,
        "recent_predictions": data["predictions"][-10:],
    }


def get_predictions_by_symbol(symbol: str) -> list:
    """获取某股票的历史预测"""
    data = _load()
    return [p for p in data["predictions"] if p["symbol"] == symbol]


def get_calibrated_confidence(
    base_confidence: float,
    symbol: str,
    market_state: str,
    thesis_keywords: list,
) -> float:
    """
    基于历史胜率校准置信度

    Args:
        base_confidence: 原始置信度（0-1）
        symbol: 股票代码
        market_state: 当前市场状态
        thesis_keywords: 论据关键词列表
    """
    data = _load()

    # 1. 该股票的历史胜率
    symbol_preds = [p for p in data["predictions"]
                    if p["symbol"] == symbol and p["status"] == "checked"]
    if symbol_preds:
        avg_score = sum(p["score"] for p in symbol_preds) / len(symbol_preds)
        symbol_adjustment = (avg_score - 0.5) * 0.1  # ±5%
    else:
        avg_score = None
        symbol_adjustment = 0

    # 2. 同类市场状态下的胜率
    market_preds = [p for p in data["predictions"]
                    if p.get("market_state") == market_state and p["status"] == "checked"]
    if market_preds:
        market_avg = sum(p["score"] for p in market_preds) / len(market_preds)
        market_adjustment = (market_avg - 0.5) * 0.05
    else:
        market_adjustment = 0

    # 3. 全局胜率
    s = data.get("summary", {})
    total = s.get("total", 0)
    if total >= 5:
        global_rate = (s.get("correct", 0) + s.get("acceptable", 0) * 0.5) / total
        global_adjustment = (global_rate - 0.5) * 0.05
    else:
        global_adjustment = 0

    # 综合调整
    total_adjustment = symbol_adjustment + market_adjustment + global_adjustment
    calibrated = base_confidence + total_adjustment

    # 限制范围
    calibrated = max(0.3, min(0.95, calibrated))

    return {
        "calibrated_confidence": round(calibrated, 3),
        "adjustments": {
            "symbol_history": round(symbol_adjustment, 4) if avg_score is not None else "N/A",
            "market_state_adjustment": round(market_adjustment, 4),
            "global_adjustment": round(global_adjustment, 4),
        },
        "source_data": {
            "symbol_history_avg": round(avg_score, 3) if avg_score is not None else None,
            "symbol_predictions_count": len(symbol_preds),
            "global_predictions": total,
            "global_win_rate": s.get("win_rate", 0),
        },
    }


def auto_check_expired_predictions() -> list:
    """
    定时任务：自动检查已到期的预测
    需要外部传入实际价格（可从 data_fetcher 获取）
    """
    data = _load()
    now = datetime.now()
    checked = []

    for pred in data["predictions"]:
        if pred["status"] != "active":
            continue

        check_at = datetime.fromisoformat(pred["check_at"])
        if check_at > now:
            continue

        # 到期了但没有实际价格 → 标记为过期，不评分
        pred["status"] = "expired"
        pred["notes"] = "验证期到期，未获取到实际价格"
        checked.append(pred["id"])

    if checked:
        _save(data)

    return checked


if __name__ == "__main__":
    # CLI 工具
    import argparse

    parser = argparse.ArgumentParser(description="预测追踪工具")
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("summary", help="查看胜率统计")
    sub.add_parser("list", help="查看最近预测")

    args = parser.parse_args()

    if args.cmd == "summary":
        s = get_summary()
        print(f"\n{'='*50}")
        print(f"  预测胜率统计（{s['total_predictions']} 条）")
        print(f"{'='*50}")
        print(f"  ✅ 正确:   {s['correct']} 条")
        print(f"  ⚠️ 可接受: {s['acceptable']} 条")
        print(f"  ❌ 错误:   {s['wrong']} 条")
        print(f"  ──────────────────────")
        print(f"  胜率（严格）: {s['win_rate']}%")
        print(f"  胜率（宽松）: {s['acceptable_rate']}%")
        print(f"{'='*50}\n")

    elif args.cmd == "list":
        s = get_summary()
        for p in s["recent_predictions"]:
            status_icon = {"active": "🟡", "checked": "🟢", "expired": "⚪"}.get(p["status"], "⚪")
            print(f"{status_icon} {p['name']}({p['symbol']}) {p['predicted_at'][:10]} "
                  f"| 方向:{p['direction']} | {p.get('outcome', '待验证')} | 得分:{p.get('score', '?')}")

    else:
        s = get_summary()
        print(f"共 {s['total_predictions']} 条预测 | 胜率 {s['win_rate']}%")
