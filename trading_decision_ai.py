"""
交易决策AI助手
读取市场分析结果和账户信息，做出交易决策
"""

import anthropic
import os
import json
from typing import Optional, Dict


class TradingDecisionAI:
    """交易决策AI助手"""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        初始化交易决策AI

        Args:
            api_key: Anthropic API密钥
            base_url: API基础URL（可选）
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("请提供Anthropic API密钥或设置环境变量ANTHROPIC_API_KEY")

        if base_url:
            self.client = anthropic.Anthropic(api_key=self.api_key, base_url=base_url)
        else:
            self.client = anthropic.Anthropic(api_key=self.api_key)

        self.system_prompt = """你是一位专业的加密货币交易执行助手，擅长中长期交易策略。

你的职责是：
1. 阅读市场分析师提供的分析报告，理解其中长期趋势判断
2. 查看当前账户的资金和持仓情况
3. 根据分析建议、置信度和账户状态，做出具体的交易决策
4. 以JSON格式输出交易指令

可用的交易操作：
- buy_long: 做多（开多仓），参数：quantity（数量）, price（价格）, leverage（杠杆1-5）
- buy_short: 做空（开空仓），参数：quantity（数量）, price（价格）, leverage（杠杆1-5）
- sell_long: 平多仓，参数：quantity（数量）, price（价格）
- sell_short: 平空仓，参数：quantity（数量）, price（价格）
- hold: 不操作（观望等待）

输出格式要求：
必须返回一个JSON对象，格式如下：
{
    "action": "操作类型（buy_long/buy_short/sell_long/sell_short/hold）",
    "params": {
        "quantity": 数量（浮点数），
        "price": 价格（浮点数），
        "leverage": 杠杆倍率（1-5的整数，仅开仓时需要）
    },
    "reason": "决策理由（简短说明）"
}

决策原则（中期视角）：
1. 如果分析建议HOLD或置信度<70%，选择hold观望，耐心等待更好机会
2. 如果分析建议BUY且置信度≥70%且当前无多仓，考虑开多仓
3. 如果分析建议SELL且置信度≥70%且当前有多仓，考虑平多仓
4. 如果分析建议SELL且置信度≥70%且当前无空仓，考虑开空仓
5. 如果分析建议BUY且置信度≥70%且当前有空仓，考虑平空仓
6. 根据置信度和账户余额，合理分配仓位大小（建议每次使用10-30%可用余额）
7. 杠杆倍率建议2-3倍，避免过高风险
8. 确保不超过可用余额

重要：采用中期策略，不追求频繁交易，在高质量信号出现时才操作。

请严格按照JSON格式输出，不要添加任何其他文字。"""

    def make_decision(self, analysis_result: str, account_info: Dict,
                     model: str = "claude-sonnet-4-5-20250929") -> Dict:
        """
        根据分析结果和账户信息做出交易决策

        Args:
            analysis_result: 市场分析结果文本
            account_info: 账户信息字典
            model: 使用的Claude模型

        Returns:
            决策结果字典
        """
        # 构建用户消息
        user_message = self._build_user_message(analysis_result, account_info)

        try:
            message = self.client.messages.create(
                model=model,
                max_tokens=1000,
                messages=[
                    {
                        "role": "user",
                        "content": self.system_prompt + "\n\n" + user_message
                    }
                ]
            )

            # 提取响应内容（过滤掉thinking blocks，只获取text blocks）
            text_blocks = [block for block in message.content if hasattr(block, 'text')]
            if not text_blocks:
                raise ValueError("API响应中没有找到文本内容")
            response_text = text_blocks[0].text.strip()

            # 解析JSON
            decision = self._parse_decision(response_text)

            return {
                "success": True,
                "decision": decision,
                "raw_response": response_text,
                "usage": {
                    "input_tokens": message.usage.input_tokens,
                    "output_tokens": message.usage.output_tokens
                }
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "decision": None
            }

    def _build_user_message(self, analysis_result: str, account_info: Dict) -> str:
        """
        构建发送给AI的用户消息

        Args:
            analysis_result: 市场分析结果
            account_info: 账户信息

        Returns:
            格式化的用户消息
        """
        message = f"""# 市场分析报告

{analysis_result}

# 当前账户状态

可用余额: {account_info['balance']:.2f}
占用保证金: {account_info['total_margin']:.2f}
未实现盈亏: {account_info['total_unrealized_pnl']:.2f}
总权益: {account_info['total_equity']:.2f}
"""

        if account_info['long_position']:
            pos = account_info['long_position']
            message += f"""
多头仓位:
  持仓数量: {pos['total_quantity']:.4f}
  平均成本: {pos['avg_price']:.2f}
  平均杠杆: {pos['avg_leverage']:.2f}x
  占用保证金: {pos['total_margin']:.2f}
  未实现盈亏: {pos['unrealized_pnl']:.2f}
"""

        if account_info['short_position']:
            pos = account_info['short_position']
            message += f"""
空头仓位:
  持仓数量: {pos['total_quantity']:.4f}
  平均成本: {pos['avg_price']:.2f}
  平均杠杆: {pos['avg_leverage']:.2f}x
  占用保证金: {pos['total_margin']:.2f}
  未实现盈亏: {pos['unrealized_pnl']:.2f}
"""

        message += "\n请根据以上信息，做出交易决策并以JSON格式输出。"
        return message

    def _parse_decision(self, response_text: str) -> Dict:
        """
        解析AI返回的JSON决策

        Args:
            response_text: AI返回的文本

        Returns:
            解析后的决策字典
        """
        text = response_text.strip()

        # 尝试从markdown代码块中提取JSON
        if "```json" in text:
            # 找到```json和```之间的内容
            start = text.find("```json") + 7
            end = text.find("```", start)
            if end != -1:
                text = text[start:end].strip()
        elif "```" in text:
            # 找到```和```之间的内容
            start = text.find("```") + 3
            end = text.find("```", start)
            if end != -1:
                text = text[start:end].strip()
        else:
            # 尝试找到JSON对象的开始和结束
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1 and end > start:
                text = text[start:end+1]

        # 解析JSON
        try:
            decision = json.loads(text)
            return decision
        except json.JSONDecodeError as e:
            raise ValueError(f"无法解析JSON决策: {e}\n原始文本: {response_text}")
