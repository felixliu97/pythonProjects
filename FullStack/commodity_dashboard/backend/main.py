from typing import List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime

# 导入业务逻辑
from commodity_service import CommodityService

app = FastAPI(
    title="Global Commodity Dashboard API",
    description="Professional real-time contract-driven API for global commodity tracking.",
    version="1.2.0",
)

# 1. 定义数据模型 (The Contract)
class Commodity(BaseModel):
    ticker: str = Field(..., example="GC=F", description="商品代码")
    name: str = Field(..., description="商品全称")
    price: float = Field(..., gt=0, description="当前价格")
    unit: str = Field(..., description="计价单位 (如 oz, bbl)")
    change_pct: float = Field(..., description="当日涨跌幅 (%)")
    change_abs: float = Field(..., description="当日涨跌绝对值")
    category: str = Field(..., description="分类 (如 Precious Metals, Energy)")
    icon: str = Field("Globe", description="图标名称 (Lucide)")
    trend: str = Field("Neutral", description="市场情绪 (Bullish, Bearish, Neutral)")
    last_updated: str = Field(..., description="上次更新时间 (YYYY-MM-DD HH:MM:SS)")

# 2. 定义接口 (Endpoints)
@app.get("/commodities", response_model=List[Commodity])
async def list_commodities():
    """
    获取全球大宗商品实时报价。
    数据来源: yfinance (Yahoo Finance)
    缓存策略: 5分钟更新一次，失败时从本地持久化缓存读取。
    """
    data = await CommodityService.fetch_real_time_commodities()
    if not data:
        raise HTTPException(status_code=503, detail="Service Unavailable: No data available from API or Cache")
    return data

@app.get("/commodities/{ticker}", response_model=Commodity)
async def get_commodity(ticker: str):
    """获取单品详情报价。"""
    commodities = await CommodityService.fetch_real_time_commodities()
    commodity = next((c for c in commodities if c["ticker"] == ticker.upper()), None)
    if not commodity:
        raise HTTPException(status_code=404, detail="Commodity not found")
    return commodity
