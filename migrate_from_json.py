"""将旧版 shuatiServer 的 JSON 数据迁移到 SQLite"""
import json
import os
import sqlite3

OLD_DIR = r"D:\Desktop\卢恩厅\工作\shuatiServer\data"
NEW_DB = os.path.join(os.path.dirname(__file__), "data", "shuati.db")

conn = sqlite3.connect(NEW_DB)

# 1️⃣ 白名单
with open(os.path.join(OLD_DIR, "whitelist.json"), "r", encoding="utf-8") as f:
    whitelist = json.load(f)
for phone in whitelist:
    conn.execute("INSERT OR IGNORE INTO whitelist (phone) VALUES (?)", (phone,))
print(f"✅ 白名单: {len(whitelist)} 条")

# 2️⃣ 用户
with open(os.path.join(OLD_DIR, "users.json"), "r", encoding="utf-8") as f:
    users = json.load(f)
for phone, data in users.items():
    conn.execute("INSERT OR IGNORE INTO users (phone, password) VALUES (?, ?)",
                 (phone, data["password"]))
print(f"✅ 用户: {len(users)} 条")

# 3️⃣ 进度数据（错题集 + 答题进度 + 历史）
raw = open(os.path.join(OLD_DIR, "progress.json"), "r", encoding="utf-8").read()
# 兼容文件被多次追加写入的情况，只取第一个完整 JSON
for end in range(len(raw), 0, -1):
    try:
        progress = json.loads(raw[:end])
        break
    except json.JSONDecodeError:
        continue

wc = sc = hc = 0
for phone, banks in progress.items():
    for bank_name, data in banks.items():
        for qid in data.get("wrong_ids", []):
            conn.execute("INSERT OR IGNORE INTO wrong_questions (phone, bank, question_id) VALUES (?, ?, ?)",
                         (phone, bank_name, qid))
            wc += 1
        for mode_key, ss in data.get("sessions", {}).items():
            conn.execute('''
                INSERT OR IGNORE INTO user_progress (phone, bank, mode_key, shuffled_ids, current_index, answers, submitted)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                phone, bank_name, mode_key,
                json.dumps(ss.get("shuffledIds", [])),
                ss.get("currentIndex", 0),
                json.dumps(ss.get("answers", {})),
                json.dumps(ss.get("submitted", {})),
            ))
            sc += 1
        for rec in data.get("history", []):
            conn.execute(
                "INSERT INTO history (phone, bank, date, mode, total, correct, rate) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (phone, bank_name, rec.get("date", ""), rec.get("mode", ""),
                 rec.get("total", 0), rec.get("correct", 0), rec.get("rate", 0))
            )
            hc += 1

conn.commit()
conn.close()
print(f"✅ 错题集: {wc} 条")
print(f"✅ 答题进度: {sc} 条")
print(f"✅ 历史记录: {hc} 条")
print("\n🎉 迁移完成！")
