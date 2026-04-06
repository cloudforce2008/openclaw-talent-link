# -*- coding: utf-8 -*-
"""
飞书卡片渲染器 - 股票分析员专用输出技能
将分析报告渲染为飞书 Interactive Card 格式
"""

from typing import Optional
from ..agents.stock_analyst import StockAnalystReport


class FeishuCardRenderer:
    """
    飞书卡片渲染器
    
    输出格式:
    - 飞书 Interactive Card (JSON)
    - 微信图文消息 (Markdown)
    - 纯文本摘要
    """
    
    @staticmethod
    def render(report: StockAnalystReport, style: str = "feishu") -> str:
        """
        渲染报告为指定格式
        
        Args:
            report: 分析报告对象
            style: 输出格式 ("feishu" / "wechat" / "text")
        
        Returns:
            格式化后的字符串
        """
        if style == "feishu":
            return FeishuCardRenderer._render_feishu(report)
        elif style == "wechat":
            return FeishuCardRenderer._render_wechat(report)
        else:
            return FeishuCardRenderer._render_text(report)
    
    @staticmethod
    def _render_feishu(report: StockAnalystReport) -> str:
        """渲染为飞书 Interactive Card"""
        m = report.market_data
        sig = report.signal
        risk = report.risk
        final = report.final_recommendation
        
        # 颜色: 涨红跌绿
        color = "red" if m.change_percent >= 0 else "green"
        change_str = f"{m.change_pct:+.2f}%" if m.change_percent else "N/A"
        
        # 信号颜色
        signal_colors = {
            "买入": "green",
            "持有": "grey", 
            "卖出": "red",
            "观望": "grey"
        }
        signal_color = signal_colors.get(final.get("action", "观望"), "grey")
        
        card = {
            "config": {"wide_screen_mode": True},
            "header": {
                "title": {"tag": "plain_text", "content": f"📊 {m.name} ({m.symbol})"},
                "template": color
            },
            "elements": [
                # 价格区块
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**当前价**: ¥{m.current:.2f}  |  **{change_str}**  |  成交量 {m.volume/10000:.1f}万手"
                    }
                },
                {"tag": "hr"},
                
                # 技术/基本面/情绪三栏
                {
                    "tag": "column_set",
                    "flex_mode": "none",
                    "columns": [
                        {
                            "tag": "column",
                            "width": "weighted",
                            "weight": 1,
                            "elements": [
                                {"tag": "plain_text", "content": "🔬 技术面", "weight": "bold"},
                                {"tag": "div", "text": {"tag": "lark_md", "content": f"趋势: {report.technical.trend}"}},
                                {"tag": "div", "text": {"tag": "lark_md", "content": f"信心: {report.technical.confidence:.0%}"}}
                            ]
                        },
                        {
                            "tag": "column",
                            "width": "weighted",
                            "weight": 1,
                            "elements": [
                                {"tag": "plain_text", "content": "📈 基本面", "weight": "bold"},
                                {"tag": "div", "text": {"tag": "lark_md", "content": f"估值: {report.fundamental.valuation}"}},
                                {"tag": "div", "text": {"tag": "lark_md", "content": f"信心: {report.fundamental.confidence:.0%}"}}
                            ]
                        },
                        {
                            "tag": "column",
                            "width": "weighted",
                            "weight": 1,
                            "elements": [
                                {"tag": "plain_text", "content": "💬 情绪面", "weight": "bold"},
                                {"tag": "div", "text": {"tag": "lark_md", "content": f"新闻: {report.sentiment.news_sentiment}"}},
                                {"tag": "div", "text": {"tag": "lark_md", "content": f"信心: {report.sentiment.confidence:.0%}"}}
                            ]
                        }
                    ]
                },
                {"tag": "hr"},
                
                # 多空辩论
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"⚔️ **多空分歧**: 看多目标 ¥{report.bull_case.target_price:.2f} | 看空目标 ¥{report.bear_case.target_price:.2f}"
                    }
                },
                
                # 最终建议
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"🎯 **最终建议**: **{final.get('action', '观望')}**\n入场 ¥{final.get('entry', 'N/A')} | 目标 ¥{final.get('target', 'N/A')} | 止损 ¥{final.get('stop', 'N/A')}"
                    }
                },
                
                # 风控
                {
                    "tag": "note",
                    "elements": [
                        {"tag": "plain_text", "content": f"🛡️ 风控: {risk.approval} | 建议仓位: {risk.max_position} | 风险: {risk.risk_level}"}
                    ]
                }
            ]
        }
        
        import json
        return json.dumps(card, ensure_ascii=False)
    
    @staticmethod
    def _render_wechat(report: StockAnalystReport) -> str:
        """渲染为微信图文消息 (Markdown)"""
        m = report.market_data
        final = report.final_recommendation
        
        lines = [
            f"📊 **{m.name}** ({m.symbol})",
            f"---",
            f"**当前价**: ¥{m.current:.2f}  |  **{m.change_pct:+.2f}%**",
            f"",
            f"🔬 **技术面**: {report.technical.trend}",
            f"📈 **基本面**: {report.fundamental.valuation}",
            f"💬 **情绪面**: {report.sentiment.news_sentiment}",
            f"",
            f"⚔️ 多空分歧: ¥{report.bull_case.target_price:.2f} vs ¥{report.bear_case.target_price:.2f}",
            f"",
            f"🎯 **建议**: **{final.get('action', '观望')}**",
            f"入场 ¥{final.get('entry')} | 目标 ¥{final.get('target')} | 止损 ¥{final.get('stop')}",
            f"",
            f"🛡️ 风控: {report.risk.risk_level}风险 | 仓位 {report.risk.max_position}",
            f"",
            f"---",
            f"*本报告由 OpenClaw Talent Link 自动生成*"
        ]
        
        return "\n".join(lines)
    
    @staticmethod
    def _render_text(report: StockAnalystReport) -> str:
        """渲染为纯文本 (终端/日志)"""
        m = report.market_data
        final = report.final_recommendation
        
        lines = [
            f"{'='*50}",
            f"📊 {m.name} ({m.symbol}) 分析报告",
            f"{'='*50}",
            f"当前价: ¥{m.current:.2f}  ({m.change_pct:+.2f}%)",
            f"成交量: {m.volume/10000:.1f}万手  成交额: ¥{m.amount/10000:.1f}万",
            f"",
            f"技术面: {report.technical.trend} (信心 {report.technical.confidence:.0%})",
            f"基本面: {report.fundamental.valuation} (信心 {report.fundamental.confidence:.0%})",
            f"情绪面: {report.sentiment.news_sentiment} (信心 {report.sentiment.confidence:.0%})",
            f"",
            f"⚔️ 多空分歧:",
            f"  看多: ¥{report.bull_case.target_price:.2f} (信心 {report.bull_case.confidence:.0%})",
            f"  看空: ¥{report.bear_case.target_price:.2f} (信心 {report.bear_case.confidence:.0%})",
            f"",
            f"🎯 最终建议: {final.get('action', '观望')}",
            f"  入场: ¥{final.get('entry')}  目标: ¥{final.get('target')}  止损: ¥{final.get('stop')}",
            f"",
            f"🛡️ 风控: {report.risk.approval} | 仓位: {report.risk.max_position} | 风险: {report.risk.risk_level}",
            f"{'='*50}",
            f"⚠️ 仅供参考，不构成投资建议",
        ]
        
        return "\n".join(lines)
