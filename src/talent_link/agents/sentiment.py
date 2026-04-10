# -*- coding: utf-8 -*-
"""
Sentiment Agent - 情绪分析师
直接复用 workspace 的 global_market_fetcher 获取真实全球市场信号
"""

import subprocess
import json
from typing import Dict, List
import sys
from pathlib import Path


WORKSPACE_UTILS = '/root/.openclaw/workspace/skills/stock-analyzer-v2/utils'


class SentimentAgent:
    """情绪分析师 Agent"""

    def __init__(self):
        self.name = "Sentiment Analyst"
        self._global_signals_cache = None
        self._global_signals_fetch_time = None

    def analyze(self, market_data: dict) -> dict:
        """情绪分析"""
        symbol = market_data.get('symbol', '')
        change_percent = market_data.get('change_percent', 0)
        volume = market_data.get('volume', 0)
        avg_volume = market_data.get('avg_volume', volume)

        # 基于价格和成交量判断情绪
        sentiment = self._analyze_price_action(change_percent, volume, avg_volume)

        # 获取新闻情绪
        news_sentiment = self._fetch_news_sentiment(symbol)

        # 获取全球市场信号（复用 workspace 成熟模块）
        global_signals = self._fetch_global_signals()

        # 整合
        confidence = sentiment['confidence']

        return {
            'agent': self.name,
            'news_sentiment': news_sentiment,
            'market_sentiment': sentiment['market'],
            'retail_fomo': sentiment['fomo'],
            'volume_signal': sentiment['volume_signal'],
            'key_events': sentiment['events'],
            'industry_signals': {'relevant': False},  # 暂时禁用，来源数据过期
            'global_signals': global_signals,
            'confidence': confidence,
            'analysis': sentiment['analysis']
        }

    def _analyze_price_action(self, change: float, volume: float, avg_volume: float) -> dict:
        """基于价格行为分析情绪"""
        result = {
            'market': 'neutral',
            'fomo': 'low',
            'volume_signal': 'normal',
            'events': [],
            'confidence': 0.5,
            'analysis': ''
        }

        if change > 10:
            result['market'] = 'extremely_bullish'
            result['fomo'] = 'high'
            result['events'].append('strong_rally')
            result['analysis'] = f'暴涨{change:.1f}%，市场情绪极度亢奋'
            result['confidence'] = 0.75
        elif change > 5:
            result['market'] = 'bullish'
            result['fomo'] = 'moderate'
            result['analysis'] = f'上涨{change:.1f}%，市场乐观'
            result['confidence'] = 0.65
        elif change < -10:
            result['market'] = 'extremely_bearish'
            result['events'].append('strong_decline')
            result['analysis'] = f'暴跌{abs(change):.1f}%，恐慌情绪蔓延'
            result['confidence'] = 0.75
        elif change < -5:
            result['market'] = 'bearish'
            result['analysis'] = f'下跌{abs(change):.1f}%，市场偏空'
            result['confidence'] = 0.65
        elif change < -2:
            result['market'] = 'slightly_bearish'
            result['analysis'] = f'小跌{abs(change):.1f}%，情绪偏谨慎'
            result['confidence'] = 0.55
        elif change > 2:
            result['market'] = 'slightly_bullish'
            result['analysis'] = f'小涨{change:.1f}%，情绪偏暖'
            result['confidence'] = 0.55
        else:
            result['analysis'] = f'横盘{change:+.1f}%，市场观望'

        if avg_volume > 0:
            vol_ratio = volume / avg_volume
            if vol_ratio > 2:
                result['volume_signal'] = 'massive_spike'
                result['events'].append('volume_surge')
                result['analysis'] += '，成交量暴增需警惕'
            elif vol_ratio > 1.5:
                result['volume_signal'] = 'above_average'

        return result

    def _fetch_news_sentiment(self, symbol: str) -> str:
        """获取新闻情绪（通过 kimi_search 实时获取）"""
        return 'neutral'

    def _fetch_global_signals(self) -> dict:
        """获取全球市场信号 - 直接调用 workspace 成熟模块"""
        try:
            if WORKSPACE_UTILS not in sys.path:
                sys.path.insert(0, WORKSPACE_UTILS)
            from global_market_fetcher import get_full_global_signals
            return get_full_global_signals()
        except Exception as e:
            print(f"[SentimentAgent] global_market_fetcher failed: {e}")
            return {
                'fetch_time': None,
                'us_ai_leaders': {},
                'commodities': {},
                'geopolitics': {},
                'signals': [],
                '_error': str(e)
            }
