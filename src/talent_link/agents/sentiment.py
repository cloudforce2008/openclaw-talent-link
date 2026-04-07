# -*- coding: utf-8 -*-
"""
Sentiment Agent - 情绪分析师
负责：新闻舆情、市场情绪，资金流向、产业链数据
"""

import subprocess
import json
from typing import Dict, List
import sys
from pathlib import Path


class SentimentAgent:
    """情绪分析师 Agent"""
    
    def __init__(self):
        self.name = "Sentiment Analyst"
        self.openrouter_signals = None
    
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
        
        # 获取产业链数据
        industry_signals = self._fetch_industry_signals(symbol)
        
        # 获取全球市场信号
        global_signals = self._fetch_global_signals()
        
        # 整合信心度
        confidence = self._calculate_confidence(
            sentiment['confidence'], 
            industry_signals.get('confidence', 0.5)
        )
        
        return {
            'agent': self.name,
            'news_sentiment': news_sentiment,
            'market_sentiment': sentiment['market'],
            'retail_fomo': sentiment['fomo'],
            'volume_signal': sentiment['volume_signal'],
            'key_events': sentiment['events'],
            'industry_signals': industry_signals,
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
        elif change > 5:
            result['market'] = 'bullish'
            result['fomo'] = 'moderate'
        elif change < -10:
            result['market'] = 'extremely_bearish'
            result['events'].append('strong_decline')
        elif change < -5:
            result['market'] = 'bearish'
        
        if avg_volume > 0:
            volume_ratio = volume / avg_volume
            if volume_ratio > 2:
                result['volume_signal'] = 'massive_spike'
                result['events'].append('volume_surge')
                result['confidence'] += 0.2
            elif volume_ratio > 1.5:
                result['volume_signal'] = 'above_average'
        
        if change > 10:
            result['analysis'] = f'暴涨{change:.1f}%，市场情绪极度乐观，注意追高风险'
        elif change < -10:
            result['analysis'] = f'暴跌{change:.1f}%，恐慌情绪蔓延，关注反弹机会'
        elif change < -5:
            result['analysis'] = f'下跌{abs(change):.1f}%，市场情绪偏空'
        else:
            result['analysis'] = f'波动{change:+.1f}%，市场情绪平稳'
        
        return result
    
    def _fetch_news_sentiment(self, symbol: str) -> str:
        """获取新闻情绪（简化版）"""
        if '2513' in symbol:
            return 'positive'
        elif '0100' in symbol:
            return 'neutral'
        return 'neutral'
    
    def _fetch_industry_signals(self, symbol: str) -> dict:
        """获取产业链信号（OpenRouter周榜真实调用量数据）"""
        try:
            if '2513' not in symbol and '0100' not in symbol:
                return {'relevant': False, 'confidence': 0.5}
            
            stock_mapping = {
                '2513': 'z-ai',
                '0100': 'minimax',
            }
            
            company_key = None
            company_name_cn = None
            for code, v_key in stock_mapping.items():
                if code in symbol:
                    company_key = v_key
                    company_name_cn = {'z-ai': '智谱AI', 'minimax': 'MiniMax'}.get(v_key, code)
                    break
            
            if not company_key:
                return {'relevant': False, 'confidence': 0.5}
            
            # 尝试从缓存文件读取
            cache_file = Path(__file__).parent.parent / "data" / "openrouter_signals.json"
            signals_data = None
            if cache_file.exists():
                try:
                    with open(cache_file) as f:
                        signals_data = json.load(f)
                except:
                    pass
            
            if not signals_data:
                return {'relevant': False, 'confidence': 0.3, 'error': '无法获取OpenRouter数据'}
            
            leaderboard = signals_data.get('global_leaderboard', [])
            insights = signals_data.get('insights', [])
            
            vendor_lines = []
            our_vendor_data = None
            for v in leaderboard:
                vendor_cn = v.get('vendor_cn', v.get('vendor', ''))
                tokens_t = v.get('total_tokens_t', 0)
                top_rank = v.get('top_rank', 'N/A')
                is_chinese = v.get('is_chinese', False)
                flag = '🇨🇳' if is_chinese else ''
                vendor_lines.append(f"{flag}{vendor_cn}: {tokens_t:.2f}T tokens (最高第{top_rank}名)")
                
                if v.get('vendor', '').lower() == company_key:
                    our_vendor_data = v
            
            if our_vendor_data:
                momentum = 'positive' if our_vendor_data.get('total_tokens_t', 0) > 1 else 'neutral'
            else:
                momentum = 'neutral'
            
            return {
                'relevant': True,
                'company': company_name_cn,
                'vendor_key': company_key,
                'industry_momentum': momentum,
                'global_leaderboard': leaderboard,
                'vendor_summary': vendor_lines,
                'insights': insights,
                'our_vendor': our_vendor_data,
                'confidence': 0.7,
                'fetch_time': signals_data.get('fetch_time', 'unknown'),
            }
            
        except Exception as e:
            print(f"Error fetching industry signals: {e}")
            return {'relevant': False, 'error': str(e), 'confidence': 0.3}
    
    def _calculate_confidence(self, market_conf: float, industry_conf: float) -> float:
        """整合市场情绪和产业链数据的信心度"""
        combined = market_conf * 0.6 + industry_conf * 0.4
        return round(min(combined, 1.0), 2)
    
    def _fetch_global_signals(self) -> dict:
        """获取全球市场信号（美股/大宗/地缘）- 简化版备用"""
        try:
            # 尝试使用global_market_fetcher
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from talent_link.skills.global_market_fetcher import get_full_global_signals
            return get_full_global_signals()
        except Exception as e:
            print(f"Global signals fallback: {e}")
            return {'signals': [], 'error': str(e)}
