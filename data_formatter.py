"""
数据格式化工具
将API数据转换为适合LLM输入的格式化文本
"""

from crypto_data_client import CryptoDataClient, KlineType
from models import Trade, Depth, KlineData
from datetime import datetime
import time


class DataFormatter:
    """数据格式化器"""

    def __init__(self, api_key: str):
        """初始化格式化器"""
        self.client = CryptoDataClient(api_key)

    def format_trade_data(self, symbol: str) -> str:
        """
        格式化成交明细数据

        Args:
            symbol: 产品代码

        Returns:
            格式化的文本
        """
        trades_data = self.client.get_batch_trade([symbol])

        if not trades_data:
            return f"未获取到 {symbol} 的成交明细数据"

        output = []
        output.append(f"产品 {symbol} 的实时成交明细")

        for trade_dict in trades_data:
            trade = Trade.from_dict(trade_dict)
            output.append(f"\n产品代码: {trade.symbol}")
            output.append(f"交易时间: {trade.get_datetime().strftime('%Y-%m-%d %H:%M:%S')}")
            output.append(f"成交价格: {trade.price}")
            output.append(f"成交量: {trade.volume}")
            output.append(f"成交额: {trade.amount}")

            direction_map = {0: "未知", 1: "买入", 2: "卖出"}
            output.append(f"交易方向: {direction_map.get(trade.direction, '未知')}")

        return "\n".join(output)

    def format_depth_data(self, symbol: str) -> str:
        """
        格式化盘口数据

        Args:
            symbol: 产品代码

        Returns:
            格式化的文本
        """
        depth_data = self.client.get_batch_depth([symbol])

        if not depth_data:
            return f"未获取到 {symbol} 的盘口数据"

        output = []
        output.append(f"产品 {symbol} 的实时买卖盘口")

        for depth_dict in depth_data:
            depth = Depth.from_dict(depth_dict)
            output.append(f"\n产品代码: {depth.symbol}")
            output.append(f"更新时间: {depth.get_datetime().strftime('%Y-%m-%d %H:%M:%S')}")

            best_ask_price, best_ask_vol = depth.get_best_ask()
            best_bid_price, best_bid_vol = depth.get_best_bid()

            output.append(f"\n最优卖一价: {best_ask_price}, 数量: {best_ask_vol}")
            output.append(f"最优买一价: {best_bid_price}, 数量: {best_bid_vol}")

            # 显示5档卖盘
            output.append(f"\n卖盘(5档):")
            for i in range(min(5, len(depth.asks[0]))):
                output.append(f"  卖{i+1}: 价格 {depth.asks[0][i]}, 数量 {depth.asks[1][i]}")

            # 显示5档买盘
            output.append(f"\n买盘(5档):")
            for i in range(min(5, len(depth.bids[0]))):
                output.append(f"  买{i+1}: 价格 {depth.bids[0][i]}, 数量 {depth.bids[1][i]}")

        return "\n".join(output)

    def format_kline_data(self, symbol: str, kline_type: KlineType, kline_num: int = 20) -> str:
        """
        格式化K线数据

        Args:
            symbol: 产品代码
            kline_type: K线类型
            kline_num: K线数量

        Returns:
            格式化的文本
        """
        kline_data = self.client.get_batch_kline(
            codes=[symbol],
            kline_type=kline_type,
            kline_num=kline_num
        )

        if not kline_data:
            return f"未获取到 {symbol} 的K线数据"

        output = []
        kline_type_map = {
            KlineType.MIN_1: "1分钟", KlineType.MIN_5: "5分钟",
            KlineType.MIN_15: "15分钟", KlineType.MIN_30: "30分钟",
            KlineType.HOUR_1: "1小时", KlineType.HOUR_2: "2小时",
            KlineType.HOUR_4: "4小时", KlineType.DAY: "日K",
            KlineType.WEEK: "周K", KlineType.MONTH: "月K"
        }

        output.append(f"产品 {symbol} 的{kline_type_map.get(kline_type, '未知')}K线数据")

        for kline_dict in kline_data:
            kline = KlineData.from_dict(kline_dict)
            output.append(f"\n产品代码: {kline.symbol}")
            output.append(f"K线数量: {len(kline.candles)} 根")
            output.append(f"\nK线数据格式: [时间, 开盘, 最高, 最低, 收盘, 成交量, 成交额, 涨跌幅, 涨跌额]")
            output.append("")

            for candle in kline.candles:
                time_str = candle.get_datetime().strftime('%Y-%m-%d %H:%M:%S')
                output.append(f"[{time_str}, {candle.open}, {candle.high}, {candle.low}, "
                            f"{candle.close}, {candle.volume}, {candle.amount}, "
                            f"{candle.change_percent}, {candle.change_amount}]")

        return "\n".join(output)

    def get_current_price(self, symbol: str) -> float:
        """
        获取当前市场价格（从最新成交价获取）

        Args:
            symbol: 产品代码

        Returns:
            当前价格
        """
        trades_data = self.client.get_batch_trade([symbol])
        time.sleep(2)  # 避免API速率限制

        if not trades_data:
            raise ValueError(f"无法获取 {symbol} 的成交数据")

        # 获取最新成交价，并转换为float
        trade = Trade.from_dict(trades_data[0])
        return float(trade.price)

    def format_all_data(self, symbol: str) -> str:
        """
        格式化所有数据（成交明细、盘口、5分钟K线、1小时K线）

        Args:
            symbol: 产品代码

        Returns:
            格式化的完整文本
        """
        output = []
        output.append(f"# 产品 {symbol} 的完整市场数据")
        output.append(f"# 数据获取时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # 1. 成交明细
        output.append(self.format_trade_data(symbol))
        time.sleep(2)

        # 2. 盘口数据
        output.append(self.format_depth_data(symbol))
        time.sleep(2)

        # 3. 5分钟K线
        output.append(self.format_kline_data(symbol, KlineType.MIN_5, kline_num=20))
        time.sleep(2)

        # 4. 1小时K线
        output.append(self.format_kline_data(symbol, KlineType.HOUR_1, kline_num=20))

        return "\n".join(output)
