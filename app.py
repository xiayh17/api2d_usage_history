from flask import Flask, request, render_template, jsonify, redirect, url_for
import requests
import os
import re
from datetime import datetime
Token = os.getenv('Token')

app = Flask(__name__)

DEFAULT_PRICE_PER_POINT = 0.003  # 默认的点数单价

@app.route('/')
def form():
    return render_template('form.html')

def get_recharge_link(api_key):
    # 使用正则表达式从api_key中匹配ck后面的数字
    match = re.search(r'ck(\d+)', api_key)
    if match:
        merchant_id = match.group(1)
        return f"https://www.apiyin.com/merchant/{merchant_id}"
    return "#"

def filter_custom_key_data(custom_key_data):
    """Filter custom_key data based on required keys."""
    required_keys = ['id', 'uid', 'point']
    return {k: v for k, v in custom_key_data.items() if k in required_keys}

def filter_point_usage_data(point_usage_data):
    """Filter point_usage_array data based on required keys."""
    required_keys = ['id', 'uid', 'before_point', 'after_point', 'changed_at']
    return [{k: v for k, v in item.items() if k in required_keys} for item in point_usage_data]

def get_credit_summary(api_key):
    url = "https://oa.api2d.net/dashboard/billing/credit_grants"
    headers = {
        'Authorization': f"Bearer {api_key}"
    }
    response = requests.post(url, headers=headers)
    
    if response.status_code == 200:
        body = response.json()
        
        if 'object' in body and body['object'] == 'credit_summary':
            # Convert the timestamp from milliseconds to seconds
            timestamp_in_seconds = body['expire_at'] / 1000
            
            # Convert to datetime format
            expire_date = datetime.utcfromtimestamp(timestamp_in_seconds)
            
            return {
                'total_granted': body['total_granted'],
                'total_used': body['total_used'],
                'total_available': body['total_available'],
                'expire_at': expire_date
            }
    return None

@app.route('/get_balance_and_history', methods=['POST'])
def get_balance_and_history():
    api_key = request.form['apikey']
    url = f"https://api.api2win.com/custom_key/get?key={api_key}"
    headers = {
        'Authorization': f"Bearer {Token}"
    }
    req_body = {}

    response = requests.post(url, headers=headers, json=req_body)
    
    if response.status_code != 200:
        return 'Request failed', 400

    body = response.json()
    if body.get('code') != 0:
        return 'Request failed', 400

    custom_key_data = filter_custom_key_data(body.get('data', {}).get('custom_key', {}))
    point_usage_data = filter_point_usage_data(body.get('data', {}).get('point_usage_array', []))
    # 如果point_usage_data不为空，取其最后一项的after_point作为总点数
    total_points = point_usage_data[-1]['after_point'] if point_usage_data else 0
    credit_summary = get_credit_summary(api_key)
    recharge_link = get_recharge_link(api_key)
    dates = [item['changed_at'] for item in point_usage_data]
    points = [item['after_point'] for item in point_usage_data]

    return render_template('result.html', dates = dates, points = points, api_key=api_key, custom_key_json=custom_key_data, point_usage_arrays=point_usage_data, price_per_point=DEFAULT_PRICE_PER_POINT, total_points=total_points, credit_summary=credit_summary, recharge_link=recharge_link)

@app.route('/update_price', methods=['POST'])
def update_price():
    new_price = float(request.form.get('new_price', DEFAULT_PRICE_PER_POINT))

    # 假设你想返回基于新价格的 point_usage_arrays
    # 此处为示例，你可以根据需要进行计算
    updated_point_usage_arrays = []  # 用你的方法计算新的数组

    return jsonify({
        'new_price': new_price,
        'updated_data': updated_point_usage_arrays  # 返回新计算的数据
    })


@app.route('/refresh', methods=['GET'])
def refresh_data():
    """A route to refresh the data by redirecting to the main page."""
    return redirect(url_for('form'))

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error.html'), 500

if __name__ == "__main__":
    app.run(debug=True)
