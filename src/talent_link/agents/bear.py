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
        current_price = technical.get('current_price', 0)
        support = technical.get('support_levels', [])
        resistance = technical.get('resistance_levels', [])
        trend = technical.get('trend', 'unknown')
        
        # 技术面分析
        tech_analysis = []
        if 'overbought_pullback' in technical.get('signals', []):
            tech_analysis.append('RSI>70超买区，MACD顶背离，短期回调风险>60%')
        if technical.get('bollinger') == 'above_upper':
            tech_analysis.append(f'股价突破布林带上轨({resistance[0] if resistance else "N/A"}港元)，乖离率过大，回调概率高')
        if trend in ['downward', 'strong_downward']:
            tech_analysis.append(f'均线空头排列，{trend}趋势，抛压持续')
        if technical.get('volume_signal') == 'volume_declining':
            tech_analysis.append('成交量萎缩至均线以下，上涨动力不足')
        
        if tech_analysis:
            lines.append(f'【技术面】{"；".join(tech_analysis[:2])}')
        
        # 基本面分析
        fund_analysis = []
        margin = fundamental.get('profit_margin', 0)
        if margin < -20:
            fund_analysis.append(f'净亏损率{margin:.1f}%，亏损持续扩大，现金流消耗速度快')
        elif margin < 0:
            fund_analysis.append(f'净利润率{margin:.1f}%，盈利模式尚未验证')
        
        valuation = fundamental.get('valuation', 'fair')
        if valuation == 'expensive':
            pe = fundamental.get('pe_ratio', 'N/A')
            fund_analysis.append(f'估值偏高(PE={pe}倍)，需持续高增长才能支撑当前股价')
        elif valuation == 'very_expensive':
            fund_analysis.append('估值泡沫化，远超行业平均，回调风险极高')
        
        competition = fundamental.get('competition_risk', 'medium')
        if competition == 'high':
            fund_analysis.append('竞争风险高：多家巨头入局，价格战可能压缩利润空间')
        
        if fund_analysis:
            lines.append(f'【基本面】{"；".join(fund_analysis[:2])}')
        
        # 情绪面分析
        sent_analysis = []
        if sentiment.get('market_sentiment') == 'extremely_bullish':
            sent_analysis.append('情绪极度乐观，看涨共识过高，一旦不及预期将引发踩踏')
        if sentiment.get('fomo') == 'high':
            sent_analysis.append('散户FOMO入场为主，机构却在悄然撤退，警惕顶部形成')
        if sentiment.get('news_sentiment') == 'negative':
            sent_analysis.append('近期负面新闻发酵，市场信心受挫')
        
        if sent_analysis:
            lines.append(f'【情绪面】{"；".join(sent_analysis[:1])}')
        
        # 外部风险
        external = []
        us_corr = sentiment.get('us_nasdaq_correlation', 0)
        if us_corr > 0.7:
            external.append(f'与纳指相关性{us_corr:.0%}，美股波动将直接传导')
        if sentiment.get('global_signals', {}).get('geopolitics') == 'high_risk':
            external.append('中东地缘风险升温，风险资产承压')
        
        if external:
            lines.append(f'【外部风险】{"；".join(external[:1])}')
        
        # 综合结论
        if not lines:
            lines.append(f'【综合】当前价格已充分反映乐观预期，下行风险大于上行空间')
        
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
        """识别潜在利空催化剂"""
        catalysts = []
        
        catalysts.extend([
            '业绩不及预期',
            '行业监管政策变化',
            '大股东减持'
        ])
        
        if fundamental.get('profit_margin', 0) < -20:
            catalysts.append('亏损扩大担忧')
        
        return catalysts[:3]
    
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
        """计算看空信心度"""
        confidence = 0.5
        
        # 技术面加分
        if technical.get('trend') in ['downward', 'strong_downward']:
            confidence += 0.15
        if 'overbought_pullback' in technical.get('signals', []):
            confidence += 0.1
        
        # 基本面加分
        if fundamental.get('profit_margin', 0) < -20:
            confidence += 0.1
        if fundamental.get('valuation') == 'expensive':
            confidence += 0.1
        
        # 情绪面加分
        if sentiment.get('market_sentiment') in ['extremely_bullish']:
            confidence += 0.15  # 极端乐观时看空 contrarian
        
        return min(confidence, 0.9)
    
    def _extract_key_points(self, technical: dict, fundamental: dict, sentiment: dict) -> list:
        """提取关键论点"""
        return [
            f"技术面: {technical.get('analysis', 'N/A')[:50]}...",
            f"基本面: {fundamental.get('analysis', 'N/A')[:50]}...",
            f"风险因素: {', '.join(self._identify_catalysts(fundamental, sentiment)[:2])}"
        ]
