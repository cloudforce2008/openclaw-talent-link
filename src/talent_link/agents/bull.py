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
        基于三大分析师的真实输出生成看多论据。
        新闻不是独立论据，而是分析师结论的【证据补充】。
        """
        technical = analysis_input.get('technical', {})
        fundamental = analysis_input.get('fundamental', {})
        sentiment = analysis_input.get('sentiment', {})
        market_data = analysis_input.get('market_data', {})

        current_price = market_data.get('current_price', 0)

        # 论点必须来自三大分析师的真实结论
        thesis = self._synthesize_from_analysts(technical, fundamental, sentiment)
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

    def _synthesize_from_analysts(self, tech, fund, sent) -> str:
        """
        核心：从三大分析师的真实输出中提取看多论点。
        每一行论点都必须对应一个具体的分析师结论。
        """
        lines = []

        # ── 1. 技术分析师的结论 ─────────────────────────────
        tech_conclusions = []
        trend = tech.get('trend', '')
        rsi = tech.get('indicators', {}).get('rsi', 50)
        macd = tech.get('indicators', {}).get('macd', 'neutral')
        signals = tech.get('signals', [])
        sup = tech.get('support_levels', [])
        res = tech.get('resistance_levels', [])

        if trend in ['strong_upward', 'upward']:
            tech_conclusions.append(
                f"【技术面·趋势】{tech.get('analysis','')}。"
                f"当前趋势{trend}，MA5>MA20均线多头排列，上涨动能持续。"
            )
        if rsi < 35:
            tech_conclusions.append(
                f"【技术面·RSI】RSI={rsi:.0f}，进入超卖区域，历史上此处反弹概率超过65%。"
            )
        if macd == 'bullish_cross':
            tech_conclusions.append(
                f"【技术面·MACD】MACD形成金叉，这是强劲的买入信号。"
            )
        if 'oversold_bounce' in signals:
            tech_conclusions.append(
                f"【技术面·超卖反弹】系统检测到底部超卖信号，反弹概率高。"
            )
        current_price = tech.get('current_price', 0)
        if sup and res and current_price:
            dist_to_res = (res[0] - current_price) / current_price * 100 if res else 0
            if dist_to_res < 15:
                tech_conclusions.append(
                    f"【技术面·空间】距离第一阻力位{res[0]}元仅{dist_to_res:.0f}%空间，上涨阻力小。"
                )

        for c in tech_conclusions[:2]:
            lines.append(c)

        # ── 2. 基本面分析师的结论 ─────────────────────────────
        fund_conclusions = []
        rev_growth = fund.get('revenue_growth', 0)
        margin = fund.get('profit_margin', 0)
        moat = fund.get('moat', '')
        pe = fund.get('pe_ratio', None)
        val = fund.get('valuation', 'fair')
        sector = fund.get('sector', '')
        analysis = fund.get('analysis', '')

        if rev_growth >= 50:
            fund_conclusions.append(
                f"【基本面·增长】{analysis[:60]}。"
                f"收入同比增长{rev_growth:.0f}%，远超行业平均，量价逻辑清晰。"
            )
        elif rev_growth > 0:
            fund_conclusions.append(
                f"【基本面·增长】收入增长{rev_growth:.0f}%，保持正向趋势。"
            )
        if margin > 0:
            fund_conclusions.append(
                f"【基本面·盈利】净利润率{margin:.1f}%，已实现盈利，财务健康。"
            )
        elif rev_growth > 80:
            fund_conclusions.append(
                f"【基本面·亏损可控】虽未盈利，但收入增速{rev_growth:.0f}%，规模效应下盈亏平衡可期。"
            )
        if moat == 'strong':
            fund_conclusions.append(
                f"【基本面·护城河】护城河评级：强。竞争对手难以复制核心优势。"
            )
        if val == 'undervalued':
            fund_conclusions.append(
                f"【基本面·估值】估值偏低（PE={pe}），相对内在价值有安全边际。"
            )

        for c in fund_conclusions[:2]:
            lines.append(c)

        # ── 3. 情绪分析师的结论 ─────────────────────────────
        sent_conclusions = []
        news_hl: list = sent.get('news_highlights', []) or []
        market_sent = sent.get('market_sentiment', 'neutral')
        gs = sent.get('global_signals', {})

        # 情绪分析师的结论：市场情绪处于什么状态
        if market_sent in ['bearish', 'extremely_bearish']:
            sent_conclusions.append(
                f"【情绪面·逆向】当前市场情绪{market_sent}，机构普遍悲观，"
                f"逆向角度看反而是布局良机（巴菲特指标）。"
            )
        elif market_sent == 'bullish':
            sent_conclusions.append(
                f"【情绪面·做多】市场情绪向好，顺势而为胜率更高。"
            )

        # 全球宏观 → 对港股的影响
        if gs:
            nasdaq = (gs.get('us_ai_leaders') or {}).get('nasdaq', {})
            nvda = (gs.get('us_ai_leaders') or {}).get('nvda', {})
            gold_chg = (gs.get('commodities') or {}).get('gold', {}).get('change', 0)
            oil_chg = (gs.get('commodities') or {}).get('oil', {}).get('change', 0)

            if nasdaq.get('change_percent', 0) > 0.5:
                sent_conclusions.append(
                    f"【情绪面·外部】纳指+{nasdaq['change_percent']:.1f}%，"
                    f"美股科技情绪向好，映射到港股AI板块形成支撑。"
                )
            if nvda.get('change_percent', 0) > 1:
                sent_conclusions.append(
                    f"【情绪面·AI联动】NVDA+{nvda['change_percent']:.1f}%，"
                    f"对{sector or 'AI'}板块有直接情绪拉动。"
                )
            if gold_chg < -1:
                sent_conclusions.append(
                    f"【情绪面·避险降】黄金{gold_chg:.1f}%，"
                    f"避险情绪降温，资金流向成长股，利好估值扩张。"
                )
            if oil_chg > 2:
                sent_conclusions.append(
                    f"【情绪面·成本】原油+{oil_chg:.1f}%，"
                    f"通胀压力利好资源股，但对科技成长股估值有一定压制。"
                )

        # 新闻标题作为分析师结论的【佐证】（不是独立论据）
        for tag, title in news_hl[:2]:
            if any(kw in title for kw in ['买入', '增持', '上调', '推荐', '突破', '发布', '超预期', '增长']):
                sent_conclusions.append(
                    f"【情绪面·新闻佐证】{tag}：" + title[:40]
                )

        for c in sent_conclusions[:3]:
            lines.append(c)

        if not lines:
            lines.append(
                f"【综合】当前三个维度暂无明确一致看多信号，"
                f"建议等待技术面或基本面出现更清晰催化剂后再入场。"
            )

        return '\n'.join(lines[:5])


    
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
        """识别潜在催化剂（从真实新闻中提取，不只是固定列表）"""
        catalysts = []
        news_highlights: list = sentiment.get('news_highlights', []) or []

        # 从真实新闻中提取看多催化剂
        for tag, title in news_highlights:
            title_lower = title.lower()
            if any(kw in title for kw in ['发布', '推出', '上线', '发布', '重磅']):
                catalysts.append(f'【产品】{title[:35]}')
            elif any(kw in title for kw in ['合作', '签约', '落地', '商业化']):
                catalysts.append(f'【业务】{title[:35]}')
            elif any(kw in title for kw in ['上调', '买入', '增持', '推荐', '跑赢']):
                catalysts.append(f'【评级】{title[:35]}')
            elif any(kw in title for kw in ['增长', '超预期', '营收', '盈利']):
                catalysts.append(f'【业绩】{title[:35]}')

        # 补充结构性催化剂
        if fundamental.get('sector') == 'AI大模型':
            catalysts.extend(['AI应用落地加速', '新模型发布', '大模型商业化'])

        # 去重
        seen = set()
        deduped = []
        for c in catalysts:
            if c not in seen:
                seen.add(c)
                deduped.append(c)

        return deduped[:4]
    
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
        """
        基于三大分析师的输出加权计算看多置信度。
        新闻不是独立权重，而是分析师结论的强化信号。

        权重分配：技术面 40% | 基本面 35% | 情绪面 25%
        """
        # ── 1. 技术面置信度（0-1）────────────────────────────
        tech_conf = technical.get('confidence', 0.5)  # Technical Agent 自带的置信度
        trend = technical.get('trend', '')
        rsi = technical.get('indicators', {}).get('rsi', 50)
        macd = technical.get('indicators', {}).get('macd', 'neutral')
        signals = technical.get('signals', [])

        # 技术面加分（基于真实指标，不是新闻）
        if trend in ['upward', 'strong_upward']:
            tech_conf = min(tech_conf + 0.12, 0.95)
        elif trend in ['downward', 'strong_downward']:
            tech_conf = max(tech_conf - 0.15, 0.1)
        if rsi < 30:
            tech_conf = min(tech_conf + 0.10, 0.95)  # 超卖 → 反弹概率大
        elif rsi > 70:
            tech_conf = max(tech_conf - 0.08, 0.1)  # 超买 → 追高风险大
        if macd == 'bullish_cross':
            tech_conf = min(tech_conf + 0.08, 0.95)
        if 'oversold_bounce' in signals:
            tech_conf = min(tech_conf + 0.08, 0.95)

        # ── 2. 基本面置信度 ─────────────────────────────────
        fund_conf = fundamental.get('confidence', 0.5)
        rev_growth = fundamental.get('revenue_growth', 0)
        margin = fundamental.get('profit_margin', 0)
        moat = fundamental.get('moat', '')
        val = fundamental.get('valuation', 'fair')

        if rev_growth > 80:
            fund_conf = min(fund_conf + 0.12, 0.95)
        elif rev_growth > 30:
            fund_conf = min(fund_conf + 0.06, 0.95)
        if margin > 0:
            fund_conf = min(fund_conf + 0.08, 0.95)
        elif margin < -20:
            fund_conf = max(fund_conf - 0.08, 0.1)
        if moat == 'strong':
            fund_conf = min(fund_conf + 0.08, 0.95)
        if val == 'undervalued':
            fund_conf = min(fund_conf + 0.08, 0.95)
        elif val == 'expensive':
            fund_conf = max(fund_conf - 0.06, 0.1)

        # ── 3. 情绪面置信度（基于分析师结论，不是新闻标签）───
        sent_conf = sentiment.get('confidence', 0.5)
        market_sent = sentiment.get('market_sentiment', 'neutral')
        gs = sentiment.get('global_signals', {}) or {}
        news_hl: list = sentiment.get('news_highlights', []) or []

        if market_sent in ['bearish', 'extremely_bearish']:
            sent_conf = min(sent_conf + 0.12, 0.95)  # 逆向看多
        elif market_sent in ['bullish']:
            sent_conf = min(sent_conf + 0.06, 0.95)

        # 外部市场利好（情绪分析师的结论）
        nasdaq = (gs.get('us_ai_leaders') or {}).get('nasdaq', {})
        nvda = (gs.get('us_ai_leaders') or {}).get('nvda', {})
        if nasdaq.get('change_percent', 0) > 1:
            sent_conf = min(sent_conf + 0.06, 0.95)
        if nvda.get('change_percent', 0) > 1:
            sent_conf = min(sent_conf + 0.06, 0.95)

        # 新闻标题作为强化信号（佐证分析师结论，不单独加分）
        # 如果分析师三方都偏多，新闻再多也是锦上添花
        # 如果分析师有分歧，新闻才作为关键辅助证据
        news_alignment = 0
        if news_hl:
            for tag, title in news_hl:
                if any(kw in title for kw in ['买入', '增持', '上调', '突破', '发布', '超预期', '创新高']):
                    news_alignment += 0.03  # 每条利好新闻 +3%

        # ── 综合加权 ─────────────────────────────────────────
        # 权重：技术40% + 基本面35% + 情绪25%
        raw_confidence = (
            tech_conf * 0.40 +
            fund_conf * 0.35 +
            sent_conf * 0.25 +
            min(news_alignment, 0.10)  # 新闻最多贡献10%
        )

        return min(max(raw_confidence, 0.10), 0.95)
    
    def _extract_key_points(self, technical: dict, fundamental: dict, sentiment: dict) -> list:
        """提取关键论点"""
        return [
            f"技术面: {technical.get('analysis', 'N/A')[:50]}...",
            f"基本面: {fundamental.get('analysis', 'N/A')[:50]}...",
            f"催化剂: {', '.join(self._identify_catalysts(fundamental, sentiment)[:2])}"
        ]
