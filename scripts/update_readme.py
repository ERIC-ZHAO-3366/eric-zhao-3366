"""
更新 README.md 中的动态内容：
- 最后更新时间戳
- 二次元图片来源链接
- GitHub 加入时间（通过 API 查询）
"""
import json
import os
import re
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta

ROOT = os.path.join(os.path.dirname(__file__), "..")
README_PATH = os.path.join(ROOT, "README.md")
META_PATH = os.path.join(ROOT, "assets", "waifu_meta.json")
USERNAME = "eric-zhao-3366"

CN_TZ = timezone(timedelta(hours=8))
HEADERS = {
    "User-Agent": "eric-zhao-3366-profile-bot/1.0",
    "Accept": "application/vnd.github+json",
}


def load_meta():
    if not os.path.exists(META_PATH):
        return None
    with open(META_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def fetch_joined_date():
    """通过 GitHub API 查询用户加入时间"""
    url = f"https://api.github.com/users/{USERNAME}"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    created = data.get("created_at", "")
    if not created:
        return None
    dt = datetime.strptime(created, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    return dt.astimezone(CN_TZ).strftime("%Y-%m-%d")


def update_readme():
    if not os.path.exists(README_PATH):
        print("README.md 不存在", file=sys.stderr)
        return 1
    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    now = datetime.now(CN_TZ)
    date_str = now.strftime("%Y-%m-%d %H:%M:%S")
    weekday_cn = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][now.weekday()]
    weekday_en = now.strftime("%A")

    content = re.sub(
        r"<!-- LAST_UPDATED:start -->.*?<!-- LAST_UPDATED:end -->",
        f"<!-- LAST_UPDATED:start -->{date_str} CST（{weekday_cn} / {weekday_en}）<!-- LAST_UPDATED:end -->",
        content,
        flags=re.DOTALL,
    )

    try:
        joined = fetch_joined_date()
        if joined:
            content = re.sub(
                r"<!-- JOINED:start -->.*?<!-- JOINED:end -->",
                f"<!-- JOINED:start -->`{joined}`<!-- JOINED:end -->",
                content,
                flags=re.DOTALL,
            )
            print(f"加入时间已更新: {joined}")
    except Exception as e:
        print(f"查询加入时间失败: {e}", file=sys.stderr)

    meta = load_meta()
    source_line = "今日图片来自 `waifu.pics`（默认）"
    if meta:
        source = meta.get("source", "unknown")
        page = meta.get("page", "")
        tags = meta.get("tags", "")
        if source in ("konachan", "yandere"):
            tag_str = ", ".join([t for t in tags.split() if t][:5]) if tags else ""
            source_line = f"今日图片来自 `{source}` [{meta.get('id','')}]({page})"
            if tag_str:
                source_line += f"  ·  标签: {tag_str}"
        else:
            source_line = f"今日图片来自 `{source}`"
    content = re.sub(
        r"<!-- IMAGE_SOURCE:start -->.*?<!-- IMAGE_SOURCE:end -->",
        f"<!-- IMAGE_SOURCE:start -->{source_line}<!-- IMAGE_SOURCE:end -->",
        content,
        flags=re.DOTALL,
    )

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"README 已更新，时间戳: {date_str}")
    return 0


if __name__ == "__main__":
    sys.exit(update_readme())
