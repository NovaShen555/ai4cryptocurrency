"""
自动交易系统使用示例
演示完整的AI驱动的自动交易流程
"""

from auto_trading_system import AutoTradingSystem
import time

# API密钥配置
crypto_api_key = "517c9f7626bd460b8b48e8faa15711d2-infoway"
anthropic_api_key = "sk-k0nw6VGbaCgz9QRFASNPNwopueAzZmw2CDDOExLAQpTCaucj"
base_url = "https://new.motchat.com/"


def main():
    """主函数：运行自动交易系统"""
    print("=" * 80)
    print("AI自动交易系统")
    print("=" * 80)

    # 初始化自动交易系统
    print("\n初始化系统...")
    system = AutoTradingSystem(
        crypto_api_key=crypto_api_key,
        anthropic_api_key=anthropic_api_key,
        initial_balance=10000.0,
        base_url=base_url
    )
    print("✓ 系统初始化完成")
    run_times = 0

    while(True):
        run_times += 1
        print("\n\n" + "#" * 80)
        print(f"# 第{run_times}次交易周期")
        print("#" * 80)

        result_1 = system.run_trading_cycle("ETHUSDT")

        if result_1["success"]:
            print(f"\n✓ 第{run_times}次交易周期完成")
        else:
            print(f"\n✗ 第{run_times}次交易周期失败: {result_1.get('error', '未知错误')}")

        # 等待一段时间（模拟）
        print("\n\n等待下一个交易周期...")
        time.sleep(300)  # 等待5分钟


if __name__ == "__main__":
    main()



