# 加密货币数据获取工具库

这是一个用于获取加密货币实时数据的Python工具库，支持获取实时成交明细、买卖盘口和K线数据。

## 功能特性

- ✅ 获取实时成交明细 (Trade)
- ✅ 获取实时买卖盘口 (Depth)
- ✅ 获取实时/历史K线数据 (Candles)
- ✅ 支持多种K线周期（1分钟到年K）
- ✅ 类型安全的数据模型
- ✅ 简洁易用的API

## 安装依赖

```bash
pip install requests
```

## 快速开始

### 1. 初始化客户端

```python
from crypto_data_client import CryptoDataClient

api_key = "YOUR_API_KEY_HERE"
client = CryptoDataClient(api_key)
```

### 2. 获取实时成交明细

```python
from models import Trade

# 获取多个产品的成交明细
trades_data = client.get_batch_trade(["BTCUSDT", "ETHUSDT"])

# 使用数据模型解析
for trade_dict in trades_data:
    trade = Trade.from_dict(trade_dict)
    print(f"产品: {trade.symbol}")
    print(f"价格: {trade.price}")
    print(f"成交量: {trade.volume}")
    print(f"时间: {trade.get_datetime()}")
```

### 3. 获取实时买卖盘口

```python
from models import Depth

# 获取盘口数据
depth_data = client.get_batch_depth(["BTCUSDT"])

for depth_dict in depth_data:
    depth = Depth.from_dict(depth_dict)

    # 获取最优买卖价
    best_ask_price, best_ask_vol = depth.get_best_ask()
    best_bid_price, best_bid_vol = depth.get_best_bid()

    print(f"产品: {depth.symbol}")
    print(f"最优卖价: {best_ask_price}, 数量: {best_ask_vol}")
    print(f"最优买价: {best_bid_price}, 数量: {best_bid_vol}")
```

### 4. 获取K线数据

```python
from crypto_data_client import KlineType
from models import KlineData

# 获取1分钟K线，最近10根
kline_data = client.get_batch_kline(
    codes=["BTCUSDT"],
    kline_type=KlineType.MIN_1,
    kline_num=10
)

for kline_dict in kline_data:
    kline = KlineData.from_dict(kline_dict)
    print(f"产品: {kline.symbol}")

    for candle in kline.candles:
        print(f"时间: {candle.get_datetime()}")
        print(f"开盘: {candle.open}, 收盘: {candle.close}")
        print(f"最高: {candle.high}, 最低: {candle.low}")
        print(f"涨跌幅: {candle.change_percent}")
```

### 5. 查询产品列表

```python
from crypto_data_client import MarketType
from models import Symbol

# 查询所有加密货币产品
all_symbols = client.get_symbols(market_type=MarketType.CRYPTO)

for symbol_dict in all_symbols[:10]:  # 显示前10个
    symbol = Symbol.from_dict(symbol_dict)
    print(f"代码: {symbol.symbol}")
    print(f"中文名: {symbol.name_cn}")
    print(f"英文名: {symbol.name_en}")

# 查询指定产品
specific = client.get_symbols(
    market_type=MarketType.CRYPTO,
    symbols=["BTCUSDT", "ETHUSDT"]
)
```

## K线类型说明

工具库支持以下K线周期类型：

| 枚举值 | 说明 |
|-------|------|
| `KlineType.MIN_1` | 1分钟K线 |
| `KlineType.MIN_5` | 5分钟K线 |
| `KlineType.MIN_15` | 15分钟K线 |
| `KlineType.MIN_30` | 30分钟K线 |
| `KlineType.HOUR_1` | 1小时K线 |
| `KlineType.HOUR_2` | 2小时K线 |
| `KlineType.HOUR_4` | 4小时K线 |
| `KlineType.DAY` | 日K线 |
| `KlineType.WEEK` | 周K线 |
| `KlineType.MONTH` | 月K线 |
| `KlineType.QUARTER` | 季K线 |
| `KlineType.YEAR` | 年K线 |

## 市场类型说明

工具库支持查询以下市场类型的产品：

| 常量 | 说明 |
|------|------|
| `MarketType.CRYPTO` | 加密货币 |
| `MarketType.STOCK_US` | 美股 |
| `MarketType.STOCK_CN` | A股 |
| `MarketType.STOCK_HK` | 港股 |
| `MarketType.FUTURES` | 期货 |
| `MarketType.FOREX` | 外汇 |
| `MarketType.ENERGY` | 能源 |
| `MarketType.METAL` | 金属 |

## API参考

### CryptoDataClient

#### `get_batch_trade(codes: List[str])`

获取产品的实时成交明细。

**参数:**
- `codes`: 产品代码列表

**返回:** 成交明细数据列表

#### `get_batch_depth(codes: List[str])`

获取产品的实时买卖盘口。

**参数:**
- `codes`: 产品代码列表

**返回:** 盘口数据列表

#### `get_batch_kline(codes, kline_type, kline_num, timestamp=None)`

获取产品的历史/实时K线数据。

**参数:**
- `codes`: 产品代码列表
- `kline_type`: K线类型（使用KlineType枚举）
- `kline_num`: 查询K线数量（单产品最多500根，多产品最多2根）
- `timestamp`: 可选，秒时间戳，用于查询历史K线

**返回:** K线数据列表

#### `get_symbols(market_type=MarketType.CRYPTO, symbols=None)`

查询产品列表。

**参数:**
- `market_type`: 市场类型，默认为CRYPTO（加密货币）
- `symbols`: 可选，指定查询的产品代码列表

**返回:** 产品信息列表

## 注意事项

1. **API Key**: 使用前需要先获取有效的API Key
2. **请求限制**:
   - 单产品K线查询最多500根
   - 多产品同时查询K线最多2根
   - 最多同时查询100个产品
3. **时间戳**: K线查询的timestamp参数仅对分钟K和小时K有效
4. **数据格式**: 所有价格、数量等数值均为字符串格式，需要时请转换为数值类型

## 项目结构

```
ai4cryptocurrency/
├── crypto_data_client.py  # 主客户端类
├── models.py              # 数据模型
├── example.py             # 使用示例
└── README.md              # 项目文档
```

## 完整示例

查看 `example.py` 文件获取更多使用示例，包括：
- 获取实时成交明细
- 获取实时买卖盘口
- 获取实时K线数据
- 获取历史K线数据
- 查询产品列表

运行示例：

```bash
python example.py
```

## 数据模型

工具库提供了以下数据模型类：

- **Trade**: 成交明细数据模型
- **Depth**: 盘口数据模型
- **Candle**: 单根K线数据模型
- **KlineData**: K线数据集合模型
- **Symbol**: 产品信息数据模型

所有模型都提供了 `from_dict()` 类方法用于从API返回的字典数据创建对象。

## 许可证

MIT License