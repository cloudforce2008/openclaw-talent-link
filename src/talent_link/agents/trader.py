"""
Trader Agent - 交易员
负责：综合多空观点，生成交易信号
"""

from typing import Dict


class TraderAgent:
    """交易员 Agent"""
    
    def __init__(self):
        self.name = "Trader"
    
    def generate_signal(self, bull_case: dict, bear_case: dict, market_data: dict) -> dict:
        """
        基于多空辩论生成交易信号
        
        Args:
            bull_case: 看多研究员的观点
            bear_case: 看空研究员的观点
            market_data: 市场数据
        """
        current_price = market_data.get('current_price', 0)
        
        # 权衡多空观点
        signal = self._weigh_arguments(bull_case, bear_case, current_price)
        
        # 计算目标价和止损
        targets = self._calculate_targets(bull_case, bear_case, current_price)
        
        # 生成理由
        rationale = self._generate_rationale(signal, bull_case, bear_case)
        
        return {
            'agent': self.name,
            'signal': signal['action'],
            'confidence': signal['confidence'],
            'entry_price': current_price,
            'target_price': targets['target'],
            'stop_loss': targets['stop_loss'],
            'position_size': signal['position_size'],
            'time_horizon': signal['time_horizon'],
            'rationale': rationale,
            'key_factors': self._extract_key_factors(bull_case, bear_case)
        }
    
    def _weigh_arguments(self, bull: dict, bear: dict, current: float) -> dict:
        """权衡多空观点，生成信号"""
        bull_conf = bull.get('confidence', 0.5)
        bear_conf = bear.get('confidence', 0.5)
        bull_target = bull.get('target_price', current * 1.1)
        bear_target = bear.get('target_price', current * 0.9)
        
        # 计算风险收益比
        upside = (bull_target - current) / current if current > 0 else 0
        downside = (current - bear_target) / current if current > 0 else 0
        risk_reward = upside / downside if downside > 0 else float('inf')
        
        # 决策逻辑
        if bull_conf > bear_conf and risk_reward > 2:
            action = 'buy'
            confidence = bull_conf
            position = '20%'
        elif bull_conf > bear_conf and risk_reward > 1.5:
            action = 'buy'
            confidence = (bull_conf + bear_conf) / 2
            position = '10%'
        elif bear_conf > bull_conf and risk_reward < 1:
            action = 'sell' if current > bear_target else 'wait'
            confidence = bear_conf
            position = '0%'
        elif abs(bull_conf - bear_conf) < 0.1:
            action = 'wait'
            confidence = 0.5
            position = '0%'
        else:
            action = 'hold' if bull_conf > 0.6 else 'wait'
            confidence = max(bull_conf, bear_conf)
            position = '5%'
        
        return {
            'action': action,
            'confidence': round(confidence, 2),
            'position_size': position,
            'time_horizon': 'medium' if action == 'buy' else 'short',
            'risk_reward': round(risk_reward, 2)
        }
    
    def _calculate_targets(self, bull: dict, bear: dict, current: float) -> dict:
        """计算目标价和止损位"""
        bull_target = bull.get('target_price', current * 1.1)
        bear_target = bear.get('target_price', current * 0.9)
        
        # 目标价偏向看多方的保守估计
        target = (bull_target + current * 1.05) / 2
        
        # 止损位基于看空方的支撑或技术支撑
        stop_loss = max(bear_target, current * 0.93)
        
        return {
            'target': round(target, 2),
            'stop_loss': round(stop_loss, 2)
        }
    
    def _generate_rationale(self, signal: dict, bull: dict, bear: dict) -> str:
        """生成交易理由"""
        action = signal['action']
        
        if action == 'buy':
            return (
                f"基于看多观点（信心度{bull.get('confidence', 0):.0%}），"
                f"{bull.get('thesis', '')[:50]}..."
                f"风险收益比 {signal.get('risk_reward', 0)} 可接受。"
            )
        elif action == 'sell':
            return (
                f"基于看空观点（信心度{bear.get('confidence', 0):.0%}），"
                f"{bear.get('thesis', '')[:50]}..."
            )
        elif action == 'hold':
            return (
                f"多空观点分歧不大（看多{bull.get('confidence', 0):.0%} vs "
                f"看空{bear.get('confidence', 0):.0%}），建议持仓观望。"
            )
        else:
            return (
                f"当前风险收益比 {signal.get('risk_reward', 0)} 不够理想，"
                f"建议等待更明确信号。"
            )
    
    def _extract_key_factors(self, bull: dict, bear: dict) -> dict:
        """提取关键决策因素"""
        return {
            'bull_confidence': bull.get('confidence', 0),
            'bear_confidence': bear.get('confidence', 0),
            'bull_target': bull.get('target_price', 0),
            'bear_target': bear.get('target_price', 0),
            'bull_catalysts': bull.get('catalysts', [])[:2],
            'bear_risks': bear.get('risks', [])[:2]
        }
