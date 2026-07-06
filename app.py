"""刷题系统 - Flask + SQLite 后端服务"""
import json
import os
import sqlite3
import hashlib
import random
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)
app.config['SECRET_KEY'] = 'shuati-system-secret-2026'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'data', 'shuati.db')
ADMIN_ID = '8550357'

# ========== 数据库初始化 ==========

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def init_db():
    conn = get_db()
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS whitelist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT UNIQUE NOT NULL
        );
        CREATE TABLE IF NOT EXISTS users (
            phone TEXT PRIMARY KEY,
            password TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bank TEXT NOT NULL,
            category TEXT NOT NULL,
            type TEXT NOT NULL,
            content TEXT NOT NULL,
            options TEXT NOT NULL DEFAULT '[]',
            answer TEXT NOT NULL DEFAULT '[]',
            answer_text TEXT NOT NULL DEFAULT '',
            raw_answer TEXT NOT NULL DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS user_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT NOT NULL,
            bank TEXT NOT NULL,
            mode_key TEXT NOT NULL,
            shuffled_ids TEXT NOT NULL DEFAULT '[]',
            current_index INTEGER DEFAULT 0,
            answers TEXT NOT NULL DEFAULT '{}',
            submitted TEXT NOT NULL DEFAULT '{}',
            UNIQUE(phone, bank, mode_key)
        );
        CREATE TABLE IF NOT EXISTS wrong_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT NOT NULL,
            bank TEXT NOT NULL,
            question_id INTEGER NOT NULL,
            UNIQUE(phone, bank, question_id)
        );
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT NOT NULL,
            bank TEXT NOT NULL,
            date TEXT NOT NULL,
            mode TEXT NOT NULL,
            total INTEGER DEFAULT 0,
            correct INTEGER DEFAULT 0,
            rate REAL DEFAULT 0
        );
    ''')
    # 确保默认管理员在白名单
    cur = conn.execute("SELECT COUNT(*) FROM whitelist WHERE phone=?", (ADMIN_ID,))
    if cur.fetchone()[0] == 0:
        conn.execute("INSERT INTO whitelist (phone) VALUES (?)", (ADMIN_ID,))
    conn.commit()
    conn.close()


def hash_pwd(password):
    return hashlib.sha256(password.encode()).hexdigest()


# ========== 辅助函数 ==========

def get_available_banks():
    conn = get_db()
    cur = conn.execute("SELECT DISTINCT bank FROM questions ORDER BY bank")
    banks = [row[0] for row in cur.fetchall()]
    conn.close()
    return banks


def load_bank(bank_name):
    conn = get_db()
    cur = conn.execute("SELECT * FROM questions WHERE bank=? ORDER BY id", (bank_name,))
    rows = cur.fetchall()
    conn.close()
    if not rows:
        return None
    questions = []
    for row in rows:
        questions.append({
            "id": row["id"],
            "bank": row["bank"],
            "category": row["category"],
            "type": row["type"],
            "content": row["content"],
            "options": json.loads(row["options"]),
            "answer": json.loads(row["answer"]),
            "answer_text": row["answer_text"],
        })
    return questions


def filter_questions(questions, mode, filter_val=None):
    if mode == 'all':
        return list(questions)
    elif mode == 'category':
        return [q for q in questions if q['category'] == filter_val]
    elif mode == 'type':
        return [q for q in questions if q['type'] == filter_val]
    return list(questions)


def get_user_wrong_ids(phone, bank):
    conn = get_db()
    cur = conn.execute(
        "SELECT question_id FROM wrong_questions WHERE phone=? AND bank=?",
        (phone, bank)
    )
    ids = [row[0] for row in cur.fetchall()]
    conn.close()
    return ids


def get_user_sessions(phone, bank):
    conn = get_db()
    cur = conn.execute(
        "SELECT mode_key, shuffled_ids, current_index, answers, submitted FROM user_progress WHERE phone=? AND bank=?",
        (phone, bank)
    )
    sessions = {}
    for row in cur.fetchall():
        sessions[row["mode_key"]] = {
            "shuffledIds": json.loads(row["shuffled_ids"]),
            "currentIndex": row["current_index"],
            "answers": json.loads(row["answers"]),
            "submitted": json.loads(row["submitted"]),
        }
    conn.close()
    return sessions


# ========== 用户认证 API ==========

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    phone = data.get('phone', '').strip()
    password = data.get('password', '')

    if not phone or not password:
        return jsonify({'success': False, 'message': '请输入柜员号和密码'})

    conn = get_db()
    cur = conn.execute("SELECT COUNT(*) FROM whitelist WHERE phone=?", (phone,))
    if cur.fetchone()[0] == 0:
        conn.close()
        return jsonify({'success': False, 'message': '该柜员号不在白名单中，无法登录'})

    cur = conn.execute("SELECT password FROM users WHERE phone=?", (phone,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return jsonify({'success': False, 'message': '该柜员号尚未注册，请先设置密码'})

    if row["password"] != hash_pwd(password):
        return jsonify({'success': False, 'message': '密码错误'})

    return jsonify({'success': True, 'message': '登录成功', 'phone': phone})


@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    phone = data.get('phone', '').strip()
    password = data.get('password', '')

    if not phone or not password:
        return jsonify({'success': False, 'message': '请输入柜员号和密码'})
    if len(password) < 4:
        return jsonify({'success': False, 'message': '密码至少4位'})

    conn = get_db()
    cur = conn.execute("SELECT COUNT(*) FROM whitelist WHERE phone=?", (phone,))
    if cur.fetchone()[0] == 0:
        conn.close()
        return jsonify({'success': False, 'message': '该柜员号不在白名单中，无法注册'})

    try:
        conn.execute("INSERT INTO users (phone, password) VALUES (?, ?)", (phone, hash_pwd(password)))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': '注册成功'})
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'success': False, 'message': '该柜员号已注册'})


@app.route('/api/check_phone', methods=['POST'])
def check_phone():
    data = request.get_json()
    phone = data.get('phone', '').strip()

    conn = get_db()
    cur = conn.execute("SELECT COUNT(*) FROM whitelist WHERE phone=?", (phone,))
    in_wl = cur.fetchone()[0] > 0

    cur = conn.execute("SELECT COUNT(*) FROM users WHERE phone=?", (phone,))
    registered = cur.fetchone()[0] > 0
    conn.close()

    return jsonify({
        'success': True,
        'in_whitelist': in_wl,
        'registered': registered
    })


# ========== 题库 API ==========

@app.route('/api/banks', methods=['GET'])
def list_banks():
    banks = get_available_banks()
    result = []
    for bank in banks:
        questions = load_bank(bank)
        if questions:
            cats = {}
            types = {}
            for q in questions:
                cats[q['category']] = cats.get(q['category'], 0) + 1
                types[q['type']] = types.get(q['type'], 0) + 1
            result.append({
                'name': bank,
                'total': len(questions),
                'categories': [{'key': k, 'count': v} for k, v in sorted(cats.items())],
                'types': [{'key': k, 'count': v} for k, v in sorted(types.items())]
            })
    return jsonify({'success': True, 'banks': result})


@app.route('/api/questions', methods=['GET'])
def get_questions():
    bank_name = request.args.get('bank', '')
    mode = request.args.get('mode', 'all')
    filter_val = request.args.get('filter', '')
    phone = request.args.get('phone', '')
    shuffle = request.args.get('shuffle', '0') == '1'

    questions = load_bank(bank_name)
    if questions is None:
        return jsonify({'success': False, 'message': '题库不存在'})

    if mode == 'wrong':
        wrong_ids = set(get_user_wrong_ids(phone, bank_name))
        filtered = [q for q in questions if q['id'] in wrong_ids]
    else:
        filtered = filter_questions(questions, mode, filter_val)

    if not filtered:
        return jsonify({'success': False, 'message': '没有符合条件的题目'})

    if shuffle:
        random.shuffle(filtered)

    return jsonify({
        'success': True,
        'questions': filtered,
        'total': len(filtered)
    })


# ========== 进度 API ==========

@app.route('/api/progress', methods=['GET'])
def get_progress():
    phone = request.args.get('phone', '')
    bank_name = request.args.get('bank', '')

    wrong_ids = get_user_wrong_ids(phone, bank_name)
    sessions = get_user_sessions(phone, bank_name)

    conn = get_db()
    cur = conn.execute(
        "SELECT COALESCE(SUM(total), 0) FROM history WHERE phone=? AND bank=?",
        (phone, bank_name)
    )
    answered_count = cur.fetchone()[0]
    conn.close()

    return jsonify({
        'success': True,
        'progress': {
            'wrong_ids': wrong_ids,
            'sessions': sessions,
            'answered_count': answered_count,
        }
    })


@app.route('/api/progress/save', methods=['POST'])
def save_progress():
    data = request.get_json()
    phone = data.get('phone', '')
    bank_name = data.get('bank', '')
    session_data = data.get('session', {})

    conn = get_db()
    for mode_key, ss in session_data.items():
        conn.execute('''
            INSERT INTO user_progress (phone, bank, mode_key, shuffled_ids, current_index, answers, submitted)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(phone, bank, mode_key) DO UPDATE SET
                shuffled_ids=excluded.shuffled_ids,
                current_index=excluded.current_index,
                answers=excluded.answers,
                submitted=excluded.submitted
        ''', (
            phone,
            bank_name,
            mode_key,
            json.dumps(ss.get('shuffledIds', []), ensure_ascii=False),
            ss.get('currentIndex', 0),
            json.dumps(ss.get('answers', {}), ensure_ascii=False),
            json.dumps(ss.get('submitted', {}), ensure_ascii=False),
        ))
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': '进度已保存'})


@app.route('/api/progress/history', methods=['POST'])
def save_history():
    data = request.get_json()
    phone = data.get('phone', '')
    bank_name = data.get('bank', '')
    record = data.get('record', {})

    conn = get_db()
    conn.execute(
        "INSERT INTO history (phone, bank, date, mode, total, correct, rate) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (phone, bank_name, record.get('date', ''), record.get('mode', ''),
         record.get('total', 0), record.get('correct', 0), record.get('rate', 0))
    )
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': '记录已保存'})


@app.route('/api/history', methods=['GET'])
def get_history():
    phone = request.args.get('phone', '')
    bank_name = request.args.get('bank', '')

    conn = get_db()
    cur = conn.execute(
        "SELECT date, mode, total, correct, rate FROM history WHERE phone=? AND bank=? ORDER BY id ASC",
        (phone, bank_name)
    )
    history = [{
        'date': row['date'],
        'mode': row['mode'],
        'total': row['total'],
        'correct': row['correct'],
        'rate': row['rate'],
    } for row in cur.fetchall()]
    conn.close()

    return jsonify({'success': True, 'history': history})


# ========== 错题管理 API ==========

@app.route('/api/wrong/add', methods=['POST'])
def add_wrong():
    data = request.get_json()
    phone = data.get('phone', '')
    bank_name = data.get('bank', '')
    question_id = data.get('question_id')

    conn = get_db()
    try:
        conn.execute(
            "INSERT OR IGNORE INTO wrong_questions (phone, bank, question_id) VALUES (?, ?, ?)",
            (phone, bank_name, question_id)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    conn.close()

    wrong_ids = get_user_wrong_ids(phone, bank_name)
    return jsonify({'success': True, 'message': '已加入错题集', 'wrong_ids': wrong_ids})


@app.route('/api/wrong/remove', methods=['POST'])
def remove_wrong():
    data = request.get_json()
    phone = data.get('phone', '')
    bank_name = data.get('bank', '')
    question_id = data.get('question_id')

    conn = get_db()
    conn.execute(
        "DELETE FROM wrong_questions WHERE phone=? AND bank=? AND question_id=?",
        (phone, bank_name, question_id)
    )
    conn.commit()
    conn.close()

    wrong_ids = get_user_wrong_ids(phone, bank_name)
    return jsonify({'success': True, 'message': '已移出错题集', 'wrong_ids': wrong_ids})


@app.route('/api/wrong/clear', methods=['POST'])
def clear_wrong():
    data = request.get_json()
    phone = data.get('phone', '')
    bank_name = data.get('bank', '')

    conn = get_db()
    conn.execute("DELETE FROM wrong_questions WHERE phone=? AND bank=?", (phone, bank_name))
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': '错题集已清空', 'wrong_ids': []})


@app.route('/api/wrong/list', methods=['GET'])
def get_wrong():
    phone = request.args.get('phone', '')
    bank_name = request.args.get('bank', '')
    wrong_ids = get_user_wrong_ids(phone, bank_name)
    return jsonify({'success': True, 'wrong_ids': wrong_ids})


# ========== 白名单管理 API ==========

@app.route('/api/whitelist', methods=['GET'])
def get_whitelist():
    phone = request.args.get('phone', '')
    if phone != ADMIN_ID:
        return jsonify({'success': False, 'message': '无管理员权限'})

    conn = get_db()
    cur = conn.execute("SELECT phone FROM whitelist ORDER BY id")
    whitelist = [row[0] for row in cur.fetchall()]
    conn.close()
    return jsonify({'success': True, 'whitelist': whitelist})


@app.route('/api/whitelist', methods=['POST'])
def update_whitelist():
    data = request.get_json()
    admin_phone = data.get('admin_phone', '')
    if admin_phone != ADMIN_ID:
        return jsonify({'success': False, 'message': '无管理员权限'})

    phone = data.get('phone', '').strip()
    action = data.get('action', '')

    if not phone:
        return jsonify({'success': False, 'message': '请输入柜员号'})

    conn = get_db()
    if action == 'add':
        conn.execute("INSERT OR IGNORE INTO whitelist (phone) VALUES (?)", (phone,))
        conn.commit()
        cur = conn.execute("SELECT phone FROM whitelist ORDER BY id")
        whitelist = [row[0] for row in cur.fetchall()]
        conn.close()
        return jsonify({'success': True, 'message': f'已添加 {phone}', 'whitelist': whitelist})

    elif action == 'remove':
        conn.execute("DELETE FROM whitelist WHERE phone=?", (phone,))
        conn.commit()
        cur = conn.execute("SELECT phone FROM whitelist ORDER BY id")
        whitelist = [row[0] for row in cur.fetchall()]
        conn.close()
        return jsonify({'success': True, 'message': f'已移除 {phone}', 'whitelist': whitelist})

    conn.close()
    return jsonify({'success': False, 'message': '无效操作'})


# ========== 管理员 API ==========

@app.route('/api/admin/check', methods=['GET'])
def check_admin():
    phone = request.args.get('phone', '')
    return jsonify({'success': True, 'is_admin': phone == ADMIN_ID})


@app.route('/api/admin/reset_password', methods=['POST'])
def admin_reset_password():
    data = request.get_json()
    admin_phone = data.get('admin_phone', '')
    if admin_phone != ADMIN_ID:
        return jsonify({'success': False, 'message': '无管理员权限'})

    target_phone = data.get('target_phone', '').strip()
    new_password = data.get('new_password', '')

    if not target_phone or not new_password:
        return jsonify({'success': False, 'message': '请填写完整信息'})
    if len(new_password) < 4:
        return jsonify({'success': False, 'message': '密码至少4位'})

    conn = get_db()
    cur = conn.execute("SELECT COUNT(*) FROM users WHERE phone=?", (target_phone,))
    if cur.fetchone()[0] == 0:
        conn.close()
        return jsonify({'success': False, 'message': '该用户尚未注册'})

    conn.execute("UPDATE users SET password=? WHERE phone=?", (hash_pwd(new_password), target_phone))
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': f'已重置 {target_phone} 的密码'})


# ========== 主页面 ==========

@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    init_db()
    print('=' * 50)
    print('刷题系统已启动！（SQLite版）')
    print('访问地址: http://localhost:5588')
    print('=' * 50)
    app.run(debug=False, port=5588, host='0.0.0.0', threaded=True)
