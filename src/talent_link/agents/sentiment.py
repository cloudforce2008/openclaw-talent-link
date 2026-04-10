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

        # 获取新闻情绪（结构化：标题+摘要+Highlights）
        news_data = self._fetch_news_sentiment(symbol)

        # 获取全球市场信号（复用 workspace 成熟模块）
        global_signals = self._fetch_global_signals()

        # 整合：新闻情绪 × 市场情绪
        news_sent_str = news_data.get('sentiment', 'neutral')
        confidence = sentiment['confidence']

        return {
            'agent': self.name,
            'news_sentiment': news_sent_str,
            'news': news_data.get('news', []),
            'news_highlights': news_data.get('highlights', []),
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

    def _fetch_news_sentiment(self, symbol: str) -> dict:
        """
        获取近期新闻：标题 + 投资相关摘要
        返回结构化 dict 而非纯字符串
        """
        # 股票 → 中文公司名/关键词
        name_map = {
            '2513': ('智谱AI', 'zhipuai OR 智谱'),
            '0100': ('MiniMax', 'minimax AI'),
            '0700': ('腾讯', '腾讯'),
            '9988': ('阿里巴巴', '阿里巴巴'),
            '3690': ('美团', '美团'),
            '1810': ('小米', '小米'),
        }

        company_key = None
        for prefix, (cn_name, search_key) in name_map.items():
            if prefix in symbol:
                company_key = cn_name
                search_term = search_key
                break

        if not company_key:
            return {'sentiment': 'neutral', 'news': [], 'highlights': []}

        try:
            news = self._search_google_news(search_term, max_results=5)
            sentiment = self._sentiment_from_headlines(news)
            return {
                'sentiment': sentiment,
                'news': news,
                'highlights': self._extract_investment_highlights(news, company_key),
            }
        except Exception as e:
            print(f"[Sentiment] news fetch failed: {e}")
            return {'sentiment': 'neutral', 'news': [], 'highlights': []}

    def _search_google_news(self, query: str, max_results: int = 5) -> list:
        """通过 Google News RSS 获取近期新闻标题"""
        import urllib.request, urllib.parse, re, time
        encoded = urllib.parse.quote(query)
        url = f"https://news.google.com/rss/search?q={encoded}&hl=zh-CN&gl=CN&ceid=CN:zh-Hans"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        resp = urllib.request.urlopen(req, timeout=10)
        xml = resp.read().decode("utf-8", errors="ignore")

        titles = []
        seen = set()
        for m in re.finditer(r"<title>([^<]+)</title>", xml):
            title = m.group(1).strip()
            # 去重 + 去除 "... - Google 新闻"
            clean = re.sub(r'\s*-\s*Google\s*新闻\s*$', '', title).strip()
            if clean and clean not in seen and len(clean) > 5:
                seen.add(clean)
                titles.append(clean)
                if len(titles) >= max_results:
                    break
        time.sleep(0.3)  # 礼貌爬虫
        return titles

    def _sentiment_from_headlines(self, headlines: list) -> str:
        """根据新闻标题判断情绪"""
        if not headlines:
            return 'neutral'
        positive = ['涨', '突破', '创新高', '增持', '买入', '超预期', '增长', '合作', '领涨', '利好', '上调']
        negative = ['跌', '亏损', '减持', '卖出', '不及预期', '风险', '诉讼', '调查', '暴雷', '预警', '下调', '利空']
        pos_count = sum(1 for h in headlines for kw in positive if kw in h)
        neg_count = sum(1 for h in headlines for kw in negative if kw in h)
        if pos_count > neg_count and pos_count > 1:
            return 'bullish'
        elif neg_count > pos_count and neg_count > 1:
            return 'bearish'
        return 'neutral'

    def _extract_investment_highlights(self, headlines: list, company: str) -> list:
        """
        从新闻标题中提炼对投资有参考价值的摘要
        返回格式：[('事件类型', '简要描述'), ...]
        """
        highlights = []
        for title in headlines:
            # 评级/目标价变动
            if any(kw in title for kw in ['评级', '目标价', '买入', '增持', '卖出', '下调', '上调']):
                highlights.append(('📊 评级动态', title))
            # 业绩/营收
            elif any(kw in title for kw in ['财报', '业绩', '营收', '收入', '盈利', '亏损', '超预期']):
                highlights.append(('💰 业绩相关', title))
            # 融资/上市
            elif any(kw in title for kw in ['IPO', '上市', '融资', '配股', '增发']):
                highlights.append(('💵 融资动态', title))
            # 产品/技术
            elif any(kw in title for kw in ['发布', '产品', '模型', '技术', '合作', '落地']):
                highlights.append(('🚀 产品进展', title))
            # 政策/监管
            elif any(kw in title for kw in ['监管', '政策', '审查', '禁止', '牌照']):
                highlights.append(('⚖️ 政策监管', title))
            # 竞争/市场份额
            elif any(kw in title for kw in ['竞争', '份额', '市场', '对手', '领先']):
                highlights.append(('🏆 竞争格局', title))

        # 去重，保留前5条最有价值的
        seen = set()
        deduped = []
        for h in highlights:
            if h[1] not in seen:
                seen.add(h[1])
                deduped.append(h)
        return deduped[:5]

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
