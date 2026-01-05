"""
加密货币数据获取工具库
支持获取实时成交明细、买卖盘口、K线数据
"""

import requests
from typing import List, Dict, Any, Optional
from enum import IntEnum


class KlineType(IntEnum):
    """K线类型枚举"""
    MIN_1 = 1      # 1分钟
    MIN_5 = 2      # 5分钟
    MIN_15 = 3     # 15分钟
    MIN_30 = 4     # 30分钟
    HOUR_1 = 5     # 1小时
    HOUR_2 = 6     # 2小时
    HOUR_4 = 7     # 4小时
    DAY = 8        # 日K
    WEEK = 9       # 周K
    MONTH = 10     # 月K
    QUARTER = 11   # 季K
    YEAR = 12      # 年K


class TradeDirection(IntEnum):
    """交易方向枚举"""
    DEFAULT = 0
    BUY = 1
    SELL = 2


class MarketType:
    """市场类型常量"""
    STOCK_US = "STOCK_US"  # 美股
    STOCK_CN = "STOCK_CN"  # A股
    STOCK_HK = "STOCK_HK"  # 港股
    FUTURES = "FUTURES"    # 期货
    FOREX = "FOREX"        # 外汇
    ENERGY = "ENERGY"      # 能源
    METAL = "METAL"        # 金属
    CRYPTO = "CRYPTO"      # 加密货币


class CryptoDataClient:
    """加密货币数据客户端"""

    BASE_URL = "https://data.infoway.io"

    def __init__(self, api_key: str):
        """
        初始化客户端

        Args:
            api_key: API密钥
        """
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({"apiKey": api_key})

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        发起HTTP请求

        Args:
            method: 请求方法 (GET/POST)
            endpoint: API端点
            **kwargs: 其他请求参数

        Returns:
            响应数据字典

        Raises:
            requests.RequestException: 请求失败时抛出
        """
        url = f"{self.BASE_URL}{endpoint}"
        response = self.session.request(method, url, **kwargs)
        response.raise_for_status()

        result = response.json()
        if result.get("ret") != 200:
            raise Exception(f"API错误: {result.get('msg', '未知错误')}")

        return result

    def get_batch_trade(self, codes: List[str]) -> List[Dict[str, Any]]:
        """
        获取产品的实时成交明细

        Args:
            codes: 产品代码列表，例如 ["BTCUSDT", "ETHUSDT"]

        Returns:
            成交明细列表，每个元素包含:
            - s: 标的名称
            - t: 交易时间(毫秒时间戳)
            - p: 价格
            - v: 成交量
            - vw: 成交额
            - td: 交易方向 (0=默认, 1=Buy, 2=Sell)

        Example:
            >>> client = CryptoDataClient("your_api_key")
            >>> trades = client.get_batch_trade(["BTCUSDT", "ETHUSDT"])
        """
        codes_str = ",".join(codes)
        endpoint = f"/crypto/batch_trade/{codes_str}"
        result = self._make_request("GET", endpoint)
        return result.get("data", [])

    def get_batch_depth(self, codes: List[str]) -> List[Dict[str, Any]]:
        """
        获取产品的实时买卖盘口

        Args:
            codes: 产品代码列表，例如 ["BTCUSDT", "ETHUSDT"]

        Returns:
            盘口数据列表，每个元素包含:
            - s: 标的名称
            - t: 时间戳(毫秒)
            - a: 卖盘数据 [[价格列表], [数量列表]]
            - b: 买盘数据 [[价格列表], [数量列表]]

        Example:
            >>> client = CryptoDataClient("your_api_key")
            >>> depth = client.get_batch_depth(["BTCUSDT"])
            >>> # 访问卖一价格: depth[0]['a'][0][0]
            >>> # 访问卖一数量: depth[0]['a'][1][0]
        """
        codes_str = ",".join(codes)
        endpoint = f"/crypto/batch_depth/{codes_str}"
        result = self._make_request("GET", endpoint)
        return result.get("data", [])

    def get_batch_kline(
        self,
        codes: List[str],
        kline_type: KlineType,
        kline_num: int,
        timestamp: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        获取产品的历史/实时K线数据

        Args:
            codes: 产品代码列表，例如 ["BTCUSDT", "ETHUSDT"]
                   单产品最多500根K线，多产品同时查询最多2根K线
                   最多同时查询100个产品
            kline_type: K线类型，使用KlineType枚举
            kline_num: 查询K线数量
            timestamp: 秒时间戳，向前查询历史K线(可选)
                      只针对分钟K和小时K有效，日K及以上不限制

        Returns:
            K线数据列表，每个元素包含:
            - s: 标的代码
            - respList: K线列表，每根K线包含:
                - t: 时间戳(秒)
                - h: 最高价
                - o: 开盘价
                - l: 最低价
                - c: 收盘价
                - v: 成交量
                - vw: 成交额
                - pc: 涨跌幅
                - pca: 涨跌额

        Example:
            >>> client = CryptoDataClient("your_api_key")
            >>> klines = client.get_batch_kline(
            ...     codes=["BTCUSDT"],
            ...     kline_type=KlineType.MIN_1,
            ...     kline_num=10
            ... )
        """
        payload = {
            "klineType": kline_type.value,
            "klineNum": kline_num,
            "codes": ",".join(codes)
        }

        if timestamp is not None:
            payload["timestamp"] = timestamp

        endpoint = "/crypto/v2/batch_kline"
        result = self._make_request("POST", endpoint, json=payload)
        return result.get("data", [])

    def get_symbols(
        self,
        market_type: str = MarketType.CRYPTO,
        symbols: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        查询产品列表

        Args:
            market_type: 市场类型，默认为加密货币(CRYPTO)
                        可选值: STOCK_US, STOCK_CN, STOCK_HK, FUTURES,
                               FOREX, ENERGY, METAL, CRYPTO
            symbols: 可选，指定查询的产品代码列表

        Returns:
            产品列表，每个元素包含:
            - symbol: 标的代码
            - name_cn: 中文名称
            - name_hk: 繁体名称
            - name_en: 英文名称

        Example:
            >>> client = CryptoDataClient("your_api_key")
            >>> # 查询所有加密货币
            >>> all_cryptos = client.get_symbols()
            >>> # 查询指定的产品
            >>> specific = client.get_symbols(symbols=["BTCUSDT", "ETHUSDT"])
        """
        params = {"type": market_type}
        if symbols:
            params["symbols"] = ",".join(symbols)

        endpoint = "/common/basic/symbols"
        result = self._make_request("GET", endpoint, params=params)
        return result.get("data", [])
