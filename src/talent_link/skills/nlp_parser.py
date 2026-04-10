# -*- coding: utf-8 -*-
"""
自然语言解析器 - 数字人才市场
从自然语言中提取股票代码和用户意图
"""

import re
from dataclasses import dataclass
from typing import Optional


# 常见股票名称映射（港股+A股）
STOCK_NAME_MAP = {
    # 港股 AI 相关
    "智谱": "2513.HK",
    "智谱AI": "2513.HK",
    "minimax": "0100.HK",
    "MiniMax": "0100.HK",
    "小魔阁": "0100.HK",
    "腾讯": "0700.HK",
    "阿里": "9988.HK",
    "阿里巴巴": "9988.HK",
    "美团": "3690.HK",
    "京东": "9618.HK",
    "百度": "9888.HK",
    "小米": "1810.HK",
    "比亚迪": "1211.HK",
    "宁德时代": "300750.SZ",
    # A股
    "平安银行": "000001",
    "平安": "000001",
    "万科": "000002",
    "茅台": "600519",
    "贵州茅台": "600519",
    "工商银行": "601398",
    "中国平安": "601318",
    "中信证券": "600030",
    "东方财富": "300059",
    "宁德": "300750",
    # ETF
    "纳指ETF": "513100",
    "恒生科技": "513180",
}


INTENT_PATTERNS = {
    "analyze": [
        r"分析",
        r"看看",
        r"查一下",
        r"看一下",
        r"怎么看",
        r"走势",
        r"行情",
    ],
    "buy": [
        r"能买",
        r"可以买",
        r"买.*吗",
        r"建议买",
        r"买入",
        r"要不要买",
    ],
    "sell": [
        r"能卖",
        r"可以卖",
        r"卖.*吗",
        r"建议卖",
        r"卖出",
        r"要不要卖",
        r"减仓",
    ],
    "hold": [
        r"持仓",
        r"持有",
        r"继续持有",
        r"拿着",
        r"不动",
    ],
    "compare": [
        r"对比",
        r"比较",
        r"哪个好",
        r"选哪个",
    ],
}


@dataclass
class ParsedQuery:
    """解析结果"""
    raw: str                    # 原始输入
    symbol: Optional[str] = None  # 股票代码
    name: Optional[str] = None    # 股票名称
    intent: str = "analyze"       # 意图：analyze/buy/sell/hold/compare
    confidence: float = 0.0       # 解析置信度


def extract_symbol(text: str) -> Optional[tuple[str, str]]:
    """
    从文本中提取股票代码
    返回: (symbol, name) 或 None
    """
    text = text.strip()

    # 1. 直接匹配代码格式
    # 港股: 4位数字.HK 或 4位数字.SZ 或 4位数字.SS
    m = re.search(r'(\d{4}\.(?:HK|SZ|SS))', text, re.IGNORECASE)
    if m:
        return m.group(1).upper(), m.group(1)

    # A股: 6位数字
    m = re.search(r'\b(\d{6})\b', text)
    if m:
        code = m.group(1)
        # 判断沪市还是深市
        if code.startswith(('6', '5', '9')):
            return f"{code}.SS", code  # 沪市
        else:
            return f"{code}.SZ", code  # 深市

    # 2. 匹配股票名称
    for name, code in STOCK_NAME_MAP.items():
        if name in text:
            return code, name

    return None, None


def extract_intent(text: str) -> tuple[str, float]:
    """
    从文本中提取用户意图
    返回: (intent, confidence)
    """
    scores = {}
    for intent, patterns in INTENT_PATTERNS.items():
        score = 0
        for p in patterns:
            if re.search(p, text):
                score += 1
        if score > 0:
            scores[intent] = score

    if not scores:
        return "analyze", 0.5

    # 取最高分
    best = max(scores, key=scores.get)
    confidence = min(scores[best] / 2.0, 1.0)
    return best, confidence


def parse(text: str) -> ParsedQuery:
    """
    主解析函数
    从自然语言中提取股票代码和意图
    """
    symbol, name = extract_symbol(text)
    intent, confidence = extract_intent(text)

    return ParsedQuery(
        raw=text,
        symbol=symbol,
        name=name,
        intent=intent,
        confidence=confidence,
    )


if __name__ == "__main__":
    # 简单测试
    test_cases = [
        "帮我看看 2513.HK",
        "智谱AI现在能买吗",
        "分析一下贵州茅台",
        "腾讯走势怎么样",
        "000001 平安银行",
        "持仓的股票要不要卖",
    ]
    for t in test_cases:
        r = parse(t)
        print(f"输入: {t}")
        print(f"  -> 代码: {r.symbol} | 名称: {r.name} | 意图: {r.intent} | 置信度: {r.confidence}")
        print()
