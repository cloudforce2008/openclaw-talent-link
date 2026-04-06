# -*- coding: utf-8 -*-
"""
AkShare A股数据封装 - 股票分析员专用数据技能
用于获取A股实时行情、财务数据、板块信息等
"""

from typing import Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class AStockQuote:
    """A股实时行情"""
    symbol: str           # 股票代码 (e.g., "000001")
    name: str            # 股票名称
    current: float       # 当前价格
    change: float        # 涨跌额
    change_pct: float    # 涨跌幅 %
    volume: int          # 成交量 (手)
    amount: float        # 成交额 (元)
    high: float          # 最高价
    low: float           # 最低价
    open: float          # 开盘价
    prev_close: float    # 昨收价
    timestamp: str       # 数据时间


class AkShareWrapper:
    """
    AkShare A股数据封装类
    
    功能覆盖:
    - 实时行情
    - 历史行情
    - 主力资金流向
    - 龙虎榜数据
    - 板块/概念涨跌
    """
    
    def __init__(self):
        self._client = None  # Lazy init
    
    def _get_client(self):
        """延迟初始化 AkShare"""
        if self._client is None:
            try:
                import akshare as ak
                self._client = ak
            except ImportError:
                raise ImportError("请先安装 akshare: pip install akshare")
        return self._client
    
    def get_quote(self, symbol: str) -> AStockQuote:
        """
        获取单只A股实时行情
        
        Args:
            symbol: 股票代码 (支持沪深全市场)
                    - 上交所: 600000 (6位数)
                    - 深交所: 000001 (6位数)
                    - 创业板: 300001 (6位数)
                    - 科创板: 688001 (6位数)
        
        Returns:
            AStockQuote 对象
        """
        client = self._get_client()
        
        # 判断市场
        if symbol.startswith("6"):
            market = "sh"
        else:
            market = "sz"
        
        # 获取实时行情
        df = client.stock_zh_a_spot_em()
        row = df[df["代码"] == symbol]
        
        if row.empty:
            raise ValueError(f"未找到股票: {symbol}")
        
        r = row.iloc[0]
        return AStockQuote(
            symbol=r["代码"],
            name=r["名称"],
            current=float(r["最新价"]),
            change=float(r["涨跌额"]),
            change_pct=float(r["涨跌幅"]),
            volume=int(r["成交量"]),
            amount=float(r["成交额"]),
            high=float(r["最高"]),
            low=float(r["最低"]),
            open=float(r["开盘"]),
            prev_close=float(r["昨收"]),
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
    
    def get_realtime_quotes(self, symbols: list[str]) -> list[AStockQuote]:
        """
        批量获取实时行情 (用于自选股监控)
        
        Args:
            symbols: 股票代码列表
        
        Returns:
            AStockQuote 列表
        """
        return [self.get_quote(s) for s in symbols]
    
    def get_money_flow(self, symbol: str) -> dict:
        """
        获取个股资金流向
        
        Args:
            symbol: 股票代码
        
        Returns:
            资金流向字典 {
                "main_inflow": 主力净流入 (元)
                "main_inflow_pct": 主力净流入占比 %
                "retail_inflow": 散户净流入
                "buy_large": 大单买入
                "sell_large": 大单卖出
            }
        """
        client = self._get_client()
        df = client.stock_individual_fund_flow(stock=symbol, indicator="今日")
        
        return {
            "main_inflow": float(df["主力净流入"].iloc[0]),
            "main_inflow_pct": float(df["主力净流入占比"].iloc[0]),
            "retail_inflow": float(df["散户净流入"].iloc[0]),
            "buy_large": float(df["大单买入"].iloc[0]),
            "sell_large": float(df["大单卖出"].iloc[0])
        }
    
    def get_sector_ranking(self, sector: str = "行业") -> list[dict]:
        """
        获取板块涨跌排行
        
        Args:
            sector: 板块类型
                    - "行业": 行业板块
                    - "concept": 概念板块
                    - "地域": 地域板块
        
        Returns:
            板块排行列表
        """
        client = self._get_client()
        
        if sector == "行业":
            df = client.stock_board_industry_name_em()
        elif sector == "概念":
            df = client.stock_board_concept_name_em()
        else:
            df = client.stock_board_area_name_em()
        
        # 按涨跌幅排序
        df = df.sort_values("涨跌幅", ascending=False)
        
        return df.head(20).to_dict("records")
    
    def get_limit_up(self) -> list[dict]:
        """
        获取今日涨停股票
        
        Returns:
            涨停股票列表
        """
        client = self._get_client()
        df = client.stock_zt_pool_em(date=datetime.now().strftime("%Y%m%d"))
        return df.to_dict("records") if df is not None else []
    
    def get_limit_down(self) -> list[dict]:
        """
        获取今日跌停股票
        
        Returns:
            跌停股票列表
        """
        client = self._get_client()
        df = client.stock_zt_pool_falling_em(date=datetime.now().strftime("%Y%m%d"))
        return df.to_dict("records") if df is not None else []


# 便捷函数
def get_quote(symbol: str) -> AStockQuote:
    """获取单只A股行情"""
    return AkShareWrapper().get_quote(symbol)


def get_money_flow(symbol: str) -> dict:
    """获取个股资金流向"""
    return AkShareWrapper().get_money_flow(symbol)
