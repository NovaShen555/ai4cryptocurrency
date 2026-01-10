"""
AI金融分析使用示例
演示如何使用AI分析器分析市场数据并获取交易建议
"""

from data_formatter import DataFormatter
from ai_analyzer import AIAnalyzer

# API密钥
crypto_api_key = "f2c603977976434f898e0eae3ebf3159-infoway"
# Anthropic API密钥
anthropic_api_key = "sk-k0nw6VGbaCgz9QRFASNPNwopueAzZmw2CDDOExLAQpTCaucj"


def main():
    """主函数：获取市场数据并进行AI分析"""
    print("=" * 80)
    print("AI加密货币交易分析系统")
    print("=" * 80)

    # 1. 获取并格式化市场数据
    print("\n[步骤1] 正在获取ETHUSDT的市场数据...")
    formatter = DataFormatter(crypto_api_key)
    market_data = formatter.format_all_data("ETHUSDT")

    print("市场数据获取完成！")
    print(f"数据长度: {len(market_data)} 字符")

    # 可选：保存原始数据
    with open("market_data.txt", "w", encoding="utf-8") as f:
        f.write(market_data)
    print("市场数据已保存到: market_data.txt")

    # 2. 使用AI分析数据
    print("\n[步骤2] 正在使用AI分析市场数据...")

    try:
        # 初始化AI分析器
        analyzer = AIAnalyzer(api_key=anthropic_api_key,
                              base_url="https://new.motchat.com/"
                              )

        # 进行分析
        result = analyzer.analyze(market_data)

        if result["success"]:
            print("\n" + "=" * 80)
            print("AI分析结果")
            print("=" * 80)
            print(f"\n交易决策: {result['decision']}")
            print(f"\n详细分析:\n{result['analysis']}")
            print(f"\n使用模型: {result['model']}")
            print(f"Token使用: 输入={result['usage']['input_tokens']}, "
                  f"输出={result['usage']['output_tokens']}")

            # 保存分析结果
            with open("ai_analysis_result.txt", "w", encoding="utf-8") as f:
                f.write(f"交易决策: {result['decision']}\n\n")
                f.write(f"详细分析:\n{result['analysis']}\n\n")
                f.write(f"使用模型: {result['model']}\n")
                f.write(f"Token使用: 输入={result['usage']['input_tokens']}, "
                       f"输出={result['usage']['output_tokens']}\n")

            print("\n分析结果已保存到: ai_analysis_result.txt")
        else:
            print(f"\n分析失败: {result['error']}")

    except ValueError as e:
        print(f"\n错误: {e}")
        print("\n请设置环境变量 ANTHROPIC_API_KEY 或在代码中提供API密钥")
    except Exception as e:
        print(f"\n发生错误: {e}")

    print("\n" + "=" * 80)
    print("分析完成")
    print("=" * 80)


if __name__ == "__main__":
    main()
