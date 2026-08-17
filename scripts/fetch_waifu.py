"""
每日获取和风/古风二次元图片
优先从 Konachan 搜索 kimono/japanese_style 标签，失败则 fallback 到 waifu.pics
"""
import json
import os
import random
import sys
import time
import urllib.request
import urllib.error

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "assets")
OUTPUT_PATH = os.path.join(ASSETS_DIR, "waifu.png")
META_PATH = os.path.join(ASSETS_DIR, "waifu_meta.json")
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config.json")

HEADERS = {
    "User-Agent": "eric-zhao-3366-profile-bot/1.0 (https://github.com/eric-zhao-3366)"
}


def load_waifu_tags():
    defaults = ["kimono", "yukata", "japanese_clothes", "traditional_clothes", "fan"]
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        tags = cfg.get("waifu_tags")
        if tags:
            return tags
    return defaults


WAIFU_TAGS = load_waifu_tags()


def safe_request(url, timeout=20):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def fetch_from_konachan():
    """从 Konachan 搜索和风/古风标签的图片（sfw）"""
    tags = random.choice(WAIFU_TAGS)
    url = (
        f"https://konachan.com/post.json?tags={tags}%20rating:safe%20width:>=1000&limit=20"
    )
    data = json.loads(safe_request(url).decode("utf-8"))
    if not data:
        return None
    item = random.choice(data)
    img_url = item.get("file_url") or item.get("sample_url")
    if not img_url:
        return None
    return {
        "image": img_url,
        "source": "konachan",
        "tags": item.get("tags", ""),
        "id": item.get("id"),
        "page": f"https://konachan.com/post/show/{item.get('id')}",
    }


def fetch_from_yandere():
    """从 yande.re 搜索和风标签（sfw）"""
    tags = random.choice(WAIFU_TAGS[:3])
    url = f"https://yande.re/post.json?tags={tags}%20rating:safe%20width:>=1000&limit=20"
    data = json.loads(safe_request(url).decode("utf-8"))
    if not data:
        return None
    item = random.choice(data)
    img_url = item.get("file_url") or item.get("sample_url")
    if not img_url:
        return None
    return {
        "image": img_url,
        "source": "yandere",
        "tags": item.get("tags", ""),
        "id": item.get("id"),
        "page": f"https://yande.re/post/show/{item.get('id')}",
    }


def fetch_from_waifu_pics():
    """fallback：waifu.pics 随机图"""
    url = "https://waifu.pics/api/sfw/waifu"
    data = json.loads(safe_request(url).decode("utf-8"))
    img_url = data.get("url")
    if not img_url:
        return None
    return {
        "image": img_url,
        "source": "waifu.pics",
        "tags": "",
        "id": None,
        "page": img_url,
    }


def download_image(url, dest):
    content = safe_request(url, timeout=60)
    with open(dest, "wb") as f:
        f.write(content)
    return len(content)


def main():
    os.makedirs(ASSETS_DIR, exist_ok=True)
    providers = [fetch_from_konachan, fetch_from_yandere, fetch_from_waifu_pics]
    last_err = None
    for provider in providers:
        try:
            print(f"尝试从 {provider.__name__} 获取图片...")
            meta = provider()
            if not meta:
                print(f"{provider.__name__} 无结果，尝试下一个")
                continue
            print(f"下载图片: {meta['image']}")
            size = download_image(meta["image"], OUTPUT_PATH)
            meta["size_bytes"] = size
            meta["fetched_at"] = int(time.time())
            with open(META_PATH, "w", encoding="utf-8") as f:
                json.dump(meta, f, ensure_ascii=False, indent=2)
            print(f"成功保存图片 ({size} bytes) 来自 {meta['source']}")
            return 0
        except Exception as e:
            last_err = e
            print(f"{provider.__name__} 失败: {e}", file=sys.stderr)
            continue
    print(f"所有图源均失败: {last_err}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
