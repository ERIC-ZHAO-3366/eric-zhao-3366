"""
每日获取二次元图片（SFW）
使用 nekos.life 等对 GitHub Actions 云 IP 友好的稳定图源
原 Konachan/yande.re 会封禁 Azure IP 段（返回 400），waifu.pics 服务已异常，均已弃用
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
    "User-Agent": "eric-zhao-3366-profile-bot/1.0 (https://github.com/eric-zhao-3366)",
    "Accept": "application/json",
}


def load_waifu_tags():
    defaults = ["waifu", "neko", "fox_girl", "gecg"]
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        tags = cfg.get("waifu_tags")
        if tags:
            return tags
    return defaults


WAIFU_TAGS = load_waifu_tags()


def safe_request(url, timeout=20, retries=3):
    last_err = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except Exception as e:
            last_err = e
            if attempt < retries - 1:
                wait = 2 * (attempt + 1)
                print(f"  请求失败({attempt + 1}/{retries}): {e}，{wait}s 后重试...")
                time.sleep(wait)
    raise last_err


def fetch_from_nekos_life():
    """nekos.life - 稳定的 SFW 二次元图片 API
    端点：waifu, neko, fox_girl, gecg 等
    返回 {"url": "https://cdn.nekos.life/..."}
    """
    endpoint = random.choice(WAIFU_TAGS)
    url = f"https://nekos.life/api/v2/img/{endpoint}"
    print(f"  端点: {endpoint}")
    data = json.loads(safe_request(url).decode("utf-8"))
    img_url = data.get("url")
    if not img_url:
        return None
    return {
        "image": img_url,
        "source": "nekos.life",
        "tags": endpoint,
        "id": None,
        "page": img_url,
    }


def fetch_from_nekos_life_neko():
    """nekos.life 备用：固定 neko 端点"""
    url = "https://nekos.life/api/v2/img/neko"
    data = json.loads(safe_request(url).decode("utf-8"))
    img_url = data.get("url")
    if not img_url:
        return None
    return {
        "image": img_url,
        "source": "nekos.life",
        "tags": "neko",
        "id": None,
        "page": img_url,
    }


def fetch_from_nekos_life_waifu():
    """nekos.life 备用：固定 waifu 端点"""
    url = "https://nekos.life/api/v2/img/waifu"
    data = json.loads(safe_request(url).decode("utf-8"))
    img_url = data.get("url")
    if not img_url:
        return None
    return {
        "image": img_url,
        "source": "nekos.life",
        "tags": "waifu",
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
    providers = [
        fetch_from_nekos_life,
        fetch_from_nekos_life_neko,
        fetch_from_nekos_life_waifu,
    ]
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

    if os.path.exists(OUTPUT_PATH):
        print(
            f"所有图源均失败，保留现有图片: {OUTPUT_PATH}",
            file=sys.stderr,
        )
        return 0

    print(f"所有图源均失败且无现有图片: {last_err}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
