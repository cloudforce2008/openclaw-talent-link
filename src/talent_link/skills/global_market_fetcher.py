"""
Global Market Data Fetcher
获取：美股指数、黄金、原油、地缘政治信号
"""

import subprocess
import json
from datetime import datetime
from typing import Dict


YAHOO_SCRIPT = "/root/.openclaw/workspace/skills/yahoo-finance/scripts/query.mjs"

# 地缘政治事件映射（基于已知数据，实时需接入新闻）
GEOPOLITICAL_EVENTS = {
    "iran_israel": {
        "status": "elevated",
        "description": "中东局势持续紧张",
        "impact": "positive",  # 避险情绪对港股AI板块的影响
    },
    "us_china": {
        "status": "tariff_risks",
        "description": "中美贸易摩擦反复",
        "impact": "negative",
    }
}


def fetch_yahoo_quote(symbol: str) -> Dict:
    """获取单只股票/指数报价"""
    try:
        result = subprocess.run(
            ['node', YAHOO_SCRIPT, 'quote', symbol],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            return None
        
        output = result.stdout
        data = {}
        for line in output.split('\n'):
            if '当前价格:' in line:
                data['price'] = _extract_number(line)
            elif '涨跌幅:' in line:
                data['change_percent'] = _extract_number(line)
            elif '前收盘:' in line:
                data['prev_close'] = _extract_number(line)
            elif '开盘价:' in line:
                data['open'] = _extract_number(line)
            elif '最高价:' in line:
                data['high'] = _extract_number(line)
            elif '最低价:' in line:
                data['low'] = _extract_number(line)
            elif '成交量:' in line:
                data['volume'] = _extract_number(line)
        return data
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return None


def _extract_number(text: str) -> float:
    import re
    numbers = re.findall(r'-?[\d,]+\.?\d*', text.replace(',', ''))
    if numbers:
        try:
            return float(numbers[0])
        except:
            return 0
    return 0


def get_us_ai_leaders() -> Dict:
    """美股AI风向标：纳指、NVDA、费城半导体"""
    nasdaq = fetch_yahoo_quote('^IXIC')
    sp500 = fetch_yahoo_quote('^GSPC')
    nvda = fetch_yahoo_quote('NVDA')
    
    return {
        'nasdaq': nasdaq,
        'sp500': sp500,
        'nvda': nvda,
    }


def get_commodities() -> Dict:
    """大宗商品：黄金、原油"""
    gold = fetch_yahoo_quote('GC=F')
    crude = fetch_yahoo_quote('CL=F')
    
    return {
        'gold': gold,
        'crude_oil': crude,
    }


def get_geopolitical_signals() -> Dict:
    """地缘政治信号"""
    return GEOPOLITICAL_EVENTS


def get_full_global_signals() -> Dict:
    """获取完整全球市场信号"""
    us_ai = get_us_ai_leaders()
    commodities = get_commodities()
    geopolitics = get_geopolitical_signals()
    
    # 信号解读
    signals = []
    
    # 纳指
    nasdaq_change = us_ai.get('nasdaq', {}).get('change_percent', 0)
    if abs(nasdaq_change) > 2:
        signals.append(f"纳指{nasdaq_change:+.2f}%（波动较大）")
    elif nasdaq_change > 0:
        signals.append(f"纳指微涨{nasdaq_change:+.2f}%")
    else:
        signals.append(f"纳指微跌{nasdaq_change:+.2f}%")
    
    # 黄金
    gold_change = commodities.get('gold', {}).get('change_percent', 0)
    signals.append(f"黄金{commodities.get('gold', {}).get('price', 0):.0f}美元({gold_change:+.2f}%)")
    
    # 原油
    crude_change = commodities.get('crude_oil', {}).get('change_percent', 0)
    signals.append(f"原油{commodities.get('crude_oil', {}).get('price', 0):.1f}美元({crude_change:+.2f}%)")
    
    # NVDA
    nvda_change = us_ai.get('nvda', {}).get('change_percent', 0)
    signals.append(f"NVDA {us_ai.get('nvda', {}).get('price', 0)}美元({nvda_change:+.2f}%)")
    
    return {
        'fetch_time': datetime.now().isoformat(),
        'us_ai_leaders': us_ai,
        'commodities': commodities,
        'geopolitics': geopolitics,
        'signals': signals,
    }


if __name__ == '__main__':
    data = get_full_global_signals()
    print(json.dumps(data, indent=2, ensure_ascii=False))
