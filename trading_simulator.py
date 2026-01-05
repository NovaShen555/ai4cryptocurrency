"""
模拟交易程序
支持做多做空、杠杆交易、仓位管理等功能
"""

from typing import Optional, List, Dict
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import json
import os


class PositionType(Enum):
    """仓位类型"""
    LONG = "LONG"   # 做多
    SHORT = "SHORT"  # 做空


@dataclass
class Trade:
    """交易记录"""
    trade_id: int
    timestamp: datetime
    position_type: PositionType
    quantity: float  # 交易数量
    price: float  # 交易价格
    leverage: int  # 杠杆倍率
    cost: float  # 实际花费（保证金）
    is_open: bool  # True=开仓, False=平仓

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "trade_id": self.trade_id,
            "timestamp": self.timestamp.isoformat(),
            "position_type": self.position_type.value,
            "quantity": self.quantity,
            "price": self.price,
            "leverage": self.leverage,
            "cost": self.cost,
            "is_open": self.is_open
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Trade':
        """从字典创建"""
        return cls(
            trade_id=data["trade_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            position_type=PositionType(data["position_type"]),
            quantity=data["quantity"],
            price=data["price"],
            leverage=data["leverage"],
            cost=data["cost"],
            is_open=data["is_open"]
        )


@dataclass
class Position:
    """持仓信息"""
    position_type: PositionType
    total_quantity: float  # 总持仓数量
    avg_price: float  # 平均成本价
    avg_leverage: float  # 平均杠杆率
    total_margin: float  # 总保证金
    unrealized_pnl: float  # 未实现盈亏

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "position_type": self.position_type.value,
            "total_quantity": self.total_quantity,
            "avg_price": self.avg_price,
            "avg_leverage": self.avg_leverage,
            "total_margin": self.total_margin,
            "unrealized_pnl": self.unrealized_pnl
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Position':
        """从字典创建"""
        return cls(
            position_type=PositionType(data["position_type"]),
            total_quantity=data["total_quantity"],
            avg_price=data["avg_price"],
            avg_leverage=data["avg_leverage"],
            total_margin=data["total_margin"],
            unrealized_pnl=data["unrealized_pnl"]
        )


class TradingSimulator:
    """模拟交易器"""

    def __init__(self, initial_balance: float = 10000.0, persist_file: str = "trading_state.json"):
        """
        初始化模拟交易器

        Args:
            initial_balance: 初始资金（仅在首次创建时使用）
            persist_file: 持久化文件路径
        """
        self.persist_file = persist_file

        # 尝试从文件加载状态
        if os.path.exists(persist_file):
            self._load_state()
            print(f"✓ 从文件加载交易状态: {persist_file}")
        else:
            # 初始化新状态
            self.initial_balance = initial_balance
            self.balance = initial_balance  # 可用余额
            self.trades: List[Trade] = []  # 交易历史
            self.trade_counter = 0  # 交易计数器
            self.long_position: Optional[Position] = None  # 多头仓位
            self.short_position: Optional[Position] = None  # 空头仓位
            self._save_state()
            print(f"✓ 创建新的交易状态: {persist_file}")

    def buy_long(self, quantity: float, price: float, leverage: int = 1) -> Dict:
        """
        做多（买入开多仓）

        Args:
            quantity: 买入数量
            price: 买入价格
            leverage: 杠杆倍率 (1-5)

        Returns:
            交易结果字典
        """
        return self._open_position(PositionType.LONG, quantity, price, leverage)

    def buy_short(self, quantity: float, price: float, leverage: int = 1) -> Dict:
        """
        做空（卖出开空仓）

        Args:
            quantity: 卖出数量
            price: 卖出价格
            leverage: 杠杆倍率 (1-5)

        Returns:
            交易结果字典
        """
        return self._open_position(PositionType.SHORT, quantity, price, leverage)

    def sell_long(self, quantity: float, price: float) -> Dict:
        """
        平多仓（卖出平多）

        Args:
            quantity: 卖出数量
            price: 卖出价格

        Returns:
            交易结果字典
        """
        return self._close_position(PositionType.LONG, quantity, price)

    def sell_short(self, quantity: float, price: float) -> Dict:
        """
        平空仓（买入平空）

        Args:
            quantity: 买入数量
            price: 买入价格

        Returns:
            交易结果字典
        """
        return self._close_position(PositionType.SHORT, quantity, price)

    def _open_position(self, position_type: PositionType, quantity: float, price: float, leverage: int) -> Dict:
        """
        开仓内部方法

        Args:
            position_type: 仓位类型
            quantity: 数量
            price: 价格
            leverage: 杠杆倍率

        Returns:
            交易结果字典
        """
        # 验证杠杆倍率
        if leverage < 1 or leverage > 5:
            return {
                "success": False,
                "error": "杠杆倍率必须在1-5之间",
                "balance": self.balance
            }

        # 计算所需保证金（实际花费）
        total_value = quantity * price
        margin_required = total_value / leverage

        # 检查余额是否足够
        if margin_required > self.balance:
            return {
                "success": False,
                "error": f"余额不足，需要 {margin_required:.2f}，当前余额 {self.balance:.2f}",
                "balance": self.balance
            }

        # 扣除保证金
        self.balance -= margin_required

        # 记录交易
        self.trade_counter += 1
        trade = Trade(
            trade_id=self.trade_counter,
            timestamp=datetime.now(),
            position_type=position_type,
            quantity=quantity,
            price=price,
            leverage=leverage,
            cost=margin_required,
            is_open=True
        )
        self.trades.append(trade)

        # 更新持仓
        self._update_position_on_open(position_type, quantity, price, leverage, margin_required)

        # 保存状态
        self._save_state()

        return {
            "success": True,
            "trade_id": trade.trade_id,
            "position_type": position_type.value,
            "quantity": quantity,
            "price": price,
            "leverage": leverage,
            "cost": margin_required,
            "balance": self.balance
        }

    def _close_position(self, position_type: PositionType, quantity: float, price: float) -> Dict:
        """
        平仓内部方法

        Args:
            position_type: 仓位类型
            quantity: 数量
            price: 价格

        Returns:
            交易结果字典
        """
        # 获取对应的持仓
        position = self.long_position if position_type == PositionType.LONG else self.short_position

        if not position:
            return {
                "success": False,
                "error": f"没有{position_type.value}持仓",
                "balance": self.balance
            }

        if quantity > position.total_quantity:
            return {
                "success": False,
                "error": f"平仓数量超过持仓数量，当前持仓 {position.total_quantity}",
                "balance": self.balance
            }

        # 计算盈亏
        if position_type == PositionType.LONG:
            # 做多：卖出价 - 买入价
            pnl_per_unit = (price - position.avg_price) * position.avg_leverage
        else:
            # 做空：买入价 - 卖出价
            pnl_per_unit = (position.avg_price - price) * position.avg_leverage

        total_pnl = pnl_per_unit * quantity

        # 计算释放的保证金
        margin_to_release = (quantity / position.total_quantity) * position.total_margin

        # 返还保证金和盈亏
        self.balance += margin_to_release + total_pnl

        # 记录交易
        self.trade_counter += 1
        trade = Trade(
            trade_id=self.trade_counter,
            timestamp=datetime.now(),
            position_type=position_type,
            quantity=quantity,
            price=price,
            leverage=int(position.avg_leverage),
            cost=margin_to_release,
            is_open=False
        )
        self.trades.append(trade)

        # 更新持仓
        self._update_position_on_close(position_type, quantity, margin_to_release)

        # 保存状态
        self._save_state()

        return {
            "success": True,
            "trade_id": trade.trade_id,
            "position_type": position_type.value,
            "quantity": quantity,
            "price": price,
            "pnl": total_pnl,
            "margin_released": margin_to_release,
            "balance": self.balance
        }

    def _update_position_on_open(self, position_type: PositionType, quantity: float,
                                  price: float, leverage: int, margin: float):
        """
        开仓时更新持仓信息

        Args:
            position_type: 仓位类型
            quantity: 数量
            price: 价格
            leverage: 杠杆倍率
            margin: 保证金
        """
        if position_type == PositionType.LONG:
            if self.long_position is None:
                # 新建多头仓位
                self.long_position = Position(
                    position_type=PositionType.LONG,
                    total_quantity=quantity,
                    avg_price=price,
                    avg_leverage=float(leverage),
                    total_margin=margin,
                    unrealized_pnl=0.0
                )
            else:
                # 加仓：计算新的平均价格和平均杠杆
                old_pos = self.long_position
                total_qty = old_pos.total_quantity + quantity

                # 加权平均价格
                self.long_position.avg_price = (
                    (old_pos.avg_price * old_pos.total_quantity + price * quantity) / total_qty
                )

                # 加权平均杠杆
                self.long_position.avg_leverage = (
                    (old_pos.avg_leverage * old_pos.total_quantity + leverage * quantity) / total_qty
                )

                self.long_position.total_quantity = total_qty
                self.long_position.total_margin += margin
        else:
            if self.short_position is None:
                # 新建空头仓位
                self.short_position = Position(
                    position_type=PositionType.SHORT,
                    total_quantity=quantity,
                    avg_price=price,
                    avg_leverage=float(leverage),
                    total_margin=margin,
                    unrealized_pnl=0.0
                )
            else:
                # 加仓
                old_pos = self.short_position
                total_qty = old_pos.total_quantity + quantity

                self.short_position.avg_price = (
                    (old_pos.avg_price * old_pos.total_quantity + price * quantity) / total_qty
                )

                self.short_position.avg_leverage = (
                    (old_pos.avg_leverage * old_pos.total_quantity + leverage * quantity) / total_qty
                )

                self.short_position.total_quantity = total_qty
                self.short_position.total_margin += margin

    def _update_position_on_close(self, position_type: PositionType, quantity: float, margin_released: float):
        """
        平仓时更新持仓信息

        Args:
            position_type: 仓位类型
            quantity: 平仓数量
            margin_released: 释放的保证金
        """
        if position_type == PositionType.LONG:
            self.long_position.total_quantity -= quantity
            self.long_position.total_margin -= margin_released

            # 如果仓位清空，删除持仓记录
            if self.long_position.total_quantity <= 0:
                self.long_position = None
        else:
            self.short_position.total_quantity -= quantity
            self.short_position.total_margin -= margin_released

            if self.short_position.total_quantity <= 0:
                self.short_position = None

    def get_account_info(self, current_price: float) -> Dict:
        """
        获取当前账户信息

        Args:
            current_price: 当前市场价格（用于计算未实现盈亏）

        Returns:
            账户信息字典
        """
        # 计算未实现盈亏
        long_unrealized_pnl = 0.0
        short_unrealized_pnl = 0.0

        if self.long_position:
            pnl_per_unit = (current_price - self.long_position.avg_price) * self.long_position.avg_leverage
            long_unrealized_pnl = pnl_per_unit * self.long_position.total_quantity
            self.long_position.unrealized_pnl = long_unrealized_pnl

        if self.short_position:
            pnl_per_unit = (self.short_position.avg_price - current_price) * self.short_position.avg_leverage
            short_unrealized_pnl = pnl_per_unit * self.short_position.total_quantity
            self.short_position.unrealized_pnl = short_unrealized_pnl

        total_unrealized_pnl = long_unrealized_pnl + short_unrealized_pnl
        total_margin = 0.0
        if self.long_position:
            total_margin += self.long_position.total_margin
        if self.short_position:
            total_margin += self.short_position.total_margin

        # 总权益 = 可用余额 + 占用保证金 + 未实现盈亏
        total_equity = self.balance + total_margin + total_unrealized_pnl

        return {
            "balance": self.balance,
            "total_margin": total_margin,
            "total_unrealized_pnl": total_unrealized_pnl,
            "total_equity": total_equity,
            "long_position": self._format_position(self.long_position) if self.long_position else None,
            "short_position": self._format_position(self.short_position) if self.short_position else None
        }

    def _format_position(self, position: Position) -> Dict:
        """
        格式化持仓信息为字典

        Args:
            position: 持仓对象

        Returns:
            持仓信息字典
        """
        return {
            "position_type": position.position_type.value,
            "total_quantity": position.total_quantity,
            "avg_price": position.avg_price,
            "avg_leverage": position.avg_leverage,
            "total_margin": position.total_margin,
            "unrealized_pnl": position.unrealized_pnl
        }

    def print_account_info(self, current_price: float):
        """
        打印当前账户信息

        Args:
            current_price: 当前市场价格
        """
        info = self.get_account_info(current_price)

        print("\n" + "=" * 80)
        print("账户信息")
        print("=" * 80)
        print(f"初始资金: {self.initial_balance:.2f}")
        print(f"可用余额: {info['balance']:.2f}")
        print(f"占用保证金: {info['total_margin']:.2f}")
        print(f"未实现盈亏: {info['total_unrealized_pnl']:.2f}")
        print(f"总权益: {info['total_equity']:.2f}")
        print(f"总收益率: {((info['total_equity'] - self.initial_balance) / self.initial_balance * 100):.2f}%")

        if info['long_position']:
            print("\n" + "-" * 80)
            print("多头仓位:")
            pos = info['long_position']
            print(f"  持仓数量: {pos['total_quantity']:.4f}")
            print(f"  平均成本: {pos['avg_price']:.2f}")
            print(f"  平均杠杆: {pos['avg_leverage']:.2f}x")
            print(f"  占用保证金: {pos['total_margin']:.2f}")
            print(f"  未实现盈亏: {pos['unrealized_pnl']:.2f}")
            print(f"  收益率: {(pos['unrealized_pnl'] / pos['total_margin'] * 100):.2f}%")

        if info['short_position']:
            print("\n" + "-" * 80)
            print("空头仓位:")
            pos = info['short_position']
            print(f"  持仓数量: {pos['total_quantity']:.4f}")
            print(f"  平均成本: {pos['avg_price']:.2f}")
            print(f"  平均杠杆: {pos['avg_leverage']:.2f}x")
            print(f"  占用保证金: {pos['total_margin']:.2f}")
            print(f"  未实现盈亏: {pos['unrealized_pnl']:.2f}")
            print(f"  收益率: {(pos['unrealized_pnl'] / pos['total_margin'] * 100):.2f}%")

        print("=" * 80)

    def _save_state(self):
        """保存交易状态到文件"""
        state = {
            "initial_balance": self.initial_balance,
            "balance": self.balance,
            "trade_counter": self.trade_counter,
            "trades": [trade.to_dict() for trade in self.trades],
            "long_position": self.long_position.to_dict() if self.long_position else None,
            "short_position": self.short_position.to_dict() if self.short_position else None
        }

        with open(self.persist_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)

    def _load_state(self):
        """从文件加载交易状态"""
        with open(self.persist_file, 'r', encoding='utf-8') as f:
            state = json.load(f)

        self.initial_balance = state["initial_balance"]
        self.balance = state["balance"]
        self.trade_counter = state["trade_counter"]
        self.trades = [Trade.from_dict(t) for t in state["trades"]]
        self.long_position = Position.from_dict(state["long_position"]) if state["long_position"] else None
        self.short_position = Position.from_dict(state["short_position"]) if state["short_position"] else None
