# -*- coding: utf-8 -*-
"""
股票分析员 - OpenClaw Talent Link 核心数字员工
支持港股(HK)和A股(A股)的7-Agent多智能体分析系统
"""

# 绕过 apport_python_hook 干扰
import sys
for _mod in ['apport_python_hook', 'apport', 'apport.report', 'apport.packaging_impl']:
    if _mod in sys.modules:
        del sys.modules[_mod]

from pathlib import Path
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import Optional, Literal

# 路径设置 - 需要到 src/ 目录才能让 talent_link.agents.technical 生效
# __file__ = src/talent_link/agents/stock_analyst.py
# parent = src/talent_link/agents/
# parent.parent = src/talent_link/
# parent.parent.parent = src/
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from talent_link.agents.technical import TechnicalAgent
from talent_link.agents.fundamental import FundamentalAgent
from talent_link.agents.sentiment import SentimentAgent
from talent_link.agents.bull import BullAgent
from talent_link.agents.bear import BearAgent
from talent_link.agents.trader import TraderAgent
from talent_link.agents.risk import RiskAgent
from talent_link.skills.data_fetcher import DataFetcher


class MarketType(Enum):
    HK = "港股"
    A = "A股"


@dataclass
class MarketData:
    """市场数据"""
    symbol: str
    name: str
    market: str  # "港股" or "A股"
    current_price: float
    change_percent: float
    volume: int
    turnover: float
    high: float
    low: float
    open: float
    prev_close: float
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    # 历史K线数据（用于技术指标计算）
    history: list = field(default_factory=list)
    # A股额外字段
    amplitude: Optional[float] = None  # 振幅
    pe_ratio: Optional[float] = None  # 市盈率
    pb_ratio: Optional[float] = None  # 市净率
    market_cap: Optional[float] = None  # 总市值
    float_market_cap: Optional[float] = None  # 流通市值


class StockAnalyst:
    """
    股票分析员 - 港股+A股多智能体分析系统
    
    工作流程:
    1. 数据获取 (Yahoo Finance港股 / AkShare A股)
    2. 三分析师并行 (技术面 / 基本面 / 情绪面)
    3. 多空辩论 (看多 vs 看空)
    4. 交易信号生成
    5. 风控审核
    6. 输出报告
    """

    def __init__(self, symbol: str, name: str = None):
        self.symbol = symbol
        self.name = name or symbol
        self.report: Optional[dict] = None
        self.data_fetcher = DataFetcher()
        
        # 判断市场类型
        if symbol.endswith('.HK'):
            self.market = MarketType.HK
        elif symbol.isdigit() and len(symbol) == 6:
            self.market = MarketType.A
        else:
            self.market = MarketType.HK  # 默认港股
        
        # 初始化7个Agent
        self.tech_agent = TechnicalAgent()
        self.fund_agent = FundamentalAgent()
        self.sent_agent = SentimentAgent()
        self.bull_agent = BullAgent()
        self.bear_agent = BearAgent()
        self.trader_agent = TraderAgent()
        self.risk_agent = RiskAgent()

    def analyze(self) -> dict:
        """执行完整的7步分析流程"""
        import sys
        # JSON模式时将进度信息输出到stderr，避免污染stdout
        if hasattr(sys, '_called_from_main_json') or __name__ != '__main__':
            print(f"🔍 开始分析 {self.symbol} ({self.market.value}) @ {datetime.now().strftime('%Y-%m-%d %H:%M')}", file=sys.stderr)
        else:
            print(f"🔍 开始分析 {self.symbol} ({self.market.value}) @ {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        
        # Step 1: 获取数据
        market_data = self._fetch_data()
        if not market_data:
            return {"error": f"数据获取失败: {self.symbol}"}
        
        # 转换为dict供agents使用
        market_dict = asdict(market_data)
        
        # Step 2: 三分析师并行
        tech_view = self.tech_agent.analyze(market_dict)
        fund_view = self.fund_agent.analyze(market_dict)
        sent_view = self.sent_agent.analyze(market_dict)
        
        # Step 3: 多空辩论
        debate_input = {
            'technical': tech_view,
            'fundamental': fund_view,
            'sentiment': sent_view,
            'market_data': market_dict
        }
        bull_case = self.bull_agent.debate(debate_input)
        bear_case = self.bear_agent.debate(debate_input)
        
        # Step 4: 生成交易信号
        signal = self.trader_agent.generate_signal(bull_case, bear_case, market_dict)
        
        # Step 5: 风控审核
        risk = self.risk_agent.evaluate(signal, market_dict)
        
        # Step 6: 生成报告
        self.report = self._build_report(
            market_data, tech_view, fund_view, sent_view,
            bull_case, bear_case, signal, risk
        )
        
        return self.report

    def _fetch_data(self) -> MarketData:
        """获取市场数据"""
        data = self.data_fetcher.fetch(self.symbol, self.market.value)
        
        if not data:
            return None
        
        return MarketData(
            symbol=self.symbol,
            name=self.name,
            market=self.market.value,
            current_price=data.get('current_price', 0),
            change_percent=data.get('change_percent', 0),
            volume=data.get('volume', 0),
            turnover=data.get('turnover', 0),
            high=data.get('high', 0),
            low=data.get('low', 0),
            open=data.get('open', 0),
            prev_close=data.get('prev_close', 0),
            history=data.get('history', []),
            amplitude=data.get('amplitude'),
            pe_ratio=data.get('pe_ratio'),
            pb_ratio=data.get('pb_ratio'),
            market_cap=data.get('market_cap'),
            float_market_cap=data.get('float_market_cap'),
        )

    def _build_report(self, market_data, tech, fund, sent, bull, bear, signal, risk) -> dict:
        """构建完整报告"""
        # 综合信心度
        confidence = (
            tech.get('confidence', 0.5) * 0.3 +
            fund.get('confidence', 0.5) * 0.3 +
            sent.get('confidence', 0.5) * 0.2 +
            bull.get('confidence', 0.5) * 0.1 +
            bear.get('confidence', 0.5) * 0.1
        )
        
        # 最终建议
        if risk.get('approval') == 'rejected':
            action = '观望'
            reason = risk.get('rejection_reason', '风控审核未通过')
        else:
            action = signal.get('signal', '观望')
            reason = signal.get('rationale', '')
        
        return {
            "meta": {
                "symbol": self.symbol,
                "name": self.name,
                "market": self.market.value,
                "analysis_time": datetime.now().isoformat(),
                "version": "1.0.0",
                "engine": "OpenClaw Talent Link"
            },
            "market_data": asdict(market_data),
            "technical": tech,
            "fundamental": fund,
            "sentiment": sent,
            "bull_case": bull,
            "bear_case": bear,
            "signal": signal,
            "risk": risk,
            "final_recommendation": {
                "action": action,
                "reason": reason,
                "entry_price": signal.get('entry_price', market_data.current_price),
                "target_price": signal.get('target_price'),
                "stop_loss": signal.get('stop_loss'),
                "max_position": risk.get('max_position', '10%'),
                "confidence": round(confidence, 2)
            }
        }

    def to_text(self) -> str:
        """输出文本格式报告"""
        if not self.report:
            return "请先调用 analyze() 方法"
        
        r = self.report
        m = r['market_data']
        bull = r['bull_case']
        bear = r['bear_case']
        sig = r['signal']
        final = r['final_recommendation']
        
        lines = [
            f"{'='*60}",
            f"📊 {m['name']} ({m['symbol']}) {m['market']}分析报告",
            f"📅 {r['meta']['analysis_time'][:19]}",
            f"{'='*60}",
            f"",
            f"【市场数据']",
            f"当前价格: {m['current_price']}元",
            f"涨跌幅: {m['change_percent']:+.2f}%",
            f"成交量: {m['volume']/10000:.1f}万手",
            f"日内区间: {m['low']} - {m['high']}",
            f"",
            f"【技术面】信心 {r['technical'].get('confidence',0):.0%}",
            f"趋势: {r['technical'].get('trend','N/A')}",
            f"支撑: {r['technical'].get('support_levels',[])}",
            f"阻力: {r['technical'].get('resistance_levels',[])}",
            f"",
            f"【基本面】信心 {r['fundamental'].get('confidence',0):.0%}",
            f"估值: {r['fundamental'].get('valuation','N/A')}",
            f"收入增长: {r['fundamental'].get('revenue_growth','N/A')}%",
            f"",
            f"【多空辩论']",
            f"看多: {bull.get('target_price')}元 (信心 {bull.get('confidence',0):.0%})",
            f"  {bull.get('thesis','')[:80]}",
            f"看空: {bear.get('target_price')}元 (信心 {bear.get('confidence',0):.0%})",
            f"  {bear.get('thesis','')[:80]}",
            f"",
            f"【交易信号】",
            f"操作: {final.get('action')}",
            f"入场: {final.get('entry_price')} → 目标: {final.get('target_price')} → 止损: {final.get('stop_loss')}",
            f"",
            f"【风控】",
            f"仓位: {final.get('max_position')} | 信心: {final.get('confidence',0):.0%}",
            f"",
            f"{'='*60}",
            f"⚠️ 仅供参考，不构成投资建议",
        ]
        return "\n".join(lines)


if __name__ == "__main__":
    import sys
    
    # 解析参数
    args = sys.argv[1:]
    output_json = '--json' in args
    output_text = '--text' in args
    symbol = [a for a in args if not a.startswith('--')][0] if args else None
    
    if not symbol:
        print("用法: python stock_analyst.py <股票代码> [--json|--text]", file=sys.stderr if output_json else sys.stdout)
        print("  港股示例: python stock_analyst.py 2513.HK")
        print("  A股示例: python stock_analyst.py 000001")
        print("  JSON输出: python stock_analyst.py 2513.HK --json")
        sys.exit(1)
    
    analyst = StockAnalyst(symbol)
    
    if output_json:
        import json
        sys._called_from_main_json = True  # 通知analyze()输出到stderr
        report = analyst.analyze()
        if "error" in report:
            sys.stderr.write(f"错误: {report['error']}\n")
            sys.exit(1)
        sys.stdout.write(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        report = analyst.analyze()
        if "error" in report:
            sys.stderr.write(f"错误: {report['error']}\n")
            sys.exit(1)
        print(analyst.to_text())
