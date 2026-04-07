# -*- coding: utf-8 -*-
"""
Web API - 数字人才市场股票分析接口
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

# 设置路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from talent_link.agents.stock_analyst import StockAnalyst


# ============ 数据模型 ============

class StockQuery(BaseModel):
    symbol: str
    name: Optional[str] = None


class StockReport(BaseModel):
    meta: dict
    market_data: dict
    technical: dict
    fundamental: dict
    sentiment: dict
    bull_case: dict
    bear_case: dict
    signal: dict
    risk: dict
    final_recommendation: dict


# ============ FastAPI 应用 ============

app = FastAPI(
    title="数字人才市场 - 股票分析API",
    description="港股+A股智能分析，7-Agent多智能体系统",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "service": "数字人才市场 - 股票分析员",
        "version": "1.0.0",
        "endpoints": {
            "GET /api/stock/{symbol}": "分析单只股票",
            "POST /api/stock/analyze": "分析股票 (POST body)",
            "GET /api/health": "健康检查",
        }
    }


@app.get("/api/health")
async def health():
    return {"status": "ok", "time": datetime.now().isoformat()}


@app.get("/api/stock/{symbol}")
async def analyze_stock_get(symbol: str, name: Optional[str] = None):
    """
    GET方式分析股票
    
    Args:
        symbol: 股票代码
            - 港股: 2513.HK, 0100.HK
            - A股: 000001, 600000
        name: 股票名称(可选)
    """
    try:
        analyst = StockAnalyst(symbol, name)
        report = analyst.analyze()
        
        if "error" in report:
            raise HTTPException(status_code=404, detail=report["error"])
        
        return report
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/stock/analyze")
async def analyze_stock_post(query: StockQuery):
    """
    POST方式分析股票
    
    Body:
    {
        "symbol": "2513.HK",
        "name": "智谱AI"
    }
    """
    try:
        analyst = StockAnalyst(query.symbol, query.name)
        report = analyst.analyze()
        
        if "error" in report:
            raise HTTPException(status_code=404, detail=report["error"])
        
        return report
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stock/{symbol}/summary")
async def stock_summary(symbol: str):
    """
    获取简化版股票摘要（用于列表展示）
    """
    try:
        analyst = StockAnalyst(symbol)
        report = analyst.analyze()
        
        if "error" in report:
            raise HTTPException(status_code=404, detail=report["error"])
        
        m = report['market_data']
        final = report['final_recommendation']
        
        return {
            "symbol": m['symbol'],
            "name": m['name'],
            "market": m['market'],
            "price": m['current_price'],
            "change": m['change_percent'],
            "action": final['action'],
            "confidence": final['confidence'],
            "target": final.get('target_price'),
            "stop": final.get('stop_loss'),
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ 启动 ============

if __name__ == "__main__":
    print("🚀 启动股票分析API服务...")
    print("📍 http://localhost:8000")
    print("📚 API文档: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
