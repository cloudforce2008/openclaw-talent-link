"""
Risk Agent - 风控经理
负责：独立风控审核，仓位和止损检查
"""

from typing import Dict


class RiskAgent:
    """风控经理 Agent"""
    
    def __init__(self):
        self.name = "Risk Manager"
    
    def evaluate(self, signal: dict, market_data: dict) -> dict:
        """
        独立风控审核
        
        Args:
            signal: 交易员生成的信号
            market_data: 市场数据
        """
        current_price = market_data.get('current_price', 0)
        change_percent = market_data.get('change_percent', 0)
        
        # 各项风险评估
        position_risk = self._assess_position_risk(signal)
        stop_loss_risk = self._assess_stop_loss(signal, current_price)
        drawdown_risk = self._assess_drawdown(signal, change_percent)
        volatility_risk = self._assess_volatility(market_data)
        
        # 综合风险评级
        risk_level = self._calculate_risk_level(
            position_risk, stop_loss_risk, drawdown_risk, volatility_risk
        )
        
        # 审批决策
        approval = self._make_decision(signal, risk_level)
        
        return {
            'agent': self.name,
            'approval': approval['status'],
            'risk_level': risk_level,
            'max_position': approval['max_position'],
            'max_drawdown': '15%',
            'stop_loss_valid': stop_loss_risk['valid'],
            'risk_factors': [
                position_risk,
                stop_loss_risk,
                drawdown_risk,
                volatility_risk
            ],
            'conditions': approval['conditions'],
            'rejection_reason': approval.get('rejection_reason', ''),
            'risk_disclosure': self._generate_disclosure(signal, risk_level)
        }
    
    def _assess_position_risk(self, signal: dict) -> dict:
        """评估仓位风险"""
        position = signal.get('position_size', '0%')
        confidence = signal.get('confidence', 0)
        
        # 解析仓位百分比
        try:
            position_pct = float(position.replace('%', ''))
        except:
            position_pct = 0
        
        risk_score = 'low'
        if position_pct > 20:
            risk_score = 'high'
        elif position_pct > 10:
            risk_score = 'medium'
        
        # 信心度不足时降低仓位建议
        if confidence < 0.6 and position_pct > 10:
            risk_score = 'high'
        
        return {
            'category': 'position',
            'score': risk_score,
            'suggested_position': f'{min(position_pct, 20)}%',
            'rationale': f'建议仓位 {position}，信心度 {confidence:.0%}'
        }
    
    def _assess_stop_loss(self, signal: dict, current_price: float) -> dict:
        """评估止损设置"""
        stop_loss = signal.get('stop_loss', 0)
        entry = signal.get('entry_price', current_price)
        
        if entry <= 0:
            return {'category': 'stop_loss', 'valid': False, 'rationale': '无效入场价'}
        
        loss_pct = (entry - stop_loss) / entry
        
        valid = True
        if loss_pct > 0.10:  # 止损超过10%认为太宽
            valid = False
            rationale = f'止损位 {stop_loss} 距离过远（{loss_pct:.1%}），建议收紧至 {entry * 0.93:.0f}'
        elif loss_pct < 0.03:  # 止损小于3%可能太紧
            valid = False
            rationale = f'止损位 {stop_loss} 距离过近（{loss_pct:.1%}），容易被洗出'
        else:
            rationale = f'止损设置合理（{loss_pct:.1%}）'
        
        return {
            'category': 'stop_loss',
            'valid': valid,
            'stop_loss_distance': f'{loss_pct:.1%}',
            'rationale': rationale
        }
    
    def _assess_drawdown(self, signal: dict, change_percent: float) -> dict:
        """评估回撤风险"""
        # 基于近期波动评估
        if abs(change_percent) > 15:
            risk = 'high'
            rationale = f'近期波动剧烈（{change_percent:+.1f}%），最大回撤风险高'
        elif abs(change_percent) > 8:
            risk = 'medium'
            rationale = f'近期波动较大（{change_percent:+.1f}%），注意回撤控制'
        else:
            risk = 'low'
            rationale = '近期波动温和，回撤风险可控'
        
        return {
            'category': 'drawdown',
            'score': risk,
            'max_expected_drawdown': '15%' if risk == 'high' else '10%',
            'rationale': rationale
        }
    
    def _assess_volatility(self, market_data: dict) -> dict:
        """评估波动率风险"""
        # 简化版：基于日内振幅
        high = market_data.get('high', 0)
        low = market_data.get('low', 0)
        current = market_data.get('current_price', 1)
        
        if current > 0 and high > 0 and low > 0:
            intraday_range = (high - low) / current
            
            if intraday_range > 0.15:  # 日内振幅>15%
                risk = 'high'
                rationale = f'日内波动极大（{intraday_range:.1%}），不适合大资金操作'
            elif intraday_range > 0.08:
                risk = 'medium'
                rationale = f'日内波动较大（{intraday_range:.1%}），需控制仓位'
            else:
                risk = 'low'
                rationale = '日内波动温和'
        else:
            risk = 'medium'
            rationale = '无法评估波动率'
        
        return {
            'category': 'volatility',
            'score': risk,
            'rationale': rationale
        }
    
    def _calculate_risk_level(self, position: dict, stop_loss: dict, drawdown: dict, volatility: dict) -> str:
        """计算综合风险等级"""
        scores = [
            position.get('score', 'low'),
            drawdown.get('score', 'low'),
            volatility.get('score', 'low')
        ]
        
        # 如果止损无效，直接高风险
        if not stop_loss.get('valid', True):
            return 'high'
        
        high_count = scores.count('high')
        medium_count = scores.count('medium')
        
        if high_count >= 2:
            return 'high'
        elif high_count == 1 or medium_count >= 2:
            return 'medium'
        else:
            return 'low'
    
    def _make_decision(self, signal: dict, risk_level: str) -> dict:
        """做出审批决策"""
        action = signal.get('signal', 'wait')
        position = signal.get('position_size', '0%')
        
        # 解析仓位
        try:
            position_pct = float(position.replace('%', ''))
        except:
            position_pct = 0
        
        conditions = []
        
        if risk_level == 'high':
            if position_pct > 10:
                return {
                    'status': 'conditional',
                    'max_position': '10%',
                    'conditions': ['降低仓位至10%以下', '收紧止损至7%以内']
                }
            else:
                return {
                    'status': 'approved',
                    'max_position': position,
                    'conditions': ['严格止损', '密切监控']
                }
        elif risk_level == 'medium':
            return {
                'status': 'approved',
                'max_position': position,
                'conditions': ['按计划执行', '每日复盘']
            }
        else:
            return {
                'status': 'approved',
                'max_position': position,
                'conditions': []
            }
    
    def _generate_disclosure(self, signal: dict, risk_level: str) -> str:
        """生成风险披露声明"""
        disclosures = [
            '⚠️ 风险提示：本分析仅供参考，不构成投资建议。',
            f'风险等级：{risk_level}',
            '过往业绩不代表未来表现，投资有风险，入市需谨慎。'
        ]
        
        if risk_level == 'high':
            disclosures.append('⚠️ 当前风险等级较高，建议降低仓位或观望。')
        
        return '\n'.join(disclosures)
