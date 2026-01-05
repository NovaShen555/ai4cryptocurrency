"""
Flask Web应用
展示交易历史、价格折线图，并提供定时自动交易功能
"""

from flask import Flask, render_template, jsonify
from auto_trading_system import AutoTradingSystem
from threading import Thread
import time
import json
import os
from datetime import datetime

app = Flask(__name__)

# 全局变量
trading_system = None
trading_history = []
price_history = []
is_running = False

# API密钥配置
crypto_api_key = "517c9f7626bd460b8b48e8faa15711d2-infoway"
anthropic_api_key = "sk-k0nw6VGbaCgz9QRFASNPNwopueAzZmw2CDDOExLAQpTCaucj"
base_url = "https://new.motchat.com/"


def init_trading_system():
    """初始化交易系统"""
    global trading_system
    trading_system = AutoTradingSystem(
        crypto_api_key=crypto_api_key,
        anthropic_api_key=anthropic_api_key,
        initial_balance=10000.0,
        base_url=base_url
    )
    load_history()


def load_history():
    """从持久化文件加载历史数据"""
    global trading_history, price_history

    # 加载交易历史
    if os.path.exists("trading_state.json"):
        with open("trading_state.json", "r", encoding="utf-8") as f:
            state = json.load(f)
            trades = state.get("trades", [])

            trading_history = []
            for trade in trades:
                trading_history.append({
                    "trade_id": trade["trade_id"],
                    "timestamp": trade["timestamp"],
                    "position_type": trade["position_type"],
                    "quantity": trade["quantity"],
                    "price": trade["price"],
                    "leverage": trade["leverage"],
                    "cost": trade["cost"],
                    "is_open": trade["is_open"]
                })

    # 加载价格历史
    if os.path.exists("price_history.json"):
        with open("price_history.json", "r", encoding="utf-8") as f:
            price_history = json.load(f)


def save_price_history(price, timestamp):
    """保存价格历史"""
    global price_history
    price_history.append({
        "timestamp": timestamp,
        "price": price
    })

    # 只保留最近100条记录
    if len(price_history) > 100:
        price_history = price_history[-100:]

    with open("price_history.json", "w", encoding="utf-8") as f:
        json.dump(price_history, f, ensure_ascii=False, indent=2)


def trading_task():
    """定时交易任务"""
    global is_running, trading_history

    while is_running:
        try:
            print(f"\n{'='*80}")
            print(f"执行定时交易任务 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*80}")

            # 执行交易周期
            result = trading_system.run_trading_cycle("ETHUSDT")

            if result["success"]:
                # 重新加载历史数据
                load_history()

                # 保存当前价格
                if "trade" in result and result["trade"].get("success"):
                    trade_info = result["trade"]
                    if "price" in trade_info:
                        save_price_history(
                            trade_info["price"],
                            datetime.now().isoformat()
                        )

                print(f"✓ 交易周期完成")
            else:
                print(f"✗ 交易周期失败: {result.get('error', '未知错误')}")

        except Exception as e:
            print(f"✗ 交易任务出错: {str(e)}")

        # 等待10分钟
        print(f"\n等待10分钟后执行下一次交易...")
        time.sleep(600)  # 600秒 = 10分钟


@app.route('/')
def index():
    """主页"""
    return render_template('index.html')


@app.route('/api/status')
def get_status():
    """获取系统状态"""
    return jsonify({
        "is_running": is_running,
        "timestamp": datetime.now().isoformat()
    })


@app.route('/api/account')
def get_account():
    """获取账户信息"""
    try:
        # 获取当前价格
        current_price = trading_system.data_formatter.get_current_price("ETHUSDT")
        account_info = trading_system.simulator.get_account_info(current_price)

        return jsonify({
            "success": True,
            "current_price": current_price,
            "account": account_info
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })


@app.route('/api/history')
def get_history():
    """获取交易历史"""
    return jsonify({
        "success": True,
        "trades": trading_history
    })


@app.route('/api/price_history')
def get_price_history():
    """获取价格历史"""
    return jsonify({
        "success": True,
        "prices": price_history
    })


@app.route('/api/start')
def start_trading():
    """启动定时交易"""
    global is_running

    if not is_running:
        is_running = True
        thread = Thread(target=trading_task, daemon=True)
        thread.start()
        return jsonify({"success": True, "message": "定时交易已启动"})
    else:
        return jsonify({"success": False, "message": "定时交易已在运行中"})


@app.route('/api/stop')
def stop_trading():
    """停止定时交易"""
    global is_running

    if is_running:
        is_running = False
        return jsonify({"success": True, "message": "定时交易已停止"})
    else:
        return jsonify({"success": False, "message": "定时交易未在运行"})


if __name__ == '__main__':
    # 初始化交易系统
    print("初始化交易系统...")
    init_trading_system()
    print("✓ 交易系统初始化完成")

    # 启动Flask应用
    print("\n启动Web服务器...")
    print("访问 http://127.0.0.1:5000 查看交易面板")
    app.run(debug=True, host='0.0.0.0', port=5000)
