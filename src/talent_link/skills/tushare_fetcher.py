#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A股 Tushare 数据获取器 - 在独立子进程中运行，绕过 apport_hook 干扰
"""

import sys
import json

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: tushare_fetcher.py <股票代码>"}))
        sys.exit(1)
    
    symbol = sys.argv[1]
    
    try:
        import tushare as ts
        
        # 单只股票实时行情
        df = ts.get_realtime_quotes(symbol)
        
        if df is None or df.empty:
            print(json.dumps({"error": f"未找到股票 {symbol}"}))
            sys.exit(1)
        
        r = df.iloc[0]
        price = float(r['price'])
        pre_close = float(r['pre_close'])
        change = price - pre_close
        pct = change / pre_close * 100 if pre_close > 0 else 0
        
        result = {
            'symbol': symbol,
            'name': r['name'],
            'current_price': price,
            'change_percent': pct,
            'open': float(r['open']),
            'high': float(r['high']),
            'low': float(r['low']),
            'prev_close': pre_close,
            'volume': int(r['volume']),
            'amount': float(r['amount']),
            'update_time': f"{r['date']} {r['time']}",
            'source': 'tushare'
        }
        
        print(json.dumps(result, ensure_ascii=False))
        
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)
