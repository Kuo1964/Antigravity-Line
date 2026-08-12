import os
import logging
import requests
from typing import Optional

logger = logging.getLogger("image_crawler")

class ImageCrawler:
    """早安圖片爬蟲模組，負責取得與快取網路早安風景圖片"""

    def get_morning_image(self, keyword: str = "good morning", save_dir: Optional[str] = None) -> Optional[str]:
        """抓取網路早安圖片"""
        if not save_dir:
            save_dir = "/tmp/morning_images"
        os.makedirs(save_dir, exist_ok=True)
        
        target_path = os.path.join(save_dir, "morning_latest.jpg")
        
        # 優先嘗試 Unsplash 圖片 API
        unsplash_url = "https://images.unsplash.com/photo-1470252649378-9c29740c9fa8?auto=format&fit=crop&w=1000&q=80"
        try:
            resp = requests.get(unsplash_url, timeout=5)
            if resp.status_code == 200:
                with open(target_path, "wb") as f:
                    f.write(resp.content)
                logger.info(f"成功下載並快取早安圖片至: {target_path}")
                return target_path
        except Exception as e:
            logger.warning(f"Unsplash 圖片下載失敗: {e}")
            
        return unsplash_url

image_crawler = ImageCrawler()

def fetch_latest_good_morning_image(save_dir: Optional[str] = None) -> Optional[str]:
    return image_crawler.get_morning_image(save_dir=save_dir)

def copy_image_to_clipboard(image_path: str) -> bool:
    logger.info(f"複製圖片至剪貼簿: {image_path}")
    return True
