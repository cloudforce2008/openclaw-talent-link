# -*- coding: utf-8 -*-
"""
Data Fetcher - 统一数据获取层
支持港股(Yahoo Finance)和A股(Tushare实时行情)
"""

import subprocess
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict

# Tushare - lazy import避免apport_hook干扰
TUSHARE_AVAILABLE = None
BAOSTOCK_AVAILABLE = None


class DataFetcher:
    """统一数据获取器"""
    
    def __init__(self):
        self.yahoo_script = "/root/.openclaw/workspace/skills/yahoo-finance/scripts/query.mjs"
    
    def fetch(self, symbol: str, market: str = "港股") -> dict:
        """
        获取股票完整数据
        
        Args:
            symbol: 股票代码
                - 港股: 如 "2513.HK"
                - A股: 如 "000001" (6位数字)
            market: "港股" 或 "A股"
            
        Returns:
            统一格式的市场数据字典（兼容workspace格式）
        """
        if market == "A股":
            return self._fetch_a_share(symbol)
        else:
            return self._fetch_hk_share(symbol)
    
    def _fetch_hk_share(self, symbol: str) -> dict:
        """获取港股数据 (Yahoo Finance)"""
        try:
            quote = self._fetch_yahoo_quote(symbol)
            if not quote:
                return {}
            
            history = self._fetch_yahoo_history(symbol, days=20)
            avg_volume = sum(h.get('volume', 0) for h in history) / len(history) if history else 0
            
            return {
                'symbol': symbol,
                'date': datetime.now().strftime("%Y-%m-%d"),
                'current': quote,
                'history': history,
                'info': {},
                'current_price': quote.get('price', 0),
                'change_percent': quote.get('change_percent', 0),
                'volume': quote.get('volume', 0),
                'turnover': 0,
                'high': quote.get('high', 0),
                'low': quote.get('low', 0),
                'open': quote.get('open', 0),
                'prev_close': quote.get('prev_close', 0),
                'avg_volume': avg_volume,
            }
        except Exception as e:
            print(f"港股数据获取失败 {symbol}: {e}")
            return {}
    
    def _fetch_a_share(self, symbol: str) -> dict:
        """获取A股数据 - Tushare子进程调用（绕过apport）+ Yahoo备用"""
        # 优先通过子进程调用Tushare（隔离apport问题）
        result = self._fetch_a_share_tushare_subprocess(symbol)
        if result:
            return result
        
        # Yahoo备用
        print(f"A股 Tushare子进程失败，使用Yahoo备用: {symbol}")
        return self._fetch_a_share_yahoo(symbol)
    
    def _fetch_a_share_tushare_subprocess(self, symbol: str) -> dict:
        """通过子进程调用Tushare获取A股实时行情"""
        try:
            script = Path(__file__).parent / "tushare_fetcher.py"
            result = subprocess.run(
                ['/usr/bin/python3', str(script), symbol],
                capture_output=True, text=True, timeout=30
            )
            
            if result.returncode != 0:
                return None
            
            import json
            data = json.loads(result.stdout.strip())
            
            if 'error' in data:
                return None
            
            # 转换为标准格式
            return {
                'symbol': data['symbol'],
                'date': data.get('update_time', '')[:10],
                'current': {
                    'price': data['current_price'],
                    'change_percent': data['change_percent'],
                    'open': data['open'],
                    'high': data['high'],
                    'low': data['low'],
                    'prev_close': data['prev_close'],
                    'volume': data['volume'],
                    'amount': data['amount'],
                },
                'history': [],
                'info': {},
                'current_price': data['current_price'],
                'change_percent': data['change_percent'],
                'volume': data['volume'],
                'amount': data['amount'],
                'high': data['high'],
                'low': data['low'],
                'open': data['open'],
                'prev_close': data['prev_close'],
                'source': 'tushare',
            }
        except Exception as e:
            print(f"Tushare子进程失败 {symbol}: {e}")
            return None
    
    def _fetch_a_share_yahoo(self, symbol: str) -> dict:
        """A股Yahoo Finance备用方案"""
        try:
            if symbol.startswith('6'):
                yahoo_sym = f"{symbol}.SS"
            else:
                yahoo_sym = f"{symbol}.SZ"
            return self._fetch_hk_share(yahoo_sym)
        except Exception as e:
            print(f"A股Yahoo备用失败 {symbol}: {e}")
            return {}
    
    def _fetch_a_share_backup(self, symbol: str) -> dict:
        """A股备用方案 - Yahoo Finance"""
        try:
            if symbol.startswith('6'):
                yahoo_sym = f"{symbol}.SS"
            else:
                yahoo_sym = f"{symbol}.SZ"
            return self._fetch_hk_share(yahoo_sym)
        except Exception as e:
            print(f"A股备用方案失败 {symbol}: {e}")
            return {}
    
    def _fetch_yahoo_quote(self, symbol: str) -> dict:
        """获取Yahoo Finance实时报价"""
        try:
            result = subprocess.run(
                ['node', self.yahoo_script, 'quote', symbol],
                capture_output=True, text=True, timeout=30
            )
            
            if result.returncode != 0:
                return {}
            
            quote = {}
            for line in result.stdout.strip().split('\n'):
                if '当前价格:' in line:
                    quote['price'] = self._extract_number(line)
                elif '涨跌幅:' in line:
                    quote['change_percent'] = self._extract_number(line)
                elif '前收盘:' in line:
                    quote['prev_close'] = self._extract_number(line)
                elif '开盘价:' in line:
                    quote['open'] = self._extract_number(line)
                elif '最高价:' in line:
                    quote['high'] = self._extract_number(line)
                elif '最低价:' in line:
                    quote['low'] = self._extract_number(line)
                elif '成交量:' in line:
                    quote['volume'] = self._extract_number(line)
            
            return quote
            
        except Exception as e:
            print(f"Yahoo报价失败 {symbol}: {e}")
            return {}
    
    def _fetch_yahoo_history(self, symbol: str, days: int = 20) -> list:
        """获取Yahoo Finance历史数据"""
        try:
            result = subprocess.run(
                ['node', self.yahoo_script, 'history', symbol, str(days)],
                capture_output=True, text=True, timeout=30
            )
            
            if result.returncode != 0:
                return []
            
            history = []
            for line in result.stdout.strip().split('\n'):
                parts = line.split(',')
                if len(parts) >= 6 and parts[0].startswith('20'):
                    history.append({
                        'date': parts[0],
                        'open': float(parts[1]) if parts[1] else 0,
                        'high': float(parts[2]) if parts[2] else 0,
                        'low': float(parts[3]) if parts[3] else 0,
                        'close': float(parts[4]) if parts[4] else 0,
                        'volume': float(parts[5]) if parts[5] else 0,
                    })
            return history
        except Exception as e:
            print(f"Yahoo历史失败 {symbol}: {e}")
            return []
    
    def _extract_number(self, text: str) -> float:
        """从文本中提取数字"""
        import re
        numbers = re.findall(r'-?[\d,]+\.?\d*', text.replace(',', ''))
        if numbers:
            try:
                return float(numbers[0])
            except:
                return 0
        return 0


if __name__ == "__main__":
    fetcher = DataFetcher()
    
    print("=== 测试港股 (2513.HK) ===")
    data = fetcher.fetch("2513.HK", "港股")
    print(f"价格: {data.get('current_price')} | 涨跌: {data.get('change_percent'):+.2f}%")
    
    print("\n=== 测试A股 (000001) ===")
    data = fetcher.fetch("000001", "A股")
    if data:
        print(f"价格: {data.get('current_price')} | 涨跌: {data.get('change_percent'):+.2f}%")
    else:
        print("A股需要安装akshare: pip install akshare")
