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
trading_history_normal = []
trading_history_reverse = []
price_history = []
equity_history_normal = []
equity_history_reverse = []
is_running = False
latest_ai_responses = {
    "analysis": None,
    "decision": None,
    "timestamp": None
}
system_logs = []  # 存储系统日志，最多300条

# API密钥配置
crypto_api_key = "151eb73352514d528b955d8117e9cda3-infoway"
anthropic_api_key = "sk-k0nw6VGbaCgz9QRFASNPNwopueAzZmw2CDDOExLAQpTCaucj"
base_url = "https://new.motchat.com/"


def add_log(message: str):
    """添加日志到系统日志列表"""
    global system_logs
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"[{timestamp}] {message}"
    system_logs.append(log_entry)

    # 只保留最新的300条日志
    if len(system_logs) > 300:
        system_logs = system_logs[-300:]

    # 同时打印到控制台
    print(message)


def init_trading_system():
    """初始化交易系统"""
    global trading_system
    trading_system = AutoTradingSystem(
        crypto_api_key=crypto_api_key,
        anthropic_api_key=anthropic_api_key,
        initial_balance=10000.0,
        base_url=base_url,
        log_callback=add_log  # 传递日志回调函数
    )
    load_history()


def load_history():
    """从持久化文件加载历史数据"""
    global trading_history_normal, trading_history_reverse, price_history, equity_history_normal, equity_history_reverse

    # 加载正向交易历史
    if os.path.exists("trading_state_normal.json"):
        with open("trading_state_normal.json", "r", encoding="utf-8") as f:
            state = json.load(f)
            trades = state.get("trades", [])

            trading_history_normal = []
            for trade in trades:
                trading_history_normal.append({
                    "trade_id": trade["trade_id"],
                    "timestamp": trade["timestamp"],
                    "position_type": trade["position_type"],
                    "quantity": trade["quantity"],
                    "price": trade["price"],
                    "leverage": trade["leverage"],
                    "cost": trade["cost"],
                    "is_open": trade["is_open"]
                })

    # 加载反向交易历史
    if os.path.exists("trading_state_reverse.json"):
        with open("trading_state_reverse.json", "r", encoding="utf-8") as f:
            state = json.load(f)
            trades = state.get("trades", [])

            trading_history_reverse = []
            for trade in trades:
                trading_history_reverse.append({
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

    # 加载正向总权益历史
    if os.path.exists("equity_history_normal.json"):
        with open("equity_history_normal.json", "r", encoding="utf-8") as f:
            equity_history_normal = json.load(f)

    # 加载反向总权益历史
    if os.path.exists("equity_history_reverse.json"):
        with open("equity_history_reverse.json", "r", encoding="utf-8") as f:
            equity_history_reverse = json.load(f)


def save_price_history(price, equity_normal, equity_reverse, timestamp):
    """保存价格和总权益历史"""
    global price_history, equity_history_normal, equity_history_reverse

    price_history.append({
        "timestamp": timestamp,
        "price": price
    })

    equity_history_normal.append({
        "timestamp": timestamp,
        "equity": equity_normal
    })

    equity_history_reverse.append({
        "timestamp": timestamp,
        "equity": equity_reverse
    })

    # 只保留最近100条记录
    if len(price_history) > 100:
        price_history = price_history[-100:]
    if len(equity_history_normal) > 100:
        equity_history_normal = equity_history_normal[-100:]
    if len(equity_history_reverse) > 100:
        equity_history_reverse = equity_history_reverse[-100:]

    with open("price_history.json", "w", encoding="utf-8") as f:
        json.dump(price_history, f, ensure_ascii=False, indent=2)

    with open("equity_history_normal.json", "w", encoding="utf-8") as f:
        json.dump(equity_history_normal, f, ensure_ascii=False, indent=2)

    with open("equity_history_reverse.json", "w", encoding="utf-8") as f:
        json.dump(equity_history_reverse, f, ensure_ascii=False, indent=2)


def trading_task():
    """定时交易任务"""
    global is_running, latest_ai_responses

    while is_running:
        try:
            add_log(f"\n{'='*80}")
            add_log(f"执行定时交易任务 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            add_log(f"{'='*80}")

            # 执行交易周期
            result = trading_system.run_trading_cycle("ETHUSDT")

            if result["success"]:
                # 保存最新的AI响应
                latest_ai_responses = {
                    "analysis": {
                        "decision": result["analysis"]["decision"],
                        "analysis_text": result["analysis"]["analysis"],
                        "usage": result["analysis"]["usage"]
                    },
                    "decision": {
                        "action": result["decision"]["decision"]["action"],
                        "reason": result["decision"]["decision"]["reason"],
                        "params": result["decision"]["decision"].get("params", {}),
                        "raw_response": result["decision"]["raw_response"],
                        "usage": result["decision"]["usage"]
                    },
                    "timestamp": datetime.now().isoformat()
                }

                # 重新加载历史数据
                load_history()

                # 获取当前价格和两个账户的总权益
                try:
                    current_price = trading_system.data_formatter.get_current_price("ETHUSDT")
                    account_info_normal = trading_system.simulator_normal.get_account_info(current_price)
                    account_info_reverse = trading_system.simulator_reverse.get_account_info(current_price)

                    # 保存价格和两个账户的总权益历史
                    save_price_history(
                        current_price,
                        account_info_normal['total_equity'],
                        account_info_reverse['total_equity'],
                        datetime.now().isoformat()
                    )
                except Exception as e:
                    add_log(f"✗ 保存历史数据失败: {str(e)}")

                add_log(f"✓ 交易周期完成")
            else:
                add_log(f"✗ 交易周期失败: {result.get('error', '未知错误')}")

        except Exception as e:
            add_log(f"✗ 交易任务出错: {str(e)}")

        # 等待10分钟
        add_log(f"\n等待10分钟后执行下一次交易...")
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
        account_info_normal = trading_system.simulator_normal.get_account_info(current_price)
        account_info_reverse = trading_system.simulator_reverse.get_account_info(current_price)

        return jsonify({
            "success": True,
            "current_price": current_price,
            "account_normal": account_info_normal,
            "account_reverse": account_info_reverse
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
        "trades_normal": trading_history_normal,
        "trades_reverse": trading_history_reverse
    })


@app.route('/api/price_history')
def get_price_history():
    """获取价格历史"""
    return jsonify({
        "success": True,
        "prices": price_history
    })


@app.route('/api/equity_history')
def get_equity_history():
    """获取总权益历史"""
    return jsonify({
        "success": True,
        "equities_normal": equity_history_normal,
        "equities_reverse": equity_history_reverse
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


@app.route('/api/ai_responses')
def get_ai_responses():
    """获取最新的AI分析和决策响应"""
    return jsonify({
        "success": True,
        "responses": latest_ai_responses
    })


@app.route('/api/logs')
def get_logs():
    """获取系统日志"""
    return jsonify({
        "success": True,
        "logs": system_logs
    })


if __name__ == '__main__':
    # 初始化交易系统
    print("初始化交易系统...")
    init_trading_system()
    print("✓ 交易系统初始化完成")

    # 启动Flask应用
    print("\n启动Web服务器...")
    print("访问 http://127.0.0.1:5000 查看交易面板")
    app.run(debug=True, host='0.0.0.0', port=5000)
