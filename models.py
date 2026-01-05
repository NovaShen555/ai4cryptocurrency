"""
数据模型类
提供类型安全的数据结构
"""

from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime


@dataclass
class Trade:
    """成交明细数据模型"""
    symbol: str  # 标的名称
    timestamp: int  # 交易时间(毫秒时间戳)
    price: str  # 价格
    volume: str  # 成交量
    amount: str  # 成交额
    direction: int  # 交易方向 (0=默认, 1=Buy, 2=Sell)

    @classmethod
    def from_dict(cls, data: dict) -> "Trade":
        """从字典创建Trade对象"""
        return cls(
            symbol=data["s"],
            timestamp=data["t"],
            price=data["p"],
            volume=data["v"],
            amount=data["vw"],
            direction=data["td"]
        )

    def get_datetime(self) -> datetime:
        """获取交易时间的datetime对象"""
        return datetime.fromtimestamp(self.timestamp / 1000)


@dataclass
class Depth:
    """盘口数据模型"""
    symbol: str  # 标的名称
    timestamp: int  # 时间戳(毫秒)
    asks: List[List[str]]  # 卖盘 [[价格列表], [数量列表]]
    bids: List[List[str]]  # 买盘 [[价格列表], [数量列表]]

    @classmethod
    def from_dict(cls, data: dict) -> "Depth":
        """从字典创建Depth对象"""
        return cls(
            symbol=data["s"],
            timestamp=data["t"],
            asks=data["a"],
            bids=data["b"]
        )

    def get_datetime(self) -> datetime:
        """获取时间的datetime对象"""
        return datetime.fromtimestamp(self.timestamp / 1000)

    def get_best_ask(self) -> tuple[str, str]:
        """获取最优卖价和数量"""
        if self.asks and self.asks[0] and self.asks[1]:
            return self.asks[0][0], self.asks[1][0]
        return "", ""

    def get_best_bid(self) -> tuple[str, str]:
        """获取最优买价和数量"""
        if self.bids and self.bids[0] and self.bids[1]:
            return self.bids[0][0], self.bids[1][0]
        return "", ""


@dataclass
class Candle:
    """K线数据模型"""
    timestamp: int  # 时间戳(秒)
    high: str  # 最高价
    open: str  # 开盘价
    low: str  # 最低价
    close: str  # 收盘价
    volume: str  # 成交量
    amount: str  # 成交额
    change_percent: str  # 涨跌幅
    change_amount: str  # 涨跌额

    @classmethod
    def from_dict(cls, data: dict) -> "Candle":
        """从字典创建Candle对象"""
        return cls(
            timestamp=int(data["t"]),
            high=data["h"],
            open=data["o"],
            low=data["l"],
            close=data["c"],
            volume=data["v"],
            amount=data["vw"],
            change_percent=data["pc"],
            change_amount=data["pca"]
        )

    def get_datetime(self) -> datetime:
        """获取时间的datetime对象"""
        return datetime.fromtimestamp(self.timestamp)


@dataclass
class KlineData:
    """K线数据集合模型"""
    symbol: str  # 标的代码
    candles: List[Candle]  # K线列表

    @classmethod
    def from_dict(cls, data: dict) -> "KlineData":
        """从字典创建KlineData对象"""
        candles = [Candle.from_dict(c) for c in data.get("respList", [])]
        return cls(
            symbol=data["s"],
            candles=candles
        )


@dataclass
class Symbol:
    """产品信息数据模型"""
    symbol: str  # 标的代码
    name_cn: Optional[str] = None  # 中文名称
    name_hk: Optional[str] = None  # 繁体名称
    name_en: Optional[str] = None  # 英文名称

    @classmethod
    def from_dict(cls, data: dict) -> "Symbol":
        """从字典创建Symbol对象"""
        return cls(
            symbol=data["symbol"],
            name_cn=data.get("name_cn"),
            name_hk=data.get("name_hk"),
            name_en=data.get("name_en")
        )
