import os
import time
import httpx
import logging
import subprocess
from typing import Optional, List

logger = logging.getLogger(__name__)

import re

# 經典長輩風格中文早安祝賀圖備用庫 (藍天花草 + 中文早安祝賀語)
CLASSIC_GOOD_MORNING_CARDS: List[str] = [
    "https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=1200&auto=format&fit=crop&q=80",
    "https://images.unsplash.com/photo-1518241353330-0f7941c2d9b5?w=1200&auto=format&fit=crop&q=80",
    "https://images.unsplash.com/photo-1499346030926-9a72daac6c63?w=1200&auto=format&fit=crop&q=80",
    "https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=1200&auto=format&fit=crop&q=80"
]

def search_bing_good_morning_image() -> Optional[str]:
    """
    從 Bing Image Search 即時搜尋線上記錄有『早安 一切順心』經典風格的圖片 URL
    """
    keywords = ["早安圖 一切順心", "早安 順心如意", "早安 平安喜樂", "早安 祝賀圖"]
    day_index = int(time.time() / 86400)
    query_word = keywords[day_index % len(keywords)]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    search_url = f"https://www.bing.com/images/async?q={httpx.URL(query_word).raw_path.decode()}&first=1&count=25"
    logger.info(f"正在搜尋網路最新中文早安圖 (關鍵字: '{query_word}')...")
    
    try:
        with httpx.Client(headers=headers, timeout=12.0, follow_redirects=True) as client:
            res = client.get(search_url)
            if res.status_code == 200:
                # 提取所有的 murl (Media URL)
                urls = re.findall(r'&quot;murl&quot;:&quot;(https?://[^&]+)&quot;', res.text)
                # 過濾出長相合格的 jpg/png 圖片 URL
                valid_urls = [u for u in urls if u.lower().endswith(('.jpg', '.jpeg', '.png')) and "bing.com" not in u]
                if valid_urls:
                    selected_url = valid_urls[day_index % len(valid_urls)]
                    logger.info(f"找到符合的線上早安圖 URL: {selected_url}")
                    return selected_url
    except Exception as e:
        logger.warning(f"Bing 圖片即時搜尋失敗: {e}")

    return None

def fetch_latest_good_morning_image(save_dir: str = "temp") -> str:
    """
    搜尋並下載當日最新的『早安 一切順心』風格圖片
    :param save_dir: 圖片儲存目錄
    :return: 下載後的圖片絕對路徑
    """
    abs_save_dir = os.path.abspath(save_dir)
    os.makedirs(abs_save_dir, exist_ok=True)
    target_path = os.path.join(abs_save_dir, "good_morning_latest.jpg")

    # 1. 優先從 Bing 即時搜尋線上經典早安圖
    online_url = search_bing_good_morning_image()
    
    downloaded = False
    if online_url:
        with httpx.Client(timeout=15.0, follow_redirects=True) as client:
            try:
                res = client.get(online_url)
                if res.status_code == 200 and len(res.content) > 10000:
                    with open(target_path, "wb") as f:
                        f.write(res.content)
                    logger.info(f"成功下載網路搜尋到的中文早安圖: {target_path}")
                    downloaded = True
            except Exception as e:
                logger.warning(f"下載線上搜尋圖片失敗: {e}")

    # 2. 備用方案：輪播下載經典庫
    if not downloaded:
        logger.info("採用備用線上早安圖庫...")
        day_index = int(time.time() / 86400)
        fallback_url = CLASSIC_GOOD_MORNING_CARDS[day_index % len(CLASSIC_GOOD_MORNING_CARDS)]
        with httpx.Client(timeout=15.0, follow_redirects=True) as client:
            try:
                res = client.get(fallback_url)
                if res.status_code == 200:
                    with open(target_path, "wb") as f:
                        f.write(res.content)
                    logger.info(f"成功下載備用早安圖: {target_path}")
                    downloaded = True
            except Exception as e:
                logger.error(f"下載備用圖片失敗: {e}")

    if not os.path.exists(target_path):
        raise FileNotFoundError("無法取得早安祝賀圖片，請檢查網路連線。")

    return target_path


def copy_image_to_clipboard(image_path: str) -> bool:
    """
    將指定圖片檔案寫入 macOS 系統剪貼簿 (Clipboard)
    :param image_path: 圖片絕對路徑
    :return: 是否成功寫入剪貼簿
    """
    abs_path = os.path.abspath(image_path)
    if not os.path.exists(abs_path):
        logger.error(f"圖片不存在: {abs_path}")
        return False

    ext = os.path.splitext(abs_path)[1].lower()
    image_type = "JPEG picture" if ext in ['.jpg', '.jpeg'] else "«class PNG »"

    logger.info(f"正在將圖片寫入 macOS 剪貼簿 ({abs_path})...")
    try:
        applescript_cmd = f'''
        set theFile to (POSIX file "{abs_path}")
        set the clipboard to (read theFile as {image_type})
        '''
        res = subprocess.run(["osascript", "-e", applescript_cmd], capture_output=True, text=True)
        if res.returncode == 0:
            logger.info("圖片已成功寫入 macOS 系統剪貼簿！")
            return True
        else:
            logger.error(f"寫入剪貼簿失敗: {res.stderr}")
            return False
    except Exception as e:
        logger.error(f"執行 AppleScript 寫入剪貼簿異常: {e}")
        return False
