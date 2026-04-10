"""
Bear Agent - 看空研究员
负责：收集看空论据，提示下跌风险
"""

from typing import Dict


class BearAgent:
    """看空研究员 Agent"""
    
    def __init__(self):
        self.name = "Bear Researcher"
    
    def debate(self, analysis_input: dict) -> dict:
        """
        基于分析师观点生成看空论据
        
        Args:
            analysis_input: 包含技术/基本面/情绪分析结果
        """
        technical = analysis_input.get('technical', {})
        fundamental = analysis_input.get('fundamental', {})
        sentiment = analysis_input.get('sentiment', {})
        market_data = analysis_input.get('market_data', {})
        
        current_price = market_data.get('current_price', 0)
        
        # 生成看空论点
        thesis = self._generate_thesis(technical, fundamental, sentiment)
        target = self._calculate_target(current_price, technical)
        catalysts = self._identify_catalysts(fundamental, sentiment)
        risks = self._identify_risks(technical, fundamental, sentiment)
        
        return {
            'agent': self.name,
            'stance': 'bearish',
            'thesis': thesis,
            'target_price': target,
            'current_price': current_price,
            'downside_risk': round((current_price - target) / current_price * 100, 1) if current_price > 0 else 0,
            'catalysts': catalysts,
            'risks': risks,
            'confidence': self._calculate_confidence(technical, fundamental, sentiment),
            'key_points': self._extract_key_points(technical, fundamental, sentiment)
        }
    
    def _generate_thesis(self, technical: dict, fundamental: dict, sentiment: dict) -> str:
        """生成看空核心逻辑（详细分析）"""
        lines = []
        trend = technical.get('trend', 'unknown')

        # === 从真实新闻标题中提取看空论据 ===
        news_highlights: list = sentiment.get('news_highlights', []) or []
        bear_news_lines = []
        for tag, title in news_highlights:
            # 负面新闻
            if any(kw in title for kw in ['减持', '卖出', '下调', '亏损', '风险', '调查', '诉讼', '预警', '暴雷', '危机']):
                bear_news_lines.append(f'{tag}：{title[:40]}')
            # 业绩不及预期
            elif any(kw in title for kw in ['不及预期', '低于', '下滑', '减少', '收缩']):
                bear_news_lines.append(f'业绩利空：{title[:40]}')
            # 竞争加剧
            elif any(kw in title for kw in ['竞争', '价格战', '入局', '对手', '围剿']):
                bear_news_lines.append(f'竞争压力：{title[:40]}')
            # 估值过高（知名媒体提示）
            elif any(kw in title for kw in ['高估', '泡沫', '贵', '太贵', '减持']):
                bear_news_lines.append(f'估值警示：{title[:40]}')

        if bear_news_lines:
            lines.append(f'【最新动态警示】{"；".join(bear_news_lines[:2])}')

        # 技术面分析
        tech_analysis = []
        if 'overbought_pullback' in technical.get('signals', []):
            tech_analysis.append('RSI>70超买区，MACD顶背离，回调风险>60%')
        res = technical.get('resistance_levels', [])
        if technical.get('bollinger') == 'above_upper':
            tech_analysis.append(f'股价突破布林带上轨({res[0] if res else "N/A"}元)，乖离率过大')
        if trend in ['downward', 'strong_downward']:
            tech_analysis.append(f'均线空头排列，趋势向下，抛压持续')
        if technical.get('volume_signal') == 'volume_declining':
            tech_analysis.append('成交量萎缩，上涨动力不足')

        if tech_analysis:
            lines.append(f'【技术面】{"；".join(tech_analysis[:2])}')

        # 基本面分析
        fund_analysis = []
        margin = fundamental.get('profit_margin', 0)
        if margin < -20:
            fund_analysis.append(f'净亏损率{margin:.1f}%，亏损持续扩大')
        elif margin < 0:
            fund_analysis.append(f'净利润率{margin:.1f}%，盈利模式尚未验证')

        valuation = fundamental.get('valuation', 'fair')
        if valuation == 'expensive':
            pe = fundamental.get('pe_ratio', 'N/A')
            fund_analysis.append(f'估值偏高(PE={pe}倍)，需持续高增长支撑')
        elif valuation == 'very_expensive':
            fund_analysis.append('估值泡沫化，远超行业平均')

        competition = fundamental.get('competition_risk', 'medium')
        if competition == 'high':
            fund_analysis.append('竞争风险高：多家巨头入局，价格战可能压缩利润')

        if fund_analysis:
            lines.append(f'【基本面】{"；".join(fund_analysis[:2])}')

        # 情绪面
        if sentiment.get('market_sentiment') == 'extremely_bullish':
            lines.append('【情绪面】机构情绪极度乐观，共识过高，一旦不及预期将引发踩踏')
        elif sentiment.get('fomo') == 'high':
            lines.append('【情绪面】散户FOMO为主，机构悄然撤退，警惕顶部形成')
        elif news_highlights and not bear_news_lines:
            # 有新闻但没有明显负面，提示股价可能已反映乐观预期
            lines.append('【情绪面】利好消息密集，股价可能已充分反映，后续需要更多催化')

        if not lines:
            lines.append('【综合】当前价格已充分反映乐观预期，下行风险大于上行空间')

        return '\n'.join(lines[:4])
    
    def _calculate_target(self, current: float, technical: dict) -> float:
        """计算看空目标价"""
        if current <= 0:
            return 0
        
        # 基于支撑位设定目标
        support = technical.get('support_levels', [])
        if support:
            # 取第一个支撑位或低于当前价15%
            target = min(support[0], current * 0.85)
        else:
            target = current * 0.85
        
        return round(target, 2)
    
    def _identify_catalysts(self, fundamental: dict, sentiment: dict) -> list:
        """识别潜在利空催化剂（从真实新闻中提取）"""
        catalysts = []
        news_highlights: list = sentiment.get('news_highlights', []) or []

        # 从真实新闻中提取利空催化剂
        for tag, title in news_highlights:
            if any(kw in title for kw in ['减持', '卖出', '下调', '风险', '亏损', '预警', '诉讼']):
                catalysts.append(f'【警示】{title[:35]}')
            elif any(kw in title for kw in ['不及预期', '下滑', '减少']):
                catalysts.append(f'【业绩】{title[:35]}')
            elif any(kw in title for kw in ['监管', '政策', '审查', '调查', '禁止']):
                catalysts.append(f'【政策】{title[:35]}')

        # 补充结构性利空
        catalysts.extend(['业绩不及预期', '行业监管政策变化', '大股东减持'])

        # 去重
        seen = set()
        deduped = []
        for c in catalysts:
            if c not in seen:
                seen.add(c)
                deduped.append(c)

        return deduped[:4]
    
    def _identify_risks(self, technical: dict, fundamental: dict, sentiment: dict) -> list:
        """识别看空方的风险（即上涨可能性）"""
        risks = []
        
        if technical.get('trend') == 'strong_upward':
            risks.append('强劲上涨趋势中，做空可能被套')
        
        growth = fundamental.get('revenue_growth', 0)
        if growth > 100:
            risks.append(f'高增长({growth:.0f}%)可能继续超预期')
        
        if fundamental.get('moat') == 'strong':
            risks.append('护城河深厚，竞争对手难以撼动')
        
        return risks[:3]
    
    def _calculate_confidence(self, technical: dict, fundamental: dict, sentiment: dict) -> float:
        """计算看空信心度（基于真实新闻）"""
        confidence = 0.4  # 基准稍低

        # 技术面加分
        if technical.get('trend') in ['downward', 'strong_downward']:
            confidence += 0.12
        if 'overbought_pullback' in technical.get('signals', []):
            confidence += 0.08

        # 基本面加分
        if fundamental.get('profit_margin', 0) < -20:
            confidence += 0.08
        if fundamental.get('valuation') == 'expensive':
            confidence += 0.08

        # === 基于真实新闻标题加分 ===
        news_highlights: list = sentiment.get('news_highlights', []) or []
        for tag, title in news_highlights:
            if any(kw in title for kw in ['减持', '卖出', '下调', '风险', '亏损', '调查', '诉讼', '预警', '暴雷']):
                confidence += 0.12  # 实质性利空
                break
        for tag, title in news_highlights:
            if any(kw in title for kw in ['不及预期', '下滑', '低于']):
                confidence += 0.08
                break

        # 情绪极端时逆向看空加分
        if sentiment.get('market_sentiment') == 'extremely_bullish':
            confidence += 0.10
        elif sentiment.get('fomo') == 'high':
            confidence += 0.08

        return min(confidence, 0.95)
    
    def _extract_key_points(self, technical: dict, fundamental: dict, sentiment: dict) -> list:
        """提取关键论点"""
        return [
            f"技术面: {technical.get('analysis', 'N/A')[:50]}...",
            f"基本面: {fundamental.get('analysis', 'N/A')[:50]}...",
            f"风险因素: {', '.join(self._identify_catalysts(fundamental, sentiment)[:2])}"
        ]
