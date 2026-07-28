#!/usr/bin/env python3
"""从飞书电子表格同步数据到 dashboard.html"""
import json, subprocess, sys, re, os

SPREADSHEET_TOKEN = os.environ.get("FEISHU_SPREADSHEET_TOKEN", "")
TICKET_SHEET_ID = os.environ.get("FEISHU_TICKET_SHEET_ID", "")
QA_SHEET_ID = os.environ.get("FEISHU_QA_SHEET_ID", "")
FEISHU_APP_ID = os.environ.get("FEISHU_APP_ID", "")
FEISHU_APP_SECRET = os.environ.get("FEISHU_APP_SECRET", "")

TICKET_HEADERS = ["月","周","机器人工单ID","工单名称","产品线","业务组","业务域","工单来源","工单描述","机器人回复总结","是否使用AI能力","是否有答案","是否拦截成功","工单状态","转人工场景","转人工卡片","人工工单ID","人工工单-问题详情","人工工单-解决方案","机器人信息","是否属于无效机器人工单","是否转单","转单后产品线","转单后业务组","转单后业务域","反馈人","反馈人一级部门","反馈人二级部门","反馈人三级部门","工单创建时间","工单关闭时间","反馈人提问次数","机器人回复次数","知识库有应答次数","知识库文档引用数","机器人发送消息数","机器人回复用户反馈数","机器人回复有用率","机器人回复无用率","机器人回复总耗时（秒）","机器人会话时长(min)","反馈人会话时长(min)","会话时长(min)","工单时长(min)"]

QA_HEADERS = ["机器人工单id","产品线","业务组","业务域","轮次","问题","答案","回答方式","答案来源","是否拦截","转人工场景"]

def flatten_cell(cell):
    if cell is None: return ""
    if isinstance(cell, str): return cell
    if isinstance(cell, (int, float)): return str(cell)
    if isinstance(cell, list): return "".join(flatten_cell(item) for item in cell)
    if isinstance(cell, dict): return cell.get("text", "")
    return str(cell)

def fetch_sheet(sheet_id, range_end, headers):
    url = f"/open-apis/sheets/v2/spreadsheets/{SPREADSHEET_TOKEN}/values/{sheet_id}!A2%3A{range_end}"
    result = subprocess.run(
        ['lark-cli', 'api', 'GET', url, '--format', 'json'],
        capture_output=True, text=True, timeout=30
    )
    data = json.loads(result.stdout)
    values = data.get('data', {}).get('valueRange', {}).get('values', [])
    rows = []
    for row in values:
        obj = {}
        for i, h in enumerate(headers):
            val = row[i] if i < len(row) else ""
            obj[h] = flatten_cell(val)
        rows.append(obj)
    return rows

# Get row counts first
result = subprocess.run(
    ['lark-cli', 'api', 'GET', f'/open-apis/sheets/v3/spreadsheets/{SPREADSHEET_TOKEN}/sheets/query', '--format', 'json'],
    capture_output=True, text=True, timeout=15
)
sheets_data = json.loads(result.stdout)
sheets = sheets_data.get('data', {}).get('sheets', [])
row_counts = {}
for s in sheets:
    row_counts[s['sheet_id']] = s['grid_properties']['row_count']

ticket_rows = row_counts.get(TICKET_SHEET_ID, 1303)
qa_rows = row_counts.get(QA_SHEET_ID, 2460)

print(f"Fetching tickets ({ticket_rows} rows)...")
tickets = fetch_sheet(TICKET_SHEET_ID, f"AR{ticket_rows}", TICKET_HEADERS)
print(f"  Got {len(tickets)} tickets")

print(f"Fetching QA ({qa_rows} rows)...")
qa = fetch_sheet(QA_SHEET_ID, f"K{qa_rows}", QA_HEADERS)
print(f"  Got {len(qa)} QA rows")

tickets_json = json.dumps(tickets, ensure_ascii=False)
qa_json = json.dumps(qa, ensure_ascii=False)

# Update dashboard.html
dashboard_path = sys.argv[1] if len(sys.argv) > 1 else '/Users/admin/Downloads/dashboard.html'
with open(dashboard_path, 'r') as f:
    content = f.read()

# Replace FEISHU_TICKETS
content = re.sub(
    r'var FEISHU_TICKETS = \[.*?\];',
    f'var FEISHU_TICKETS = {tickets_json};',
    content,
    count=1,
    flags=re.DOTALL
)

# Replace FEISHU_QA
content = re.sub(
    r'var FEISHU_QA = \[.*?\];',
    f'var FEISHU_QA = {qa_json};',
    content,
    count=1,
    flags=re.DOTALL
)

with open(dashboard_path, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Updated {dashboard_path} ({len(content)} bytes)")
print(f"Tickets: {len(tickets)}, QA: {len(qa)}")
