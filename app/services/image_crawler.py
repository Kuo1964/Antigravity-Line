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
    """早安圖片爬蟲模組，負責取得與快取網路生動感性早安祝賀圖片"""

    def search_bing_good_morning_images(self) -> list[str]:
        """從 Bing 搜尋豐富感性、溫馨語錄字樣的早安圖片候選清單"""
        # 精選感性、生動、溫暖心靈小語與花卉唯美關鍵字
        keywords = [
            "早安 溫馨問候語 唯美圖片",
            "早安 心靈小語 圖片 花卉",
            "日安 治癒系 祝福語 圖片",
            "早安 感恩相遇 平安喜樂 圖片",
            "早安 正能量 唯美語錄圖",
            "早安 順心如意 唯美插畫",
            "早安 一切順心 溫暖問候",
            "早安 祝福語 圖片 花瓶"
        ]
        # 依據日期與時段輪替關鍵字
        time_seed = int(time.time() / 43200) # 每 12 小時切換一組風格
        query_word = keywords[time_seed % len(keywords)]
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7"
        }
        encoded_query = urllib.parse.quote(query_word)
        search_url = f"https://www.bing.com/images/async?q={encoded_query}&first=1&count=35"
        
        logger.info(f"正在搜尋網路生動感性中文早安圖 (關鍵字: '{query_word}')...")
        try:
            resp = requests.get(search_url, headers=headers, timeout=12.0)
            if resp.status_code == 200:
                urls = re.findall(r'&quot;murl&quot;:&quot;(https?://[^&]+)&quot;', resp.text)
                # 過濾明顯無效或容易阻擋的網域
                valid_urls = [
                    u for u in urls 
                    if u.lower().endswith(('.jpg', '.jpeg', '.png')) 
                    and "bing.com" not in u 
                    and "pngtree.com" not in u # 排除經常 403 的特定圖庫
                ]
                if valid_urls:
                    logger.info(f"成功取得 {len(valid_urls)} 張候選早安祝賀圖清單")
                    return valid_urls
        except Exception as e:
            logger.warning(f"Bing 早安圖搜尋失敗: {e}")
        return []

    def get_morning_image(self, keyword: str = "good morning", save_dir: Optional[str] = None) -> Optional[str]:
        """抓取並下載最佳早安圖片（具備自動輪詢重試與感性備援機制）"""
        if not save_dir:
            save_dir = "/tmp/morning_images"
        os.makedirs(save_dir, exist_ok=True)
        
        target_path = os.path.join(save_dir, "morning_latest.jpg")
        
        # 擬真請求標頭以避免 403 阻擋
        download_headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8"
        }

        def download_and_verify(url: str) -> bool:
            try:
                resp = requests.get(url, headers=download_headers, timeout=8.0)
                content_type = resp.headers.get("Content-Type", "")
                if resp.status_code == 200 and "image" in content_type.lower() and len(resp.content) > 5120:
                    with open(target_path, "wb") as f:
                        f.write(resp.content)
                    return True
                logger.warning(f"跳過無效圖片 ({url[:45]}...) -> HTTP {resp.status_code}, 類型: {content_type}, 大小: {len(resp.content) if hasattr(resp, 'content') else 0} bytes")
                return False
            except Exception as e:
                logger.warning(f"下載候選圖片失敗 ({url[:45]}...): {e}")
                return False
        
        # 1. 優先從 Bing 候選清單中依序輪詢下載
        candidate_urls = self.search_bing_good_morning_images()
        if candidate_urls:
            # 根據當天日期偏移隨機起點，避免每次都拿第一張
            offset = int(time.time() / 86400) % len(candidate_urls)
            ordered_candidates = candidate_urls[offset:] + candidate_urls[:offset]
            
            for idx, candidate_url in enumerate(ordered_candidates[:10], start=1):
                logger.info(f"嘗試下載第 {idx} 張候選早安圖: {candidate_url[:60]}...")
                if download_and_verify(candidate_url):
                    logger.info(f"🎉 成功下載並快取高品質早安祝賀圖至: {target_path}")
                    return target_path
                    
        # 2. 備援方案：若搜尋全數失敗，使用高品質中文感性祝賀圖庫輪播
        logger.info("網路搜尋候選圖全數下載失敗，啟用精選感性早安圖庫備援...")
        backup_gallery = [
            "https://sticker.fpg.com.tw/sticker/daily-photo/daily-photo-725.jpg",
            "https://sticker.fpg.com.tw/sticker/daily-photo/daily-photo-683.jpg",
            "https://img.bc3ts.net/image/post/tumb/1765590110038_abcdc8f3-e968-4d39-8d23-dc0b51dde56f.jpg",
            "https://img.bc3ts.net/image/post/tumb/sdsBtouPZjXcYHER2onU1Ptni3p1_1604620364325_440b0acf-c140-4597-bc46-7f385fc6e142.jpg"
        ]
        backup_index = int(time.time() / 86400) % len(backup_gallery)
        selected_backup = backup_gallery[backup_index]
        
        if download_and_verify(selected_backup):
            logger.info(f"成功下載並快取精選備援早安祝賀圖至: {target_path}")
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
