"""
Bull Agent - 看多研究员
负责：收集看多论据，提出上涨逻辑
"""

from typing import Dict


class BullAgent:
    """看多研究员 Agent"""
    
    def __init__(self):
        self.name = "Bull Researcher"
    
    def debate(self, analysis_input: dict) -> dict:
        """
        基于分析师观点生成看多论据
        
        Args:
            analysis_input: 包含技术/基本面/情绪分析结果
        """
        technical = analysis_input.get('technical', {})
        fundamental = analysis_input.get('fundamental', {})
        sentiment = analysis_input.get('sentiment', {})
        market_data = analysis_input.get('market_data', {})
        
        current_price = market_data.get('current_price', 0)
        
        # 生成看多论点
        thesis = self._generate_thesis(technical, fundamental, sentiment)
        target = self._calculate_target(current_price, technical)
        catalysts = self._identify_catalysts(fundamental, sentiment)
        risks = self._identify_risks(technical, fundamental)
        
        return {
            'agent': self.name,
            'stance': 'bullish',
            'thesis': thesis,
            'target_price': target,
            'current_price': current_price,
            'upside_potential': round((target - current_price) / current_price * 100, 1) if current_price > 0 else 0,
            'catalysts': catalysts,
            'risks': risks,
            'confidence': self._calculate_confidence(technical, fundamental, sentiment),
            'key_points': self._extract_key_points(technical, fundamental, sentiment)
        }
    
    def _generate_thesis(self, technical: dict, fundamental: dict, sentiment: dict) -> str:
        """生成看多核心逻辑（详细分析）"""
        lines = []
        current_price = technical.get('current_price', 0)
        support = technical.get('support_levels', [])
        resistance = technical.get('resistance_levels', [])
        trend = technical.get('trend', 'unknown')
        
        # 技术面分析
        tech_analysis = []
        if 'oversold_bounce' in technical.get('signals', []):
            tech_analysis.append('RSI<30超卖区，MACD底背离，短期反弹概率>70%')
        if technical.get('bollinger') == 'below_lower':
            tech_analysis.append(f'股价触及布林带下轨({support[0] if support else "N/A"}港元)，历史上此处反弹概率较高')
        if trend in ['upward', 'strong_upward']:
            tech_analysis.append(f'均线多头排列，{trend}趋势， momentum 持续增强')
        if technical.get('volume_signal') == 'volume_surge':
            tech_analysis.append('成交量放大2倍以上，资金入场明显')
        
        if tech_analysis:
            lines.append(f'【技术面】{"；".join(tech_analysis[:2])}')
        
        # 基本面分析
        fund_analysis = []
        growth = fundamental.get('revenue_growth', 0)
        if growth > 50:
            fund_analysis.append(f'收入同比增长{growth:.0f}%，远超行业平均水平，说明产品市场契合度高')
        margin = fundamental.get('profit_margin', 0)
        if margin > 0:
            fund_analysis.append(f'净利润率{margin:.1f}%，已实现盈利，财务状况健康')
        elif growth > 100:
            fund_analysis.append(f'虽未盈利但收入增速{growth:.0f}%，规模效应下盈亏平衡可期')
        moat = fundamental.get('moat', '')
        if moat == 'strong':
            fund_analysis.append('护城河评级：强，竞争对手难以复制其核心优势')
        elif moat == 'medium':
            fund_analysis.append('护城河评级：中，具备一定的差异化竞争力')
        
        if fund_analysis:
            lines.append(f'【基本面】{"；".join(fund_analysis[:2])}')
        
        # 情绪面分析
        sent_analysis = []
        if sentiment.get('news_sentiment') == 'positive':
            sent_analysis.append('近期正面新闻密集，市场关注度高')
        if sentiment.get('market_sentiment') in ['bearish', 'extremely_bearish']:
            sent_analysis.append('反向指标：机构情绪极端悲观，往往是底部信号（巴菲特指标）')
        short_int = sentiment.get('shortInterest', 0)
        if short_int > 20:
            sent_analysis.append(f'空头兴趣{short_int}%，空头回补可能推动股价上涨')
        
        if sent_analysis:
            lines.append(f'【情绪面】{"；".join(sent_analysis[:1])}')
        
        # 综合结论
        if not lines:
            lines.append(f'【综合】当前估值具吸引力，下行空间有限，上行弹性充足')
        
        return '\n'.join(lines[:3])
    
    def _calculate_target(self, current: float, technical: dict) -> float:
        """计算目标价"""
        if current <= 0:
            return 0
        
        # 基于阻力位设定目标
        resistance = technical.get('resistance_levels', [])
        if resistance:
            # 取第一个阻力位或高于当前价15%
            target = max(resistance[0], current * 1.15)
        else:
            target = current * 1.15
        
        return round(target, 2)
    
    def _identify_catalysts(self, fundamental: dict, sentiment: dict) -> list:
        """识别潜在催化剂"""
        catalysts = []
        
        if fundamental.get('sector') == 'AI大模型':
            catalysts.extend([
                'AI应用落地加速',
                '新模型发布',
                '大模型商业化进展'
            ])
        
        if sentiment.get('news_sentiment') == 'positive':
            catalysts.append('近期利好消息')
        
        return catalysts[:3]
    
    def _identify_risks(self, technical: dict, fundamental: dict) -> list:
        """识别潜在风险（看多方的风险意识）"""
        risks = []
        
        if technical.get('trend') == 'strong_downward':
            risks.append('下跌趋势中，反弹可能失败')
        
        margin = fundamental.get('profit_margin', 0)
        if margin < 0:
            risks.append(f'亏损状态({margin:.1f}%)，盈利时间不确定')
        
        if fundamental.get('valuation') == 'expensive':
            risks.append('估值偏高，需业绩持续验证')
        
        return risks[:3]
    
    def _calculate_confidence(self, technical: dict, fundamental: dict, sentiment: dict) -> float:
        """计算看多信心度"""
        confidence = 0.5
        
        # 技术面加分
        if technical.get('trend') in ['upward', 'strong_upward']:
            confidence += 0.15
        if 'oversold_bounce' in technical.get('signals', []):
            confidence += 0.1
        
        # 基本面加分
        if fundamental.get('revenue_growth', 0) > 50:
            confidence += 0.1
        if fundamental.get('moat') == 'strong':
            confidence += 0.1
        
        # 情绪面加分（反向）
        if sentiment.get('market_sentiment') in ['bearish', 'extremely_bearish']:
            confidence += 0.1  # 极端看空时看多 contrarian
        
        return min(confidence, 0.9)
    
    def _extract_key_points(self, technical: dict, fundamental: dict, sentiment: dict) -> list:
        """提取关键论点"""
        return [
            f"技术面: {technical.get('analysis', 'N/A')[:50]}...",
            f"基本面: {fundamental.get('analysis', 'N/A')[:50]}...",
            f"催化剂: {', '.join(self._identify_catalysts(fundamental, sentiment)[:2])}"
        ]
