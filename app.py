from flask import Flask, request, render_template
import requests
import json
import os
Token = os.getenv('API_KEY')

app = Flask(__name__)

@app.route('/')
def form():
    return render_template('form.html')

@app.route('/get_balance_and_history', methods=['POST'])
def get_balance_and_history():
    api_key = request.form['apikey']
    url = f"https://api.api2d.com/custom_key/get?key={api_key}"
    headers = {
        'Authorization': f"Bearer {Token}"
    }
    req_body = {}

    response = requests.post(url, headers=headers, json=req_body)
    
    if response.status_code == 200:
        body = response.json()
        resp_statuscode = body.get('code')
        if resp_statuscode == 0:
            body['code'] = 200
            custom_key_json = body.get('data', {}).get('custom_key', {})
            custom_key_json_keys = list(custom_key_json.keys())
            for i in range(len(custom_key_json_keys)):
                if i not in [1, 2, 4]:
                    del custom_key_json[custom_key_json_keys[i]]
            point_usage_arrays = body.get('data', {}).get('point_usage_array', [])
            for i in range(len(point_usage_arrays)):
                usage_json = point_usage_arrays[i]
                usage_json_keys = list(usage_json.keys())
                for j in range(len(usage_json_keys)):
                    if j in [1, 5, 6]:
                        del usage_json[usage_json_keys[j]]
            return render_template('result.html', api_key=api_key, custom_key_json=custom_key_json, point_usage_arrays=point_usage_arrays)
    return 'Request failed', 400

if __name__ == "__main__":
    app.run(debug=True)
