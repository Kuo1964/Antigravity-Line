import os
import logging
import time
import re
import urllib.parse
import requests
import subprocess
from typing import Optional
logger = logging.getLogger("image_crawler")

class ImageCrawler:
    """早安圖片爬蟲模組，負責取得與快取網路早安風景圖片"""

    def search_bing_good_morning_image(self) -> Optional[str]:
        """從 Bing 搜尋有『早安』字樣的圖片 URL"""
        keywords = ["早安圖 一切順心", "早安 順心如意", "早安 平安喜樂", "早安 祝賀圖"]
        day_index = int(time.time() / 86400)
        query_word = keywords[day_index % len(keywords)]
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        encoded_query = urllib.parse.quote(query_word)
        search_url = f"https://www.bing.com/images/async?q={encoded_query}&first=1&count=25"
        
        logger.info(f"正在搜尋網路最新中文早安圖 (關鍵字: '{query_word}')...")
        try:
            resp = requests.get(search_url, headers=headers, timeout=12.0)
            if resp.status_code == 200:
                urls = re.findall(r'&quot;murl&quot;:&quot;(https?://[^&]+)&quot;', resp.text)
                valid_urls = [u for u in urls if u.lower().endswith(('.jpg', '.jpeg', '.png')) and "bing.com" not in u]
                if valid_urls:
                    selected_url = valid_urls[day_index % len(valid_urls)]
                    logger.info(f"找到符合的線上早安圖 URL: {selected_url}")
                    return selected_url
        except Exception as e:
            logger.warning(f"Bing 早安圖搜尋失敗: {e}")
        return None

    def get_morning_image(self, keyword: str = "good morning", save_dir: Optional[str] = None) -> Optional[str]:
        """抓取網路早安圖片"""
        if not save_dir:
            save_dir = "/tmp/morning_images"
        os.makedirs(save_dir, exist_ok=True)
        
        target_path = os.path.join(save_dir, "morning_latest.jpg")
        
        def download_and_verify(url: str) -> bool:
            try:
                resp = requests.get(url, timeout=10)
                content_type = resp.headers.get("Content-Type", "")
                if resp.status_code == 200 and "image" in content_type.lower() and len(resp.content) > 1024:
                    with open(target_path, "wb") as f:
                        f.write(resp.content)
                    return True
                logger.warning(f"無效的圖片回應 (狀態碼: {resp.status_code}, 類型: {content_type}, 大小: {len(resp.content) if hasattr(resp, 'content') else 0} bytes)")
                return False
            except Exception as e:
                logger.warning(f"圖片下載發生例外錯誤: {e}")
                return False
        
        # 優先嘗試 Bing 中文早安圖搜尋
        online_url = self.search_bing_good_morning_image()
        if online_url and download_and_verify(online_url):
            logger.info(f"成功下載並快取 Bing 早安圖片至: {target_path}")
            return target_path
            
        # 備用方案: Unsplash
        logger.info("Bing 圖片無效或下載失敗，切換使用備用 Unsplash 風景圖")
        backup_url = "https://images.unsplash.com/photo-1470252649378-9c29740c9fa8?auto=format&fit=crop&w=1000&q=80"
        if download_and_verify(backup_url):
            logger.info(f"成功下載並快取 Unsplash 早安圖片至: {target_path}")
            return target_path
            
        logger.error("所有圖片下載方案皆失敗！")
        return None

image_crawler = ImageCrawler()

def fetch_latest_good_morning_image(save_dir: Optional[str] = None) -> Optional[str]:
    return image_crawler.get_morning_image(save_dir=save_dir)

def copy_image_to_clipboard(image_path: str) -> bool:
    logger.info(f"準備寫入圖片至剪貼簿: {image_path}")
    try:
        if not os.path.exists(image_path):
            logger.error(f"圖片檔案不存在: {image_path}")
            return False
        script = f'set the clipboard to (read (POSIX file "{image_path}") as JPEG picture)'
        subprocess.run(["osascript", "-e", script], check=True)
        return True
    except Exception as e:
        logger.error(f"圖片寫入剪貼簿失敗: {e}")
        return False
