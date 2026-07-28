#!/usr/bin/env python3
"""生成"值班号机器人运营平台"产品架构图和工作流图
风格与 dashboard.html 保持一致
"""

from PIL import Image, ImageDraw, ImageFont
import math
import os

# ============================================================
# 画布与路径
# ============================================================
W, H = 2400, 1600
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images")
os.makedirs(OUT_DIR, exist_ok=True)

# ============================================================
# 色板（与 dashboard.html 对齐）
# ============================================================
BG          = "#f0f2f5"
CARD_BG     = "#ffffff"
PRIMARY     = "#4f6ef7"
PRIMARY_END = "#7c5cfc"
TEXT_MAIN   = "#1a1a2e"
TEXT_SEC    = "#5f6368"
TEXT_MUTED  = "#9aa0a6"
GREEN       = "#1e8e3e"
RED         = "#ea4335"
BORDER      = "#e8eaed"
ARROW_COLOR = "#c9d1f8"
ACCENT_LINE = (79, 110, 247)   # #4f6ef7
ACCENT_END  = (124, 92, 252)   # #7c5cfc

# ============================================================
# 字体
# ============================================================
FONT_CN = ImageFont.truetype("/System/Library/Fonts/STHeiti Medium.ttc", 28)
FONT_CN_SM = ImageFont.truetype("/System/Library/Fonts/STHeiti Medium.ttc", 22)
FONT_CN_XS = ImageFont.truetype("/System/Library/Fonts/STHeiti Medium.ttc", 18)
FONT_CN_TITLE = ImageFont.truetype("/System/Library/Fonts/STHeiti Medium.ttc", 40)
FONT_CN_H1 = ImageFont.truetype("/System/Library/Fonts/STHeiti Medium.ttc", 48)
FONT_CN_BIG = ImageFont.truetype("/System/Library/Fonts/STHeiti Medium.ttc", 32)

try:
    FONT_EN = ImageFont.truetype("/System/Library/Fonts/SFNS.ttf", 24)
    FONT_EN_SM = ImageFont.truetype("/System/Library/Fonts/SFNS.ttf", 18)
    FONT_EN_XS = ImageFont.truetype("/System/Library/Fonts/SFNS.ttf", 15)
except Exception:
    FONT_EN = FONT_CN
    FONT_EN_SM = FONT_CN_SM
    FONT_EN_XS = FONT_CN_XS


# ============================================================
# 绘图工具函数
# ============================================================

def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def lerp_color(c1, c2, t):
    """线性插值两个 RGB 颜色"""
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def draw_rounded_rect(draw, xy, radius, fill=None, outline=None, width=1):
    """绘制圆角矩形"""
    x1, y1, x2, y2 = xy
    r = radius
    draw.rounded_rectangle(xy, radius=r, fill=fill, outline=outline, width=width)


def draw_gradient_line(draw, x1, y1, x2, y2, c1, c2, width=6):
    """绘制渐变线（水平）"""
    w = int(x2 - x1)
    for i in range(w):
        t = i / max(w - 1, 1)
        color = lerp_color(c1, c2, t)
        draw.line([(x1 + i, y1), (x1 + i, y1 + width)], fill=color)


def draw_accent_bar(draw, card_x, card_y, card_w):
    """在卡片顶部画渐变装饰线"""
    c1 = hex_to_rgb(PRIMARY)
    c2 = hex_to_rgb(PRIMARY_END)
    draw_gradient_line(draw, card_x + 24, card_y, card_x + card_w - 24, card_y, c1, c2, 6)


def draw_card_shadow(draw, x, y, w, h, radius):
    """模拟卡片阴影（多层半透明边框）"""
    for i, alpha in [(6, 8), (4, 10), (2, 12)]:
        draw_rounded_rect(draw, (x-i, y-i, x+w+i, y+h+i), radius + i,
                          outline=(0, 0, 0, alpha), width=1)


def draw_dashed_arrow(draw, x1, y1, x2, y2, color, width=3, dash_len=16, gap_len=10):
    """绘制虚线箭头"""
    dx = x2 - x1
    dy = y2 - y1
    length = math.sqrt(dx*dx + dy*dy)
    if length == 0:
        return
    ux = dx / length
    uy = dy / length
    pos = 0.0
    total = dash_len + gap_len
    while pos < length - 12:
        start = pos
        end = min(pos + dash_len, length - 12)
        draw.line([
            (x1 + ux * start, y1 + uy * start),
            (x1 + ux * end, y1 + uy * end)
        ], fill=color, width=width)
        pos += total
    # 箭头
    arrow_size = 14
    tip_x, tip_y = x2, y2
    base_x = tip_x - ux * arrow_size
    base_y = tip_y - uy * arrow_size
    px = -uy * arrow_size * 0.5
    py = ux * arrow_size * 0.5
    draw.polygon([
        (tip_x, tip_y),
        (base_x + px, base_y + py),
        (base_x - px, base_y - py)
    ], fill=color)


def draw_solid_arrow(draw, x1, y1, x2, y2, color, width=3):
    """绘制实线箭头"""
    draw.line([(x1, y1), (x2, y2)], fill=color, width=width)
    dx = x2 - x1
    dy = y2 - y1
    length = math.sqrt(dx*dx + dy*dy)
    if length == 0:
        return
    ux = dx / length
    uy = dy / length
    arrow_size = 14
    tip_x, tip_y = x2, y2
    base_x = tip_x - ux * arrow_size
    base_y = tip_y - uy * arrow_size
    px = -uy * arrow_size * 0.5
    py = ux * arrow_size * 0.5
    draw.polygon([
        (tip_x, tip_y),
        (base_x + px, base_y + py),
        (base_x - px, base_y - py)
    ], fill=color)


def draw_icon_circle(draw, cx, cy, r, color_start, color_end):
    """绘制渐变圆形图标背景"""
    for i in range(r * 2):
        t = i / max(r * 2 - 1, 1)
        y = cy - r + i
        color = lerp_color(color_start, color_end, t)
        x_start = cx - int(math.sqrt(max(0, r*r - (i - r)**2)))
        x_end = cx + int(math.sqrt(max(0, r*r - (i - r)**2)))
        draw.line([(x_start, y), (x_end, y)], fill=color)


def draw_icon_symbol(draw, cx, cy, icon_type, size=28):
    """绘制简单几何图标"""
    white = (255, 255, 255)
    w = 3  # 线宽
    if icon_type == "spreadsheet":
        # 表格图标
        r = size
        draw.rectangle((cx-r, cy-r+8, cx+r, cy+r), outline=white, width=w)
        draw.line((cx-r, cy-r+8+20, cx+r, cy-r+8+20), fill=white, width=w)
        draw.line((cx-6, cy-r+8, cx-6, cy+r), fill=white, width=w)
    elif icon_type == "api":
        # API / 齿轮
        r = size - 4
        for i in range(0, 360, 45):
            rad = i * math.pi / 180
            draw.line((cx + (r-6)*math.cos(rad), cy + (r-6)*math.sin(rad),
                       cx + r*math.cos(rad), cy + r*math.sin(rad)), fill=white, width=w)
        draw.ellipse((cx-r+10, cy-r+10, cx+r-10, cy+r-10), outline=white, width=w)
    elif icon_type == "python":
        # Python / 脚本
        r = size
        draw.line((cx-8, cy-r+4, cx+8, cy-4), fill=white, width=w)
        draw.line((cx-8, cy+4, cx+8, cy-r+4+10), fill=white, width=w)
        draw.line((cx-8, cy-r+4, cx-8, cy+4), fill=white, width=w)
        draw.arc((cx-8, cy-4, cx+8, cy+8), 0, 180, fill=white, width=w)
    elif icon_type == "database":
        # 数据库 / 存储
        r = size
        ew = r
        eh = 8
        draw.ellipse((cx-ew, cy-r+6, cx+ew, cy-r+6+eh*2), outline=white, width=w)
        draw.arc((cx-ew, cy-r+6, cx+ew, cy-r+6+eh*2), 0, 180, fill=white, width=w)
        draw.line((cx-ew, cy-r+6+eh, cx-ew, cy+r-eh), fill=white, width=w)
        draw.line((cx+ew, cy-r+6+eh, cx+ew, cy+r-eh), fill=white, width=w)
        draw.ellipse((cx-ew, cy+r-6-eh*2, cx+ew, cy+r-6), outline=white, width=w)
        draw.arc((cx-ew, cy+r-6-eh*2, cx+ew, cy+r-6), 0, 180, fill=white, width=w)
    elif icon_type == "dashboard":
        # 看板 / 图表
        r = size
        draw.rectangle((cx-r, cy-r, cx+r, cy+r), outline=white, width=w)
        bw = 8
        for bx in [cx-10, cx, cx+10]:
            bh = [16, 24, 12][(bx - cx + 10) // 10]
            draw.rectangle((bx-bw, cy+r-4-bh, bx+bw, cy+r-4), fill=white)
    elif icon_type == "layer":
        # 层
        r = size
        draw.rectangle((cx-r, cy-r, cx+r, cy+r-8), outline=white, width=w)
        draw.rectangle((cx-r+6, cy-r+8, cx+r-6, cy+r), outline=white, width=w)
    elif icon_type == "server":
        # 服务器
        r = size
        draw.rectangle((cx-r, cy-r+4, cx+r, cy+r-4), outline=white, width=w)
        for ly in [cy-8, cy, cy+8]:
            draw.line((cx-10, ly, cx+10, ly), fill=white, width=2)
        for dot_x in [cx-6, cx+6]:
            draw.ellipse((dot_x-2, cy-12, dot_x+2, cy-8), fill=white)
    elif icon_type == "feishu":
        # 飞书 / 云
        r = size
        draw.arc((cx-r, cy-r+6, cx-4, cy+6), 90, 270, fill=white, width=w)
        draw.arc((cx+4, cy-r+6, cx+r, cy+6), 270, 90, fill=white, width=w)
        draw.arc((cx-10, cy-r-2, cx+10, cy+r-2), 180, 0, fill=white, width=w)
    elif icon_type == "browser":
        # 浏览器
        r = size
        draw.rounded_rectangle((cx-r, cy-r, cx+r, cy+r), radius=8, outline=white, width=w)
        draw.line((cx-r, cy-r+12, cx+r, cy-r+12), fill=white, width=w)
        draw.ellipse((cx-r+6, cy-r+4, cx-r+14, cy-r+12), outline=white, width=2)
    elif icon_type == "check":
        # 勾选
        r = size
        draw.ellipse((cx-r, cy-r, cx+r, cy+r), outline=white, width=w)
        draw.line((cx-6, cy, cx-2, cy+6), fill=white, width=w)
        draw.line((cx-2, cy+6, cx+8, cy-6), fill=white, width=w)


def draw_tag(draw, x, y, text, bg_color, text_color="#ffffff"):
    """绘制小标签"""
    font = FONT_EN_XS
    tw = draw.textlength(text, font=font)
    pad_x, pad_y = 12, 6
    draw_rounded_rect(draw, (x, y, x + tw + pad_x*2, y + 22 + pad_y*2), 10, fill=bg_color)
    draw.text((x + pad_x, y + pad_y), text, fill=text_color, font=font)


def draw_title_block(draw, title, subtitle, y=80):
    """绘制标题区域"""
    x = 80
    # 装饰线
    c1 = hex_to_rgb(PRIMARY)
    c2 = hex_to_rgb(PRIMARY_END)
    draw_gradient_line(draw, x, y, x + 80, y, c1, c2, 6)
    # 标题
    draw.text((x, y + 18), title, fill=TEXT_MAIN, font=FONT_CN_H1)
    draw.text((x, y + 82), subtitle, fill=TEXT_MUTED, font=FONT_CN_SM)

    return y + 130  # 返回标题区底部 y


def draw_arch_tag(draw, x, y, text, is_highlight=False):
    """绘制架构特征小标签"""
    font = FONT_CN_XS
    tw = draw.textlength(text, font=font)
    bg = PRIMARY if is_highlight else "#ffffff"
    tc = "#ffffff" if is_highlight else TEXT_SEC
    outline_c = PRIMARY if is_highlight else BORDER
    draw_rounded_rect(draw, (x, y, x + tw + 24, y + 34), 8, fill=bg, outline=outline_c, width=2)
    draw.text((x + 12, y + 4), text, fill=tc, font=font)
    return tw + 28


# ============================================================
# 图1: workflow.png — 业务数据流转图
# ============================================================

def draw_workflow():
    img = Image.new("RGBA", (W, H), BG)
    draw = ImageDraw.Draw(img)

    # 标题
    title_y = draw_title_block(draw, "业务数据流转图", "Data Flow — 从飞书在线表格到浏览器看板的端到端数据链路")

    # 5 个流程节点
    nodes = [
        {"icon": "spreadsheet", "title": "飞书在线表格", "desc": "机器人工单明细表\n机器人问答明细表\n两个工作表实时更新", "tag": "Feishu Sheets", "layer": "数据源"},
        {"icon": "api",       "title": "飞书 Open API", "desc": "lark-cli 命令行工具\n调用 API v2 接口\n拉取全量表格数据", "tag": "lark-cli / API", "layer": "采集层"},
        {"icon": "python",    "title": "Python 数据同步", "desc": "refresh_feishu_data.py\n日期格式转换 & 数据清洗\nVLOOKUP 字段修复", "tag": "Python 3", "layer": "加工层"},
        {"icon": "database",  "title": "JS 数据快照", "desc": "data_tickets.js (工单)\ndata_qa.js (问答)\ndata_manual.js (人工)", "tag": "JavaScript", "layer": "交付层"},
        {"icon": "dashboard", "title": "浏览器看板渲染", "desc": "dashboard.html 核心看板\nChart.js 图表 / 语义聚类\nbiweekly-review 复盘页", "tag": "HTML5 + Chart.js", "layer": "展示层"},
    ]

    card_w = 360
    card_h = 320
    card_radius = 24
    gap = 50
    total_w = 5 * card_w + 4 * gap
    start_x = (W - total_w) // 2
    card_y = title_y + 40

    # 泳道标签
    layer_y = card_y - 48
    for i, node in enumerate(nodes):
        cx = start_x + i * (card_w + gap)
        font = FONT_CN_XS
        lw = draw.textlength(node["layer"], font=font)
        draw.text((cx + (card_w - lw) // 2, layer_y), node["layer"], fill=TEXT_MUTED, font=font)

    # 绘制节点
    node_centers = []
    c1 = hex_to_rgb(PRIMARY)
    c2 = hex_to_rgb(PRIMARY_END)

    for i, node in enumerate(nodes):
        cx = start_x + i * (card_w + gap)
        cy = card_y

        # 阴影
        draw_card_shadow(draw, cx, cy, card_w, card_h, card_radius)
        # 卡片
        draw_rounded_rect(draw, (cx, cy, cx + card_w, cy + card_h), card_radius, fill=CARD_BG, outline=BORDER, width=2)
        # 顶部渐变线
        draw_accent_bar(draw, cx, cy, card_w)

        # 图标
        icon_cy = cy + 60
        icon_cx = cx + card_w // 2
        draw_icon_circle(draw, icon_cx, icon_cy, 36, c1, c2)
        draw_icon_symbol(draw, icon_cx, icon_cy, node["icon"], 24)

        # 标题
        title = node["title"]
        tw = draw.textlength(title, font=FONT_CN_BIG)
        draw.text((cx + (card_w - tw) // 2, cy + 114), title, fill=TEXT_MAIN, font=FONT_CN_BIG)

        # 描述（多行）
        desc_lines = node["desc"].split("\n")
        desc_y = cy + 160
        for line in desc_lines:
            lw = draw.textlength(line, font=FONT_CN_XS)
            draw.text((cx + (card_w - lw) // 2, desc_y), line, fill=TEXT_SEC, font=FONT_CN_XS)
            desc_y += 28

        # 标签
        tag_text = node["tag"]
        tag_font = FONT_EN_XS
        tw = draw.textlength(tag_text, font=tag_font)
        tag_x = cx + (card_w - tw - 24) // 2
        tag_y = cy + card_h - 50
        draw_rounded_rect(draw, (tag_x, tag_y, tag_x + tw + 24, tag_y + 30), 8, fill=PRIMARY)
        draw.text((tag_x + 12, tag_y + 3), tag_text, fill="#ffffff", font=tag_font)

        node_centers.append((cx + card_w // 2, cy + card_h // 2))

    # 节点间箭头
    arrow_color = hex_to_rgb(ARROW_COLOR)
    for i in range(len(node_centers) - 1):
        x1 = node_centers[i][0] + card_w // 2 + 10
        y1 = node_centers[i][1]
        x2 = node_centers[i+1][0] - card_w // 2 - 10
        y2 = node_centers[i+1][1]
        draw_solid_arrow(draw, x1, y1, x2, y2, arrow_color, width=4)

    # 底部说明栏
    footer_y = card_y + card_h + 60
    footer_w = total_w
    footer_x = start_x
    footer_h = 100

    draw_rounded_rect(draw, (footer_x, footer_y, footer_x + footer_w, footer_y + footer_h),
                      20, fill=CARD_BG, outline=BORDER, width=2)

    # 说明栏内容
    notes = [
        ("🔄", "数据闭环", "飞书表格为唯一数据源 → Python 脚本定时同步 → 看板自动刷新时间戳"),
        ("⚡", "零后端", "纯前端静态页面，无需数据库，无需后端服务"),
        ("📊", "双模式", "静态模式双击打开 / 服务模式 python3 serve_dashboard.py :8765"),
    ]
    note_w = footer_w // 3
    for i, (icon, title, desc) in enumerate(notes):
        nx = footer_x + i * note_w
        draw.text((nx + 30, footer_y + 16), icon, fill=TEXT_MAIN, font=FONT_CN_BIG)
        draw.text((nx + 70, footer_y + 18), title, fill=TEXT_MAIN, font=FONT_CN)
        draw.text((nx + 30, footer_y + 56), desc, fill=TEXT_MUTED, font=FONT_CN_XS)

    # 保存
    path = os.path.join(OUT_DIR, "workflow.png")
    img.save(path, "PNG", dpi=(150, 150))
    print(f"✅ 已生成: {path} ({os.path.getsize(path)//1024} KB)")
    return img


# ============================================================
# 图2: architecture.png — 系统技术架构图
# ============================================================

def draw_architecture():
    img = Image.new("RGBA", (W, H), BG)
    draw = ImageDraw.Draw(img)

    # 标题
    title_y = draw_title_block(draw, "系统技术架构图", "System Architecture — 纯前端看板 + 飞书数据管道 + Python 服务层")

    # 4 层架构
    layers = [
        {
            "name": "展示层",
            "name_en": "Presentation",
            "icon": "browser",
            "color": PRIMARY,
            "end_color": PRIMARY_END,
            "items": [
                {"icon": "dashboard", "name": "dashboard.html", "desc": "核心数据看板，含机器人工单总览、人工工单总览、知识运营分析三大模块"},
                {"icon": "dashboard", "name": "biweekly-review-dashboard.html", "desc": "重点业务域双周复盘看板（13个业务域 Tab 切换）"},
            ],
            "tech": ["Chart.js 4.4.7", "SheetJS 0.20.3", "Font Awesome 6.5", "Jaccard 语义聚类", "localStorage", "CSS3 / HTML5"],
        },
        {
            "name": "数据层",
            "name_en": "Data",
            "icon": "database",
            "color": "#5a6ff0",
            "end_color": "#8b6ff0",
            "items": [
                {"icon": "database", "name": "data_tickets.js", "desc": "机器人工单数据快照（~4,300条记录，44个字段）"},
                {"icon": "database", "name": "data_qa.js", "desc": "机器人问答数据快照（~7,000条记录，11个字段）"},
                {"icon": "database", "name": "data_manual.js", "desc": "人工工单数据快照（~5,800条记录）"},
                {"icon": "database", "name": "feishu_*.json", "desc": "飞书原始 JSON 备份 & localStorage 配置持久化"},
            ],
            "tech": ["JS 全局变量", "JSON 快照", "localStorage", "日期戳缓存"],
        },
        {
            "name": "服务层",
            "name_en": "Services",
            "icon": "server",
            "color": "#5b74f8",
            "end_color": "#9b84f8",
            "items": [
                {"icon": "python", "name": "serve_dashboard.py", "desc": "HTTP 静态文件服务器（端口 :8765），提供 POST /sync 数据同步 API"},
                {"icon": "python", "name": "refresh_feishu_data.py", "desc": "飞书数据同步脚本，拉取最新数据并更新 data_*.js 文件"},
            ],
            "tech": ["Python 3", "http.server", "subprocess", "lark-cli"],
        },
        {
            "name": "外部数据源",
            "name_en": "External",
            "icon": "feishu",
            "color": "#4f6ef7",
            "end_color": "#7c5cfc",
            "items": [
                {"icon": "spreadsheet", "name": "飞书电子表格", "desc": "机器人工单明细表 + 机器人问答明细表，实时更新"},
                {"icon": "api", "name": "飞书 Open API v2", "desc": "通过 lark-cli 命令行工具调用，获取全量表格数据"},
                {"icon": "spreadsheet", "name": "Excel 备用上传", "desc": "SheetJS 前端解析 xlsx，作为飞书不可用时的备用数据源"},
            ],
            "tech": ["Feishu API", "lark-cli", "SheetJS", "xlsx"],
        },
    ]

    layer_margin = 90
    layer_w = W - layer_margin * 2
    layer_x = layer_margin
    layer_y = title_y + 20
    layer_h = 240
    layer_gap = 24

    for idx, layer in enumerate(layers):
        ly = layer_y + idx * (layer_h + layer_gap)
        c1 = hex_to_rgb(layer["color"])
        c2 = hex_to_rgb(layer["end_color"])

        # 阴影
        draw_card_shadow(draw, layer_x, ly, layer_w, layer_h, 24)
        # 卡片
        draw_rounded_rect(draw, (layer_x, ly, layer_x + layer_w, ly + layer_h), 24, fill=CARD_BG, outline=BORDER, width=2)
        # 顶部渐变线
        draw_accent_bar(draw, layer_x, ly, layer_w)

        # 左侧层级标签
        label_x = layer_x + 36
        label_y = ly + 40
        # 图标
        draw_icon_circle(draw, label_x + 30, label_y + 36, 32, c1, c2)
        draw_icon_symbol(draw, label_x + 30, label_y + 36, layer["icon"], 22)
        # 名称
        draw.text((label_x + 80, label_y + 8), layer["name"], fill=TEXT_MAIN, font=FONT_CN_TITLE)
        draw.text((label_x + 80, label_y + 56), layer["name_en"], fill=TEXT_MUTED, font=FONT_CN_XS)

        # 分隔线
        sep_x = label_x + 210
        draw.line([(sep_x, ly + 20), (sep_x, ly + layer_h - 20)], fill=BORDER, width=2)

        # 中间组件
        items_x = sep_x + 30
        item_width = (layer_w - (sep_x - layer_x) - 30 - 280) // len(layer["items"])
        for j, item in enumerate(layer["items"]):
            ix = items_x + j * item_width
            iy = ly + 30

            # 小图标
            draw_icon_circle(draw, ix + 22, iy + 50, 20, c1, c2)
            draw_icon_symbol(draw, ix + 22, iy + 50, item["icon"], 14)

            # 名称
            item_name = item["name"]
            draw.text((ix + 52, iy + 30), item_name, fill=TEXT_MAIN, font=FONT_CN_SM)

            # 描述（自动换行）
            desc = item["desc"]
            desc_font = FONT_CN_XS
            max_desc_w = item_width - 56
            words = list(desc)
            line = ""
            desc_y = iy + 66
            for ch in words:
                test_line = line + ch
                if draw.textlength(test_line, font=desc_font) > max_desc_w and line:
                    draw.text((ix + 52, desc_y), line, fill=TEXT_MUTED, font=desc_font)
                    desc_y += 24
                    line = ch
                else:
                    line = test_line
            if line:
                draw.text((ix + 52, desc_y), line, fill=TEXT_MUTED, font=desc_font)

        # 右侧技术标签
        tech_x = layer_x + layer_w - 270
        tech_y = ly + 30
        draw.text((tech_x, tech_y), "技术栈", fill=TEXT_MUTED, font=FONT_CN_XS)
        tech_y += 30
        for tech in layer["tech"]:
            tag_font = FONT_EN_XS
            tw = draw.textlength(tech, font=tag_font)
            draw_rounded_rect(draw, (tech_x, tech_y, tech_x + tw + 20, tech_y + 26), 8, fill="#f8f9fa", outline=BORDER, width=1)
            draw.text((tech_x + 10, tech_y + 3), tech, fill=TEXT_SEC, font=tag_font)
            tech_y += 34

    # 层间箭头
    arrow_color = hex_to_rgb(ARROW_COLOR)
    for i in range(len(layers) - 1):
        ly_from = layer_y + i * (layer_h + layer_gap) + layer_h
        ly_to = layer_y + (i + 1) * (layer_h + layer_gap)
        mid_x = layer_x + layer_w // 2
        draw_dashed_arrow(draw, mid_x, ly_from + 6, mid_x, ly_to - 6, arrow_color, width=3)

    # 底部架构特征
    footer_y = layer_y + 4 * (layer_h + layer_gap) + 20
    features = ["无数据库依赖", "纯前端实现", "零构建工具", "飞书表格驱动", "支持离线静态", "lark-cli 同步"]
    fx = layer_x
    for feat in features:
        fx += draw_arch_tag(draw, fx, footer_y, feat, is_highlight=(feat == "无数据库依赖")) + 12

    # 保存
    path = os.path.join(OUT_DIR, "architecture.png")
    img.save(path, "PNG", dpi=(150, 150))
    print(f"✅ 已生成: {path} ({os.path.getsize(path)//1024} KB)")
    return img


# ============================================================
# 主入口
# ============================================================

if __name__ == "__main__":
    print("🎨 生成值班号机器人运营平台架构图...")
    print(f"   输出目录: {OUT_DIR}")
    draw_workflow()
    draw_architecture()
    print("✅ 全部完成！")