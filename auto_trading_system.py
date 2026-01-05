"""
自动交易系统
整合市场数据获取、AI分析、交易决策和模拟交易执行
"""

from data_formatter import DataFormatter
from ai_analyzer import AIAnalyzer
from trading_decision_ai import TradingDecisionAI
from trading_simulator import TradingSimulator
import time


class AutoTradingSystem:
    """自动交易系统"""

    def __init__(self, crypto_api_key: str, anthropic_api_key: str,
                 initial_balance: float = 10000.0, base_url: str = None):
        """
        初始化自动交易系统

        Args:
            crypto_api_key: 加密货币数据API密钥
            anthropic_api_key: Anthropic API密钥
            initial_balance: 初始资金
            base_url: Anthropic API基础URL（可选）
        """
        self.data_formatter = DataFormatter(crypto_api_key)
        self.market_analyzer = AIAnalyzer(api_key=anthropic_api_key, base_url=base_url)
        self.decision_ai = TradingDecisionAI(api_key=anthropic_api_key, base_url=base_url)
        self.simulator = TradingSimulator(initial_balance=initial_balance)

    def run_trading_cycle(self, symbol: str):
        """
        运行一次完整的交易周期

        Args:
            symbol: 交易产品代码

        Returns:
            交易周期结果字典
        """
        print("\n" + "=" * 80)
        print(f"开始交易周期 - {symbol}")
        print("=" * 80)

        # 步骤1: 获取市场数据
        print("\n[步骤1] 获取市场数据...")
        market_data = self.data_formatter.format_all_data(symbol)
        print(f"✓ 市场数据获取完成，数据长度: {len(market_data)} 字符")

        # 步骤2: AI分析市场
        print("\n[步骤2] AI分析市场数据...")
        analysis_result = self.market_analyzer.analyze(market_data)

        if not analysis_result["success"]:
            print(f"✗ 市场分析失败: {analysis_result['error']}")
            return {"success": False, "error": "市场分析失败"}

        print(f"✓ 市场分析完成")
        print(f"  决策建议: {analysis_result['decision']}")
        print(f"  Token使用: 输入={analysis_result['usage']['input_tokens']}, "
              f"输出={analysis_result['usage']['output_tokens']}")

        # 步骤3: 获取当前价格和账户信息
        print("\n[步骤3] 获取当前价格和账户信息...")
        current_price = self.data_formatter.get_current_price(symbol)
        print(f"✓ 当前价格: {current_price:.2f}")

        account_info = self.simulator.get_account_info(current_price)
        print(f"✓ 账户余额: {account_info['balance']:.2f}")
        print(f"  总权益: {account_info['total_equity']:.2f}")

        # 步骤4: AI做出交易决策
        print("\n[步骤4] AI做出交易决策...")
        decision_result = self.decision_ai.make_decision(
            analysis_result['analysis'],
            account_info
        )

        if not decision_result["success"]:
            print(f"✗ 决策失败: {decision_result['error']}")
            return {"success": False, "error": "决策失败"}

        decision = decision_result['decision']
        print(f"✓ 决策完成")
        print(f"  操作: {decision['action']}")
        print(f"  理由: {decision['reason']}")
        print(f"  Token使用: 输入={decision_result['usage']['input_tokens']}, "
              f"输出={decision_result['usage']['output_tokens']}")

        # 步骤5: 执行交易前获取最新价格
        print("\n[步骤5] 执行交易...")
        if decision['action'] != 'hold':
            print("  获取最新价格...")
            execution_price = self.data_formatter.get_current_price(symbol)
            print(f"  ✓ 最新价格: {execution_price:.2f}")
        else:
            execution_price = current_price

        trade_result = self._execute_trade(decision, symbol, execution_price)

        if trade_result["success"]:
            print(f"✓ 交易执行成功")
            if decision['action'] != 'hold':
                print(f"  交易ID: {trade_result.get('trade_id', 'N/A')}")
                if 'cost' in trade_result:
                    print(f"  花费/释放保证金: {trade_result['cost']:.2f}")
                if 'pnl' in trade_result:
                    print(f"  实现盈亏: {trade_result['pnl']:.2f}")
                print(f"  当前余额: {trade_result['balance']:.2f}")
        else:
            print(f"✗ 交易执行失败: {trade_result.get('error', '未知错误')}")

        # 步骤6: 显示最终账户状态
        print("\n[步骤6] 最终账户状态:")
        self.simulator.print_account_info(execution_price)

        return {
            "success": True,
            "analysis": analysis_result,
            "decision": decision_result,
            "trade": trade_result
        }

    def _execute_trade(self, decision: dict, symbol: str, execution_price: float) -> dict:
        """
        执行交易决策

        Args:
            decision: AI决策字典
            symbol: 交易产品代码
            execution_price: 执行价格

        Returns:
            交易结果字典
        """
        action = decision.get('action', 'hold')
        params = decision.get('params', {})

        # 如果决策是hold，直接返回
        if action == 'hold':
            return {
                "success": True,
                "action": "hold",
                "message": "保持观望，不进行交易"
            }

        # 获取参数，使用最新获取的执行价格
        quantity = params.get('quantity', 0)
        leverage = params.get('leverage', 1)

        # 根据action执行相应的交易，使用execution_price
        if action == 'buy_long':
            return self.simulator.buy_long(quantity, execution_price, leverage)
        elif action == 'buy_short':
            return self.simulator.buy_short(quantity, execution_price, leverage)
        elif action == 'sell_long':
            return self.simulator.sell_long(quantity, execution_price)
        elif action == 'sell_short':
            return self.simulator.sell_short(quantity, execution_price)
        else:
            return {
                "success": False,
                "error": f"未知的操作类型: {action}"
            }


