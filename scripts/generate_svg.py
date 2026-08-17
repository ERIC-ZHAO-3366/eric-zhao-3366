#!/usr/bin/env python3
"""
生成完整的 Profile SVG（和风/古风二次元风格）
- 二次元图作为全屏背景 + 渐变遮罩
- 通过 GitHub API 获取加入时间
- 下载统计卡片 / 语言卡片 SVG 并嵌套嵌入
- 贡献蛇 SVG 嵌套嵌入
- 输出 assets/profile.svg
"""
import base64
import json
import os
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

ROOT = os.path.join(os.path.dirname(__file__), "..")
CONFIG_PATH = os.path.join(ROOT, "config.json")
ASSETS_DIR = os.path.join(ROOT, "assets")
OUTPUT_SVG = os.path.join(ASSETS_DIR, "profile.svg")
WAIFU_PATH = os.path.join(ASSETS_DIR, "waifu.png")
SNAKE_PATH = os.path.join(ASSETS_DIR, "snake.svg")


def load_config():
    defaults = {
        "username": "eric-zhao-3366",
        "display_name": "Eric Zhao",
        "joined": "",
        "interests": "二次元 · 和風 · 开源 · 茶道",
        "timezone": "UTC+8 ｜ CST",
        "subtitle": "古風に舞い、コードに遊ぶ ｜ Dancing with the ancient wind, coding in the modern world.",
        "theme": "noctis_minimus",
        "quote": "「花は桜木、人は武士」",
        "quote_en": '"Of flowers, the cherry; of men, the warrior."',
    }
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            defaults.update(json.load(f))
    return defaults


CFG = load_config()
USERNAME = CFG["username"]
DISPLAY_NAME = CFG["display_name"]

CN_TZ = timezone(timedelta(hours=8))

BG = "#fbf6f0"
CARD_BG = "#ffffff"
TEXT = "#3d3329"
TEXT_LIGHT = "#7a6a5a"
ACCENT = "#bf616a"
DIVIDER = "#d8c8b8"
FONT = "'Segoe UI','Microsoft YaHei','PingFang SC','Hiragino Sans GB',sans-serif"

W = 900
H = 880


def esc(s):
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def api_headers():
    h = {
        "User-Agent": f"{USERNAME}-profile-bot/1.0",
        "Accept": "application/vnd.github+json",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def api_get(url, timeout=15):
    req = urllib.request.Request(url, headers=api_headers())
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def http_get(url, timeout=30):
    req = urllib.request.Request(
        url, headers={"User-Agent": f"{USERNAME}-profile-bot/1.0"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def fetch_joined():
    try:
        data = api_get(f"https://api.github.com/users/{USERNAME}")
        created = data.get("created_at", "")
        if created:
            dt = datetime.strptime(created, "%Y-%m-%dT%H:%M:%SZ").replace(
                tzinfo=timezone.utc
            )
            return dt.astimezone(CN_TZ).strftime("%Y-%m-%d")
        return "未知"
    except Exception as e:
        print(f"[warn] 获取加入时间失败: {e}", file=sys.stderr)
        return "未知"


def fetch_avatar_b64():
    try:
        data = api_get(f"https://api.github.com/users/{USERNAME}")
        avatar_url = data.get("avatar_url", "")
        if avatar_url:
            img_data = http_get(avatar_url, timeout=15)
            return "data:image/png;base64," + base64.b64encode(img_data).decode("ascii")
        return ""
    except Exception as e:
        print(f"[warn] 获取头像失败: {e}", file=sys.stderr)
        return ""


def fetch_recent_posts(rss_url, max_posts=4):
    """从 RSS feed 获取最近博客文章"""
    try:
        content = http_get(rss_url, timeout=15).decode("utf-8")
        root = ET.fromstring(content)
        items = root.findall(".//item")
        posts = []
        for item in items[:max_posts]:
            title = item.findtext("title", "").strip()
            link = item.findtext("link", "").strip()
            pub_date = item.findtext("pubDate", "").strip()
            date_str = ""
            if pub_date:
                try:
                    dt = parsedate_to_datetime(pub_date)
                    date_str = dt.strftime("%m-%d")
                except Exception:
                    date_str = pub_date[:10]
            posts.append({"title": title, "link": link, "date": date_str})
        return posts
    except Exception as e:
        print(f"[warn] 获取博客失败: {e}", file=sys.stderr)
        return []


def parse_svg(content_str):
    vb = re.search(r'viewBox="([^"]+)"', content_str)
    viewBox = vb.group(1) if vb else "0 0 100 100"
    inner = re.search(r"<svg[^>]*>(.*)</svg>", content_str, re.DOTALL)
    return viewBox, (inner.group(1) if inner else content_str)


def embed_svg(content_str, x, y, width, height):
    if not content_str:
        return ""
    viewBox, inner = parse_svg(content_str)
    return (
        f'<svg x="{x}" y="{y}" width="{width}" height="{height}" '
        f'viewBox="{viewBox}" preserveAspectRatio="xMidYMid meet">{inner}</svg>'
    )


def img_b64(path, mime="image/png"):
    if not os.path.exists(path):
        return ""
    with open(path, "rb") as f:
        return f"data:{mime};base64," + base64.b64encode(f.read()).decode("ascii")


def download_text(url, timeout=30):
    try:
        return http_get(url, timeout=timeout).decode("utf-8")
    except Exception as e:
        print(f"[warn] 下载失败 {url}: {e}", file=sys.stderr)
        return ""


def placeholder(x, y, w, h, text):
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{CARD_BG}" '
        f'fill-opacity="0.6" rx="12"/>'
        f'<text x="{x + w / 2}" y="{y + h / 2}" text-anchor="middle" '
        f'dominant-baseline="middle" font-family="{FONT}" font-size="14" '
        f'fill="{TEXT_LIGHT}">{esc(text)}</text>'
    )


def txt(x, y, s, size=14, color=TEXT, anchor="start", weight=None, style=None):
    attrs = (
        f'x="{x}" y="{y}" text-anchor="{anchor}" '
        f'font-family="{FONT}" font-size="{size}" fill="{color}"'
    )
    if weight:
        attrs += f' font-weight="{weight}"'
    if style:
        attrs += f' font-style="{style}"'
    return f"<text {attrs}>{esc(s)}</text>"


def card(x, y, w, h, opacity=0.62):
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" '
        f'fill="{CARD_BG}" fill-opacity="{opacity}" rx="14"/>'
    )


def generate():
    joined = CFG["joined"] if CFG.get("joined") else fetch_joined()
    avatar_b64 = fetch_avatar_b64()
    theme = CFG.get("theme", "noctis_minimus")
    waifu_b64 = img_b64(WAIFU_PATH)

    snake_svg = ""
    if os.path.exists(SNAKE_PATH):
        with open(SNAKE_PATH, "r", encoding="utf-8") as f:
            snake_svg = f.read()

    rss_url = CFG.get("rss_url", "")
    recent_posts = fetch_recent_posts(rss_url, max_posts=4) if rss_url else []
    langs_card_svg = download_text(
        f"https://github-stats-extended.vercel.app/api/top-langs/?username={USERNAME}"
        f"&theme=transparent&hide_border=true&layout=compact&langs_count=6"
    )

    now = datetime.now(CN_TZ)
    date_str = now.strftime("%Y-%m-%d %H:%M:%S")
    weekday_cn = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][now.weekday()]

    p = []
    p.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
    )

    # === 背景层 ===
    if waifu_b64:
        p.append(
            f'<image href="{waifu_b64}" x="0" y="0" width="{W}" height="{H}" '
            f'preserveAspectRatio="xMidYMid slice"/>'
        )
    else:
        p.append(f'<rect width="{W}" height="{H}" fill="{BG}"/>')

    # 渐变遮罩
    p.append(
        f'<defs><linearGradient id="ov" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0%" stop-color="{BG}" stop-opacity="0.90"/>'
        f'<stop offset="35%" stop-color="{BG}" stop-opacity="0.80"/>'
        f'<stop offset="65%" stop-color="{BG}" stop-opacity="0.80"/>'
        f'<stop offset="100%" stop-color="{BG}" stop-opacity="0.93"/>'
        f"</linearGradient></defs>"
    )
    p.append(f'<rect width="{W}" height="{H}" fill="url(#ov)"/>')

    # === 标题区（名称左 + 头像右）===
    p.append(txt(40, 58, f"🏮 {DISPLAY_NAME}", 40, TEXT, "start", "bold"))
    p.append(
        txt(
            40,
            88,
            CFG.get("subtitle", "古風に舞い、コードに遊ぶ ｜ Dancing with the ancient wind, coding in the modern world."),
            13,
            TEXT_LIGHT,
            "start",
        )
    )
    # GitHub 头像（圆形，右上）
    if avatar_b64:
        p.append(
            f'<defs><clipPath id="av"><circle cx="838" cy="52" r="40"/></clipPath></defs>'
        )
        p.append(
            f'<image href="{avatar_b64}" x="798" y="12" width="80" height="80" '
            f'clip-path="url(#av)"/>'
        )
        p.append(
            f'<circle cx="838" cy="52" r="41" fill="none" '
            f'stroke="{DIVIDER}" stroke-width="2"/>'
        )
    # 装饰线
    p.append(
        f'<line x1="40" y1="108" x2="{W - 40}" y2="108" '
        f'stroke="{DIVIDER}" stroke-width="1"/>'
    )

    # === 个人信息卡片 ===
    cx, cy, cw, ch = 40, 125, 820, 170
    p.append(card(cx, cy, cw, ch))
    p.append(txt(cx + 30, cy + 32, "🌸 关于我 ｜ About Me", 20, TEXT, "start", "bold"))

    # 两列信息
    left_x = cx + 30
    right_x = cx + 430
    row1_y = cy + 68
    row2_y = cy + 128

    info = [
        (left_x, row1_y, "👤 用户名 ｜ Username", DISPLAY_NAME),
        (right_x, row1_y, "📅 加入时间 ｜ Joined GitHub", joined),
        (left_x, row2_y, "🌱 兴趣 ｜ Interests", CFG.get("interests", "二次元 · 和風 · 开源 · 茶道")),
        (right_x, row2_y, "🌍 时区 ｜ Timezone", CFG.get("timezone", "UTC+8 ｜ CST")),
    ]
    for x, y, label, value in info:
        p.append(txt(x, y, label, 12, ACCENT, "start", "bold"))
        p.append(txt(x, y + 24, value, 16, TEXT, "start"))

    # === 最近博客 + 语言卡片 ===
    sy = 320
    sh = 175
    # 左列：最近博客
    p.append(card(40, sy, 400, sh))
    p.append(txt(70, sy + 28, "📝 最近博客 ｜ Recent Posts", 16, TEXT, "start", "bold"))
    if recent_posts:
        py = sy + 58
        for post in recent_posts:
            title = post["title"]
            if len(title) > 28:
                title = title[:27] + "…"
            p.append(txt(70, py, title, 12, TEXT, "start"))
            if post["date"]:
                p.append(txt(420 - 20, py, post["date"], 11, TEXT_LIGHT, "end"))
            py += 28
    else:
        p.append(txt(70, sy + 90, "暂无文章 ｜ No posts found", 13, TEXT_LIGHT, "start"))

    # 右列：语言卡片
    if langs_card_svg:
        p.append(embed_svg(langs_card_svg, 460, sy, 400, sh))
    else:
        p.append(placeholder(460, sy, 400, sh, "💻 语言卡片加载中…"))

    # === 贡献蛇 ===
    p.append(txt(W / 2, 528, "🐍 贡献蛇 ｜ Contribution Snake", 20, TEXT, "middle", "bold"))
    if snake_svg:
        p.append(embed_svg(snake_svg, 40, 545, 820, 140))
    else:
        p.append(placeholder(40, 545, 820, 140, "🎋 贡献蛇生成中…"))

    # === 底部 ===
    p.append(
        txt(
            W / 2,
            720,
            f"🕐 最后更新 ｜ Last updated: {date_str} CST（{weekday_cn}）",
            13,
            TEXT_LIGHT,
            "middle",
        )
    )
    p.append(
        txt(W / 2, 760, CFG.get("quote", "「花は桜木、人は武士」"), 15, ACCENT, "middle", style="italic")
    )
    p.append(
        txt(
            W / 2,
            785,
            CFG.get("quote_en", '"Of flowers, the cherry; of men, the warrior."'),
            11,
            TEXT_LIGHT,
            "middle",
        )
    )
    p.append(txt(W / 2, 825, "🏮 · 🌸 · 🎎 · 🍵 · 🎐 · 🏯 · 🎋 · 🌙", 15, ACCENT, "middle"))

    p.append("</svg>")

    os.makedirs(ASSETS_DIR, exist_ok=True)
    with open(OUTPUT_SVG, "w", encoding="utf-8") as f:
        f.write("\n".join(p))

    size_kb = os.path.getsize(OUTPUT_SVG) / 1024
    print(f"[ok] SVG 已生成: {OUTPUT_SVG} ({size_kb:.1f} KB)")
    print(f"     显示名: {DISPLAY_NAME}")
    print(f"     加入: {joined}")
    return 0


if __name__ == "__main__":
    sys.exit(generate())
