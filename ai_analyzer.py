"""
AI金融分析接口
使用Claude API分析市场数据并给出交易建议
"""

import anthropic
import os
from typing import Optional


class AIAnalyzer:
    """AI金融分析器"""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        初始化AI分析器

        Args:
            api_key: Anthropic API密钥，如果不提供则从环境变量ANTHROPIC_API_KEY读取
            base_url: API基础URL，用于自定义API端点（可选）
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("请提供Anthropic API密钥或设置环境变量ANTHROPIC_API_KEY")

        # 根据是否提供base_url来初始化客户端
        if base_url:
            self.client = anthropic.Anthropic(api_key=self.api_key, base_url=base_url)
        else:
            self.client = anthropic.Anthropic(api_key=self.api_key)

        self.system_prompt = """你是一位专业的加密货币金融分析师，具有丰富的技术分析和市场分析经验。

你的职责是：
1. 仔细分析提供的市场数据，包括成交明细、买卖盘口和K线数据
2. 从技术分析角度评估市场趋势、支撑位、阻力位等关键指标
3. 综合考虑成交量、价格走势、买卖盘力量等因素
4. 给出明确的交易建议：BUY（买入）或 SELL（卖出） 并给出你认为操作的置信度
5. 提供详细的分析理由，解释你的判断依据

请保持客观、专业，基于数据做出理性分析。"""

    def analyze(self, market_data: str, model: str = "claude-sonnet-4-5-20250929") -> dict:
        """
        分析市场数据并给出交易建议

        Args:
            market_data: 格式化的市场数据文本
            model: 使用的Claude模型

        Returns:
            包含分析结果的字典，包含decision和analysis字段
        """
        user_message = f"{market_data}\n\n请你分析这份数据并给出你会buy还是sell并给出你认为操作的置信度，辅以文字分析"

        try:
            message = self.client.messages.create(
                model=model,
                max_tokens=2000,
                system=self.system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": user_message
                    }
                ]
            )

            # 提取响应内容
            response_text = message.content[0].text

            return {
                "success": True,
                "decision": self._extract_decision(response_text),
                "analysis": response_text,
                "model": model,
                "usage": {
                    "input_tokens": message.usage.input_tokens,
                    "output_tokens": message.usage.output_tokens
                }
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "decision": None,
                "analysis": None
            }

    def _extract_decision(self, text: str) -> Optional[str]:
        """
        从分析文本中提取交易决策

        Args:
            text: AI返回的分析文本

        Returns:
            "BUY" 或 "SELL"，如果无法确定则返回None
        """
        text_upper = text.upper()

        # 查找明确的BUY或SELL关键词
        buy_keywords = ["BUY", "买入", "建议买入", "推荐买入"]
        sell_keywords = ["SELL", "卖出", "建议卖出", "推荐卖出"]

        has_buy = any(keyword in text_upper for keyword in buy_keywords)
        has_sell = any(keyword in text_upper for keyword in sell_keywords)

        if has_buy and not has_sell:
            return "BUY"
        elif has_sell and not has_buy:
            return "SELL"
        else:
            # 如果同时包含或都不包含，返回None
            return None
