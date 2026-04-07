"""
Fundamental Agent - 基本面分析师
负责：财务数据、估值分析、行业对比
"""

from typing import Dict


class FundamentalAgent:
    """基本面分析师 Agent"""
    
    def __init__(self):
        self.name = "Fundamental Analyst"
    
    def analyze(self, market_data: dict) -> dict:
        """
        基本面分析
        
        由于港股财务数据获取限制，主要基于公开信息进行分析
        """
        symbol = market_data.get('symbol', '')
        info = market_data.get('info', {})
        
        # 提取基本面信息
        market_cap = info.get('market_cap', 0)
        pe_ratio = info.get('pe_ratio')
        pb_ratio = info.get('pb_ratio')
        
        # 智谱和 MiniMax 是新股，使用已知信息
        if '2513' in symbol:  # 智谱
            return self._analyze_zhigu(market_cap)
        elif '0100' in symbol or '00100' in symbol:  # MiniMax
            return self._analyze_minimax(market_cap)
        else:
            return self._generic_analysis(market_cap, pe_ratio, pb_ratio)
    
    def _analyze_zhigu(self, market_cap: float) -> dict:
        """智谱基本面分析"""
        return {
            'agent': self.name,
            'company': '智谱AI',
            'sector': 'AI大模型',
            'market_cap_hkd': market_cap,
            'revenue_growth': 158.95,  # 已知数据
            'profit_margin': -23.6,    # 亏损
            'cash_position': 'strong',  # IPO筹资
            'valuation': 'expensive',   # 高估值
            'industry_rank': 1,         # 港股AI第一股
            'moat': 'strong',           # 清华背景、技术领先
            'confidence': 0.65,
            'key_factors': [
                '全球大模型第一股，稀缺性溢价',
                '2025年收入增长158.95%，高增长',
                '但仍处亏损状态，盈利能力待验证',
                '市值一度突破4000亿港元，估值偏高'
            ],
            'analysis': '智谱作为港股AI龙头，享有稀缺性溢价。收入高增长但亏损扩大，适合高风险偏好投资者。'
        }
    
    def _analyze_minimax(self, market_cap: float) -> dict:
        """MiniMax 基本面分析"""
        return {
            'agent': self.name,
            'company': 'MiniMax',
            'sector': 'AI大模型',
            'market_cap_hkd': market_cap,
            'revenue_growth': 158.95,  # 已知数据
            'profit_margin': -2365,    # 巨额亏损
            'cash_position': 'strong',  # IPO筹资
            'valuation': 'expensive',
            'industry_rank': 2,         # 次于智谱
            'moat': 'moderate',
            'confidence': 0.60,
            'key_factors': [
                '收入增长158%，但亏损同比扩大302%',
                '汇丰目标价1000港元，当前接近目标',
                '烧钱速度快于收入增长，盈利模式待验证',
                '超额配股权行使，筹资6.97亿港元'
            ],
            'analysis': 'MiniMax高速增长但亏损严重，盈利路径不如智谱清晰。估值依赖未来业绩兑现。'
        }
    
    def _generic_analysis(self, market_cap: float, pe: float, pb: float) -> dict:
        """通用基本面分析"""
        valuation = 'fair'
        if pe and pe > 50:
            valuation = 'expensive'
        elif pe and pe < 15:
            valuation = 'cheap'
        
        return {
            'agent': self.name,
            'market_cap_hkd': market_cap,
            'pe_ratio': pe,
            'pb_ratio': pb,
            'valuation': valuation,
            'confidence': 0.50,
            'analysis': '基于有限数据的基础分析。'
        }
