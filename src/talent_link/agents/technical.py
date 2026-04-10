"""
Technical Agent - 技术分析师
负责：K线形态、技术指标、支撑阻力位分析
"""

import json
import subprocess
from typing import Dict, List


class TechnicalAgent:
    """技术分析师 Agent"""
    
    def __init__(self):
        self.name = "Technical Analyst"
        self.confidence_threshold = 0.6
    
    def analyze(self, market_data: dict) -> dict:
        """
        技术分析主函数
        
        Args:
            market_data: 包含实时行情和历史数据的字典
            
        Returns:
            技术分析结果 JSON
        """
        symbol = market_data.get('symbol', '')
        
        # 获取历史数据计算指标
        history = market_data.get('history', [])
        current = market_data.get('current', {})
        
        # 计算技术指标
        indicators = self._calculate_indicators(history)
        
        # 识别趋势
        trend = self._identify_trend(history, current)
        
        # 计算支撑阻力位
        support_resistance = self._calculate_support_resistance(history)
        
        # 生成交易信号
        signals = self._generate_signals(indicators, trend, current)
        
        # 计算置信度
        confidence = self._calculate_confidence(indicators, trend)
        
        return {
            'agent': self.name,
            'trend': trend,
            'support_levels': support_resistance['support'],
            'resistance_levels': support_resistance['resistance'],
            'indicators': indicators,
            'signals': signals,
            'confidence': confidence,
            'analysis': self._generate_analysis_text(trend, indicators, signals),
            'forecast': self._forecast(market_data.get('current_price', 0), history, trend),
        }
    
    def _calculate_indicators(self, history: List[dict]) -> dict:
        """计算技术指标"""
        if len(history) < 14:
            return {'rsi': 50, 'macd': 'neutral', 'bollinger': 'middle'}
        
        # 计算 RSI
        rsi = self._calculate_rsi(history)
        
        # 计算 MACD 信号
        macd = self._calculate_macd(history)
        
        # 布林带位置
        bollinger = self._calculate_bollinger_position(history)
        
        return {
            'rsi': round(rsi, 1),
            'macd': macd,
            'bollinger': bollinger,
            'ma5': self._calculate_ma(history, 5),
            'ma10': self._calculate_ma(history, 10),
            'ma20': self._calculate_ma(history, 20)
        }
    
    def _calculate_rsi(self, history: List[dict], period: int = 14) -> float:
        """计算 RSI 指标"""
        if len(history) < period + 1:
            return 50.0
        
        closes = [h['close'] for h in history[-(period+1):]]
        gains = []
        losses = []
        
        for i in range(1, len(closes)):
            change = closes[i] - closes[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        avg_gain = sum(gains) / len(gains) if gains else 0
        avg_loss = sum(losses) / len(losses) if losses else 0
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_macd(self, history: List[dict]) -> str:
        """简化版 MACD 信号判断"""
        if len(history) < 26:
            return 'neutral'
        
        closes = [h['close'] for h in history]
        ema12 = self._calculate_ema(closes, 12)
        ema26 = self._calculate_ema(closes, 26)
        
        if len(ema12) < 2 or len(ema26) < 2:
            return 'neutral'
        
        macd_line = ema12[-1] - ema26[-1]
        macd_prev = ema12[-2] - ema26[-2]
        
        if macd_prev < 0 and macd_line > 0:
            return 'bullish_cross'  # 金叉
        elif macd_prev > 0 and macd_line < 0:
            return 'bearish_cross'  # 死叉
        elif macd_line > 0:
            return 'bullish'
        else:
            return 'bearish'
    
    def _calculate_ema(self, data: List[float], period: int) -> List[float]:
        """计算 EMA"""
        if len(data) < period:
            return data
        
        multiplier = 2 / (period + 1)
        ema = [sum(data[:period]) / period]  # 初始值为 SMA
        
        for price in data[period:]:
            ema.append((price - ema[-1]) * multiplier + ema[-1])
        
        return ema
    
    def _calculate_ma(self, history: List[dict], period: int) -> float:
        """计算简单移动平均线"""
        if len(history) < period:
            return history[-1]['close'] if history else 0
        
        closes = [h['close'] for h in history[-period:]]
        return round(sum(closes) / len(closes), 2)
    
    def _calculate_bollinger_position(self, history: List[dict]) -> str:
        """计算当前价格在布林带中的位置"""
        if len(history) < 20:
            return 'middle'
        
        closes = [h['close'] for h in history[-20:]]
        ma20 = sum(closes) / len(closes)
        std = (sum((x - ma20) ** 2 for x in closes) / len(closes)) ** 0.5
        
        upper = ma20 + 2 * std
        lower = ma20 - 2 * std
        current = closes[-1]
        
        if current > upper:
            return 'above_upper'  # 突破上轨
        elif current < lower:
            return 'below_lower'  # 跌破下轨
        elif current > ma20:
            return 'upper_half'
        else:
            return 'lower_half'
    
    def _identify_trend(self, history: List[dict], current: dict) -> str:
        """识别趋势"""
        if len(history) < 5:
            return 'sideways'
        
        closes = [h['close'] for h in history[-5:]]
        current_price = current.get('price', closes[-1])
        
        # 计算短期趋势
        if current_price > closes[0] * 1.05:
            return 'strong_upward'
        elif current_price > closes[0] * 1.02:
            return 'upward'
        elif current_price < closes[0] * 0.95:
            return 'strong_downward'
        elif current_price < closes[0] * 0.98:
            return 'downward'
        else:
            return 'sideways'
    
    def _calculate_support_resistance(self, history: List[dict]) -> dict:
        """计算支撑阻力位（简化版）"""
        if len(history) < 20:
            return {'support': [], 'resistance': []}
        
        closes = [h['close'] for h in history]
        highs = [h['high'] for h in history]
        lows = [h['low'] for h in history]
        
        current = closes[-1]
        
        # 简化计算：使用近期高低点和移动平均线
        support_levels = []
        resistance_levels = []
        
        # 最近20日低点作为支撑
        recent_lows = sorted(lows[-20:])[:3]
        support_levels = [round(x, 2) for x in sorted(set(recent_lows))]
        
        # 最近20日高点作为阻力
        recent_highs = sorted(highs[-20:], reverse=True)[:3]
        resistance_levels = [round(x, 2) for x in sorted(set(recent_highs))]
        
        # 添加均线支撑/阻力
        ma20 = sum(closes[-20:]) / 20
        if ma20 < current:
            support_levels.append(round(ma20, 2))
        else:
            resistance_levels.append(round(ma20, 2))
        
        return {
            'support': sorted(list(set(support_levels)))[-2:],  # 最近2个支撑
            'resistance': sorted(list(set(resistance_levels)))[:2]  # 最近2个阻力
        }
    
    def _generate_signals(self, indicators: dict, trend: str, current: dict) -> List[str]:
        """生成交易信号"""
        signals = []
        
        # RSI 信号
        rsi = indicators.get('rsi', 50)
        if rsi < 30:
            signals.append('oversold_bounce')
        elif rsi > 70:
            signals.append('overbought_pullback')
        
        # MACD 信号
        macd = indicators.get('macd', 'neutral')
        if macd == 'bullish_cross':
            signals.append('macd_golden_cross')
        elif macd == 'bearish_cross':
            signals.append('macd_death_cross')
        
        # 布林带信号
        bollinger = indicators.get('bollinger', 'middle')
        if bollinger == 'below_lower':
            signals.append('bollinger_oversold')
        elif bollinger == 'above_upper':
            signals.append('bollinger_overbought')
        
        # 趋势信号
        if trend == 'strong_upward':
            signals.append('uptrend_momentum')
        elif trend == 'strong_downward':
            signals.append('downtrend_risk')
        
        return signals
    
    def _calculate_confidence(self, indicators: dict, trend: str) -> float:
        """计算分析置信度"""
        confidence = 0.5
        
        # RSI 置信度
        rsi = indicators.get('rsi', 50)
        if rsi < 20 or rsi > 80:
            confidence += 0.2  # 极端值置信度高
        elif rsi < 30 or rsi > 70:
            confidence += 0.1
        
        # MACD 置信度
        macd = indicators.get('macd', 'neutral')
        if macd in ['bullish_cross', 'bearish_cross']:
            confidence += 0.15
        
        # 趋势置信度
        if trend in ['strong_upward', 'strong_downward']:
            confidence += 0.15
        
        return min(confidence, 0.95)
    
    def _forecast(self, current_price: float, history: list, trend: str) -> dict:
        """
        基于历史波动率估算未来不同时间维度的价格区间
        方法：日收益率标准差 × √天数，不依赖历史均值（不可靠）
        趋势方向只修正期望值，不放大波动区间
        """
        if len(history) < 10 or not current_price:
            return {}

        # 计算日收益率
        closes = [h['close'] for h in history]
        returns = []
        for i in range(1, len(closes)):
            if closes[i-1] > 0:
                ret = (closes[i] - closes[i-1]) / closes[i-1]
                returns.append(ret)

        if not returns:
            return {}

        import statistics, math
        daily_std = statistics.stdev(returns) if len(returns) > 1 else 0.02

        # 趋势方向修正（只调期望值，不放大波动范围）
        trend_drift = {
            'strong_upward': 0.15,   # 强趋势月均+15%
            'upward': 0.08,
            'sideways': 0.0,
            'downward': -0.08,
            'strong_downward': -0.15,
        }.get(trend, 0.0)

        def price_range(days: int) -> dict:
            """计算N天后的68%置信区间"""
            vol = daily_std * math.sqrt(days)  # 波动幅度

            # 期望值 = 当前价 + 趋势漂移（按天折算）
            drift_fraction = trend_drift * (days / 21)  # 趋势月化后按天数比例
            expected = current_price * (1 + drift_fraction)

            # 区间 = 期望值 ± 1个标准差
            band = current_price * vol
            upper = expected + band
            lower = max(expected - band, current_price * 0.5)  # 最低跌一半

            # 波动率随时间稀释（短期波动大，长期趋于均值）
            volatility_pct = round(vol * 100, 1)

            return {
                'expected': round(expected, 2),
                'upper_68': round(upper, 2),
                'lower_68': round(lower, 2),
                'range_pct': volatility_pct,
            }

        forecast = {
            'current_price': current_price,
            'daily_volatility': round(daily_std * 100, 2),
            'annualized_vol': round(daily_std * 252 * 100, 1),
            '1_week': price_range(5),
            '2_week': price_range(10),
            '1_month': price_range(21),
            '3_month': price_range(63),
        }
        return forecast

    def _generate_analysis_text(self, trend: str, indicators: dict, signals: List[str]) -> str:
        """生成分析文本"""
        texts = []
        
        trend_map = {
            'strong_upward': '强势上涨',
            'upward': '上涨',
            'sideways': '横盘整理',
            'downward': '下跌',
            'strong_downward': '强势下跌'
        }
        texts.append(f"当前趋势: {trend_map.get(trend, trend)}")
        
        rsi = indicators.get('rsi', 50)
        if rsi < 30:
            texts.append(f"RSI {rsi} 显示超卖，存在反弹机会")
        elif rsi > 70:
            texts.append(f"RSI {rsi} 显示超买，注意回调风险")
        
        macd = indicators.get('macd', 'neutral')
        if macd == 'bullish_cross':
            texts.append("MACD 金叉，短期看涨")
        elif macd == 'bearish_cross':
            texts.append("MACD 死叉，短期看跌")
        
        if signals:
            texts.append(f"技术指标信号: {', '.join(signals)}")
        
        return '; '.join(texts)
