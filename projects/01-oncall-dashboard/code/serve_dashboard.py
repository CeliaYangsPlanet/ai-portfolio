#!/usr/bin/env python3
"""本地看板服务器 — 提供 HTTP 访问 + 飞书数据同步 API"""
import http.server
import json
import subprocess
import sys
import os
import re
import datetime
import time

PORT = 8765
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SPREADSHEET_TOKEN = os.environ.get("FEISHU_SPREADSHEET_TOKEN", "")
TICKET_SHEET_ID = os.environ.get("FEISHU_TICKET_SHEET_ID", "")
QA_SHEET_ID = os.environ.get("FEISHU_QA_SHEET_ID", "")
FEISHU_APP_ID = os.environ.get("FEISHU_APP_ID", "")
FEISHU_APP_SECRET = os.environ.get("FEISHU_APP_SECRET", "")

TICKET_HEADERS = ["月","周","机器人工单ID","工单名称","产品线","业务组","业务域","工单来源","工单描述","机器人回复总结","是否使用AI能力","是否有答案","是否拦截成功","工单状态","转人工场景","转人工卡片","人工工单ID","人工工单-问题详情","人工工单-解决方案","机器人信息","是否属于无效机器人工单","是否转单","转单后产品线","转单后业务组","转单后业务域","反馈人","反馈人一级部门","反馈人二级部门","反馈人三级部门","工单创建时间","工单关闭时间","反馈人提问次数","机器人回复次数","知识库有应答次数","知识库文档引用数","机器人发送消息数","机器人回复用户反馈数","机器人回复有用率","机器人回复无用率","机器人回复总耗时（秒）","机器人会话时长(min)","反馈人会话时长(min)","会话时长(min)","工单时长(min)"]
QA_HEADERS = ["机器人工单id","产品线","业务组","业务域","轮次","问题","答案","回答方式","答案来源","是否拦截","转人工场景"]

EPOCH = datetime.datetime(1899, 12, 30)

def flatten_cell(cell):
    if cell is None: return ""
    if isinstance(cell, str): return cell
    if isinstance(cell, (int, float)): return str(cell)
    if isinstance(cell, list): return "".join(flatten_cell(item) for item in cell)
    if isinstance(cell, dict): return cell.get("text", "")
    return str(cell)

def excel_to_date(serial):
    try:
        val = float(serial)
        days = int(val)
        frac = val - days
        dt = EPOCH + datetime.timedelta(days=days)
        if frac > 0:
            dt += datetime.timedelta(seconds=int(frac * 86400))
        return dt.strftime('%Y-%m-%d')
    except:
        return str(serial)

def sync_feishu_data():
    """从飞书拉取最新数据并保存为 JS 文件"""
    print(f"[{datetime.datetime.now():%H:%M:%S}] 开始同步飞书数据...")

    # 获取行数
    result = subprocess.run(
        ['lark-cli', 'api', 'GET', f'/open-apis/sheets/v3/spreadsheets/{SPREADSHEET_TOKEN}/sheets/query', '--format', 'json'],
        capture_output=True, text=True, timeout=15
    )
    sheets = json.loads(result.stdout).get('data', {}).get('sheets', [])
    rc = {s['sheet_id']: s['grid_properties']['row_count'] for s in sheets}

    t_rows = rc.get(TICKET_SHEET_ID, 1303)
    qa_rows = rc.get(QA_SHEET_ID, 2460)

    # 拉取工单
    result = subprocess.run(
        ['lark-cli', 'api', 'GET', f'/open-apis/sheets/v2/spreadsheets/{SPREADSHEET_TOKEN}/values/{TICKET_SHEET_ID}!A2%3AAR{t_rows}', '--format', 'json'],
        capture_output=True, text=True, timeout=30
    )
    tickets = []
    for row in json.loads(result.stdout).get('data',{}).get('valueRange',{}).get('values',[]):
        obj = {}
        for i, h in enumerate(TICKET_HEADERS):
            obj[h] = flatten_cell(row[i]) if i < len(row) else ""
        tickets.append(obj)

    # 拉取问答
    result = subprocess.run(
        ['lark-cli', 'api', 'GET', f'/open-apis/sheets/v2/spreadsheets/{SPREADSHEET_TOKEN}/values/{QA_SHEET_ID}!A2%3AK{qa_rows}', '--format', 'json'],
        capture_output=True, text=True, timeout=30
    )
    qa = []
    for row in json.loads(result.stdout).get('data',{}).get('valueRange',{}).get('values',[]):
        obj = {}
        for i, h in enumerate(QA_HEADERS):
            obj[h] = flatten_cell(row[i]) if i < len(row) else ""
        qa.append(obj)

    # 转换日期
    for d in tickets:
        yue = str(d.get('月','')).strip()
        ct = str(d.get('工单创建时间','')).strip()
        if yue and yue.replace('.','').replace('-','').isdigit() and float(yue) > 40000:
            d['月'] = excel_to_date(yue)[:7]
        if ct and ct.replace('.','').replace('-','').isdigit() and float(ct) > 40000:
            d['工单创建时间'] = excel_to_date(ct) + ' 00:00:00'

    # 修复 QA VLOOKUP
    ticket_map = {str(t.get('机器人工单ID','')).strip(): t for t in tickets}
    for q in qa:
        qid = str(q.get('机器人工单id','')).strip()
        if qid in ticket_map:
            t = ticket_map[qid]
            for field in ['是否拦截', '转人工场景']:
                val = str(q.get(field, ''))
                if not val or 'VLOOKUP' in val:
                    t_field = '是否拦截成功' if field == '是否拦截' else field
                    q[field] = str(t.get(t_field, ''))

    # 保存 JS 文件（带时间戳）
    ts = str(int(time.time()))
    with open(os.path.join(BASE_DIR, 'data_tickets.js'), 'w', encoding='utf-8') as f:
        f.write('var FEISHU_TICKETS = ' + json.dumps(tickets, ensure_ascii=False) + ';\n')
    with open(os.path.join(BASE_DIR, 'data_qa.js'), 'w', encoding='utf-8') as f:
        f.write('var FEISHU_QA = ' + json.dumps(qa, ensure_ascii=False) + ';\n')

    # 更新看板中的时间戳
    dashboard_path = os.path.join(BASE_DIR, 'dashboard.html')
    with open(dashboard_path, 'r') as f:
        html = f.read()
    html = re.sub(r'data_tickets\.js\?t=\d+', f'data_tickets.js?t={ts}', html)
    html = re.sub(r'data_qa\.js\?t=\d+', f'data_qa.js?t={ts}', html)
    with open(dashboard_path, 'w') as f:
        f.write(html)

    print(f"[{datetime.datetime.now():%H:%M:%S}] 同步完成: {len(tickets)} 工单, {len(qa)} 问答")
    return {"tickets": len(tickets), "qa": len(qa), "ts": ts}


class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE_DIR, **kwargs)

    def do_POST(self):
        if self.path == '/sync':
            try:
                result = sync_feishu_data()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"ok": True, **result}, ensure_ascii=False).encode())
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def log_message(self, format, *args):
        # 精简日志
        if '/sync' not in args[0]:
            print(f"[{datetime.datetime.now():%H:%M:%S}] {args[0]}")


if __name__ == '__main__':
    print(f"""
╔══════════════════════════════════════════╗
║     机器人工单数据看板 - 本地服务器        ║
║                                          ║
║  打开浏览器访问:                          ║
║  → http://localhost:{PORT}/dashboard.html  ║
║                                          ║
║  按 Ctrl+C 停止服务器                     ║
╚══════════════════════════════════════════╝
""")
    server = http.server.HTTPServer(('0.0.0.0', PORT), DashboardHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务器已停止")
        server.shutdown()
