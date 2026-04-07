#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A股数据获取器 - 通过子进程调用，绕过 apport_python_hook 干扰
"""

import sys
import json

def main():
    if len(sys.argv) < 2:
        print("Usage: akshare_fetcher.py <A股代码>")
        sys.exit(1)
    
    symbol = sys.argv[1]
    
    # 先导入 platform（阻止被apport覆盖）
    import platform as _platform
    _platform.python_implementation()
    
    try:
        import akshare as ak
        
        if symbol.startswith('6'):
            full = f"sh{symbol}"
        else:
            full = f"sz{symbol}"
        
        df = ak.stock_zh_a_spot_em()
        row = df[df['代码'] == symbol]
        
        if row.empty:
            print(json.dumps({"error": f"未找到股票 {symbol}"}))
            sys.exit(1)
        
        r = row.iloc[0]
        
        current_price = float(r['最新价']) if r['最新价'] != '-' else 0
        prev_close = float(r['昨收']) if r['昨收'] != '-' else 0
        
        if prev_close > 0:
            change_pct = (current_price - prev_close) / prev_close * 100
        else:
            change_pct = 0
        
        volume = float(r['成交量']) * 100 if r['成交量'] != '-' else 0
        turnover = float(r['成交额']) if r['成交额'] != '-' else 0
        
        quote = {
            'price': current_price,
            'change_percent': change_pct,
            'volume': volume,
            'high': float(r['最高']) if r['最高'] != '-' else 0,
            'low': float(r['最低']) if r['最低'] != '-' else 0,
            'open': float(r['今开']) if r['今开'] != '-' else 0,
            'prev_close': prev_close,
        }
        
        result = {
            'symbol': symbol,
            'current': quote,
            'current_price': current_price,
            'change_percent': change_pct,
            'volume': volume,
            'turnover': turnover,
            'high': quote['high'],
            'low': quote['low'],
            'open': quote['open'],
            'prev_close': prev_close,
            'amplitude': float(r['振幅']) if r['振幅'] != '-' else 0,
            'pe_ratio': float(r['市盈率-动态']) if r['市盈率-动态'] != '-' and r['市盈率-动态'] != '亏损' else None,
            'pb_ratio': float(r['市净率']) if r['市净率'] != '-' else None,
            'market_cap': float(r['总市值']) if r['总市值'] != '-' else None,
            'float_market_cap': float(r['流通市值']) if r['流通市值'] != '-' else None,
        }
        
        print(json.dumps(result, ensure_ascii=False))
        
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
