# 刷题系统

Flask + SQLite 刷题系统，支持多题库、错题集、历史成绩追踪。

## 功能

- 白名单用户登录 / 注册
- 多题库支持（自动导入 xls / xlsx）
- 四种刷题模式：全部、分类、题型、错题本
- 题目随机、选项随机、背题模式、答对自动下一题
- 错题集管理
- 历史成绩趋势图
- 管理员面板（白名单管理、密码重置）

## 快速启动

```bash
pip install -r requirements.txt
python convert.py    # 导入题库（将 xls/xlsx 放到项目目录下）
python app.py        # 启动服务
```

访问 http://localhost:5588

## 管理脚本

| 平台 | 启动 | 停止 | 重启 |
|------|------|------|------|
| Windows | `start.bat` | `stop.bat` | - |
| Linux | `start.sh` | `stop.sh` | `restart.sh` |

## 默认管理员

柜员号：`8550357`
