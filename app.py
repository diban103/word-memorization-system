from flask import Flask, jsonify, request
import json
import random
from datetime import datetime, timedelta

app = Flask(__name__)

# 加载单词数据
with open('english.json', 'r', encoding='utf-8') as f:
    words = json.load(f)

# 用户学习记录
user_records = {}

# 记忆曲线间隔（小时）
SPACED_INTERVALS = [1, 24, 72, 168, 336]  # 1小时, 1天, 3天, 7天, 14天

@app.route('/get_words', methods=['GET'])
def get_words():
    count = int(request.args.get('count', 20))
    user_id = request.args.get('user_id', 'default')
    
    # 初始化用户记录
    if user_id not in user_records:
        user_records[user_id] = {
            'learned': [],
            'review': []
        }
    
    # 检查需要复习的单词
    now = datetime.now()
    review_words = []
    for word_id, review_time in user_records[user_id]['review']:
        if now >= datetime.fromisoformat(review_time):
            review_words.append(next(w for w in words if w['id'] == word_id))
    
    # 获取新单词
    new_words = []
    if len(review_words) < count:
        learned_ids = [w['id'] for w in user_records[user_id]['learned']]
        available_words = [w for w in words if w['id'] not in learned_ids]
        new_count = min(count - len(review_words), len(available_words))
        if new_count < 0:
            new_count = 0
        # 从可用单词中按顺序取新单词，而不是随机取样
        new_words = available_words[:new_count]
        # 记录已学习的新单词
        for word in new_words:
            user_records[user_id]['learned'].append(word)
            # 设置复习时间
            for interval in SPACED_INTERVALS:
                review_time = datetime.now() + timedelta(hours=interval)
                user_records[user_id]['review'].append((word['id'], review_time.isoformat()))
    
    # 合并结果并标记复习单词
    result = []
    for word in review_words:
        word['is_review'] = True
        result.append(word)
    result.extend(new_words)
    
    return jsonify(result)

@app.route('/record_learned', methods=['POST'])
def record_learned():
    data = request.json
    user_id = data.get('user_id', 'default')
    word_id = data['word_id']
    
    # 记录学习时间
    word = next(w for w in words if w['id'] == word_id)
    user_records[user_id]['learned'].append(word)
    
    # 设置复习时间
    for interval in SPACED_INTERVALS:
        review_time = datetime.now() + timedelta(hours=interval)
        user_records[user_id]['review'].append((word_id, review_time.isoformat()))
    
    return jsonify({'status': 'success'})

@app.route('/')
def index():
    return app.send_static_file('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)