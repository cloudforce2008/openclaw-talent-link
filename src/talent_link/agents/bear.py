# -*- coding: utf-8 -*-
"""
Bear Agent - 看空研究员
负责：从三大分析师的真实输出中提取看空论据，提示下跌风险

架构原则：
- 论点必须来自技术/基本面/情绪分析师的真实结论
- 新闻只是分析师结论的佐证或质疑，不单独作为论据
- 置信度 = 技术面40% × 基本面35% × 情绪面25% 加权
"""

from typing import Dict


class BearAgent:
    """看空研究员 Agent"""

    def __init__(self):
        self.name = "Bear Researcher"

    def debate(self, analysis_input: dict) -> dict:
        """
        基于三大分析师的真实输出生成看空论据。

        Args:
            analysis_input: 包含 technical/fundamental/sentiment 三个分析师的真实输出
        """
        technical = analysis_input.get('technical', {})
        fundamental = analysis_input.get('fundamental', {})
        sentiment = analysis_input.get('sentiment', {})
        market_data = analysis_input.get('market_data', {})

        current_price = market_data.get('current_price', 0)

        thesis = self._synthesize_from_analysts(technical, fundamental, sentiment)
        target = self._calculate_target(current_price, technical)
        catalysts = self._identify_catalysts(fundamental, technical, sentiment)
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

    def _synthesize_from_analysts(self, tech, fund, sent) -> str:
        """
        核心：从三大分析师的真实输出中提取看空论点。
        每一条论点都对应具体的分析师结论，不是泛泛而谈。
        """
        lines = []

        # ── 1. 技术分析师的看空结论 ─────────────────────────
        tech_conclusions = []
        trend = tech.get('trend', '')
        rsi = tech.get('indicators', {}).get('rsi', 50)
        macd = tech.get('indicators', {}).get('macd', 'neutral')
        signals = tech.get('signals', [])
        res = tech.get('resistance_levels', [])
        sup = tech.get('support_levels', [])

        if trend in ['strong_downward', 'downward']:
            tech_conclusions.append(
                f"【技术面·趋势】当前{trend}，均线空头排列，下跌动能持续。"
            )
        if rsi > 70:
            tech_conclusions.append(
                f"【技术面·RSI】RSI={rsi:.0f}，进入超买区域，历史上在此处回调概率超过65%。"
            )
        if macd == 'bearish_cross':
            tech_conclusions.append(
                f"【技术面·MACD】MACD形成死叉，是明确的看空信号。"
            )
        if 'overbought_pullback' in signals:
            tech_conclusions.append(
                f"【技术面·超买回调】系统检测到超买信号，回调风险较高。"
            )
        if tech.get('bollinger') == 'above_upper':
            tech_conclusions.append(
                f"【技术面·布林带】股价突破上轨{res[0] if res else ''}，乖离率过大。"
            )
        if tech.get('volume_signal') == 'volume_declining':
            tech_conclusions.append(
                f"【技术面·量能】成交量萎缩，上涨动力不足。"
            )

        for c in tech_conclusions[:2]:
            lines.append(c)

        # ── 2. 基本面分析师的看空结论 ───────────────────────
        fund_conclusions = []
        rev_growth = fund.get('revenue_growth', 0)
        margin = fund.get('profit_margin', 0)
        val = fund.get('valuation', 'fair')
        competition = fund.get('competition_risk', 'medium')
        pe = fund.get('pe_ratio', None)
        analysis = fund.get('analysis', '')

        if margin < -20:
            fund_conclusions.append(
                f"【基本面·亏损】{analysis[:50]}。"
                f"净亏损率{margin:.1f}%，亏损持续扩大，现金流消耗速度快。"
            )
        elif margin < 0:
            fund_conclusions.append(
                f"【基本面·亏损】净利润率{margin:.1f}%，盈利模式尚未验证。"
            )
        if val == 'expensive':
            fund_conclusions.append(
                f"【基本面·估值】估值偏高（PE={pe}），需持续高增长才能支撑当前股价。"
            )
        elif val == 'very_expensive':
            fund_conclusions.append(
                f"【基本面·泡沫】估值远超行业平均，回调风险极高。"
            )
        if competition == 'high':
            fund_conclusions.append(
                f"【基本面·竞争】竞争风险高，多家巨头入局，价格战可能压缩利润。"
            )
        if rev_growth < 0:
            fund_conclusions.append(
                f"【基本面·下滑】收入同比下滑{rev_growth:.0f}%，基本面出现恶化信号。"
            )

        for c in fund_conclusions[:2]:
            lines.append(c)

        # ── 3. 情绪分析师的看空结论 ─────────────────────────
        sent_conclusions = []
        market_sent = sent.get('market_sentiment', 'neutral')
        gs = sent.get('global_signals', {}) or {}
        news_hl: list = sent.get('news_highlights', []) or []

        if market_sent in ['bullish', 'extremely_bullish']:
            sent_conclusions.append(
                f"【情绪面·过热】市场情绪{market_sent}，共识过高，"
                f"一旦业绩不及预期将引发踩踏。"
            )
        elif market_sent == 'neutral' and news_hl:
            sent_conclusions.append(
                f"【情绪面·已定价】利好消息密集，股价可能已充分反映，"
                f"后续需要更多催化才能继续上行。"
            )

        # 全球宏观风险（情绪分析师的判断）
        geo = gs.get('geopolitics', {})
        if geo.get('status') not in ['cold', '', None]:
            sent_conclusions.append(
                f"【情绪面·地缘】{geo.get('description_cn', '')}，"
                f"风险偏好受压，港股外资流向偏紧。"
            )
        gold_chg = (gs.get('commodities') or {}).get('gold', {}).get('change', 0)
        oil_chg = (gs.get('commodities') or {}).get('oil', {}).get('change', 0)
        if gold_chg > 1.5:
            sent_conclusions.append(
                f"【情绪面·避险】黄金+{gold_chg:.1f}%，避险情绪升温，"
                f"对高估值成长股形成压制。"
            )
        if oil_chg > 3:
            sent_conclusions.append(
                f"【情绪面·成本】原油+{oil_chg:.1f}%，通胀压力持续，"
                f"利率难以下降，对科技股估值形成压力。"
            )

        # 新闻标题中的警示信号（作为分析师结论的佐证，不是独立论据）
        for tag, title in news_hl[:2]:
            if any(kw in title for kw in ['减持', '下调', '亏损', '风险', '调查', '预警', '不及预期', '下滑']):
                sent_conclusions.append(
                    f"【情绪面·新闻警示】{tag}：" + title[:40]
                )

        for c in sent_conclusions[:3]:
            lines.append(c)

        if not lines:
            lines.append(
                f"【综合】三个维度暂无明确一致看空信号，"
                f"但当前上涨趋势若无量能支撑，需警惕滞涨风险。"
            )

        return '\n'.join(lines[:5])

    def _calculate_target(self, current: float, technical: dict) -> float:
        """计算看空目标价：基于支撑位"""
        if current <= 0:
            return 0
        support = technical.get('support_levels', [])
        if support:
            target = min(support[0], current * 0.85)
        else:
            target = current * 0.85
        return round(target, 2)

    def _identify_catalysts(self, fundamental: dict, technical: dict, sentiment: dict) -> list:
        """从分析师结论中提取看空催化剂"""
        catalysts = []

        # 基本面催化剂
        if fundamental.get('profit_margin', 0) < -20:
            catalysts.append(f"【基本面】亏损扩大：净亏损率{fundamental.get('profit_margin'):.1f}%")
        if fundamental.get('valuation') == 'expensive':
            catalysts.append(f"【基本面】估值偏高，需持续高增长验证")
        if fundamental.get('competition_risk') == 'high':
            catalysts.append(f"【基本面】竞争加剧：多家巨头入局")

        # 技术面催化剂
        if technical.get('trend') in ['downward', 'strong_downward']:
            catalysts.append(f"【技术面】趋势向下：{technical.get('trend')}")
        rsi = technical.get('indicators', {}).get('rsi', 50)
        if rsi > 70:
            catalysts.append(f"【技术面】RSI={rsi:.0f} 超买，回调概率高")

        # 情绪/宏观催化剂
        gs = sentiment.get('global_signals', {}) or {}
        if (gs.get('commodities') or {}).get('gold', {}).get('change', 0) > 1.5:
            catalysts.append(f"【情绪面】黄金上涨，避险情绪升温")
        if gs.get('geopolitics', {}).get('status') not in ['cold', '', None]:
            catalysts.append(f"【情绪面】地缘风险升温")

        return catalysts[:4]

    def _identify_risks(self, technical: dict, fundamental: dict, sentiment: dict) -> list:
        """识别看空方案的风险（即上涨可能性）"""
        risks = []

        if technical.get('trend') == 'strong_upward':
            risks.append('强劲上涨趋势中，做空可能被套')
        growth = fundamental.get('revenue_growth', 0)
        if growth > 100:
            risks.append(f'高增长({growth:.0f}%)可能继续超预期，压缩下跌空间')
        if fundamental.get('moat') == 'strong':
            risks.append('护城河深厚，竞争对手难以撼动')
        if fundamental.get('profit_margin', 0) > 0:
            risks.append('已实现盈利，下跌有基本面支撑')

        return risks[:3]

    def _calculate_confidence(self, technical: dict, fundamental: dict, sentiment: dict) -> float:
        """
        基于三大分析师输出加权计算看空置信度。

        权重：技术面 40% + 基本面 35% + 情绪面 25%
        新闻作为佐证（最多贡献10%），不独立成为论据。
        """
        # ── 1. 技术面置信度 ───────────────────────────────
        tech_conf = technical.get('confidence', 0.5)
        trend = technical.get('trend', '')
        rsi = technical.get('indicators', {}).get('rsi', 50)
        macd = technical.get('indicators', {}).get('macd', 'neutral')
        signals = technical.get('signals', [])

        if trend in ['downward', 'strong_downward']:
            tech_conf = min(tech_conf + 0.15, 0.95)
        elif trend in ['upward', 'strong_upward']:
            tech_conf = max(tech_conf - 0.15, 0.1)
        if rsi > 70:
            tech_conf = min(tech_conf + 0.12, 0.95)
        elif rsi < 30:
            tech_conf = max(tech_conf - 0.08, 0.1)
        if macd == 'bearish_cross':
            tech_conf = min(tech_conf + 0.10, 0.95)
        if 'overbought_pullback' in signals:
            tech_conf = min(tech_conf + 0.08, 0.95)

        # ── 2. 基本面置信度 ───────────────────────────────
        fund_conf = fundamental.get('confidence', 0.5)
        margin = fundamental.get('profit_margin', 0)
        val = fundamental.get('valuation', 'fair')
        competition = fundamental.get('competition_risk', 'medium')
        rev_growth = fundamental.get('revenue_growth', 0)

        if margin < -20:
            fund_conf = min(fund_conf + 0.12, 0.95)
        elif margin < 0:
            fund_conf = min(fund_conf + 0.06, 0.95)
        if val == 'expensive':
            fund_conf = min(fund_conf + 0.10, 0.95)
        elif val == 'very_expensive':
            fund_conf = min(fund_conf + 0.15, 0.95)
        if competition == 'high':
            fund_conf = min(fund_conf + 0.08, 0.95)
        if rev_growth < 0:
            fund_conf = min(fund_conf + 0.06, 0.95)

        # ── 3. 情绪面置信度 ─────────────────────────────
        sent_conf = sentiment.get('confidence', 0.5)
        market_sent = sentiment.get('market_sentiment', 'neutral')
        gs = sentiment.get('global_signals', {}) or {}

        if market_sent in ['bullish', 'extremely_bullish']:
            sent_conf = min(sent_conf + 0.15, 0.95)
        elif market_sent in ['bearish', 'extremely_bearish']:
            sent_conf = max(sent_conf - 0.10, 0.1)

        geo = gs.get('geopolitics', {})
        if geo.get('status') not in ['cold', '', None]:
            sent_conf = min(sent_conf + 0.08, 0.95)
        if (gs.get('commodities') or {}).get('gold', {}).get('change', 0) > 2:
            sent_conf = min(sent_conf + 0.05, 0.95)

        # 新闻警示信号作为佐证（最多+10%）
        news_hl: list = sentiment.get('news_highlights', []) or []
        news_bearish = sum(
            0.03 for tag, title in news_hl
            if any(kw in title for kw in ['减持', '下调', '亏损', '风险', '预警', '不及预期', '调查', '暴雷'])
        )

        # ── 综合加权 ─────────────────────────────────────
        raw_confidence = (
            tech_conf * 0.40 +
            fund_conf * 0.35 +
            sent_conf * 0.25 +
            min(news_bearish, 0.10)
        )

        return min(max(raw_confidence, 0.10), 0.95)

    def _extract_key_points(self, technical: dict, fundamental: dict, sentiment: dict) -> list:
        """提取关键论点"""
        return [
            f"技术面: {technical.get('analysis', 'N/A')[:50]}...",
            f"基本面: {fundamental.get('analysis', 'N/A')[:50]}...",
            f"催化剂: {', '.join(self._identify_catalysts(fundamental, technical, sentiment)[:2])}"
        ]
