import os
import time
import httpx
import logging
import subprocess
from typing import Optional, List

logger = logging.getLogger(__name__)

import glob
from icrawler.builtin import BingImageCrawler

def fetch_latest_good_morning_image(save_dir: str = "temp") -> str:
    """
    產生當日最新的早安圖 (使用 icrawler 爬取 Bing 現成早安圖)
    """
    abs_save_dir = os.path.abspath(save_dir)
    os.makedirs(abs_save_dir, exist_ok=True)
    
    import datetime
    import random
    
    # 檢查是否已有今日下載好的快取圖片
    today = datetime.datetime.now().date()
    existing_latest = glob.glob(os.path.join(abs_save_dir, "good_morning_latest.*"))
    if existing_latest:
        latest_file = existing_latest[0]
        file_mtime = datetime.datetime.fromtimestamp(os.path.getmtime(latest_file)).date()
        if file_mtime == today:
            logger.info(f"偵測到今日已下載過圖片 ({latest_file})，直接使用快取，跳過網路爬取！")
            return latest_file

    # 清空暫存資料夾內舊的圖片 (新的一天，清空昨天的舊圖)
    for old_file in glob.glob(os.path.join(abs_save_dir, "*.*")):
        try:
            if os.path.isfile(old_file):
                os.remove(old_file)
        except Exception:
            pass
    
    # 建立動態關鍵字，加入今天的星期幾，增加搜尋多樣性
    weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    today_weekday = weekdays[datetime.datetime.now().weekday()]
    dynamic_keyword = f"早安 風景 {today_weekday}"
    
    logger.info(f"正在使用 icrawler 搜尋網路早安圖 (關鍵字: '{dynamic_keyword}')...")
    
    try:
        # 設定 icrawler 將檔案存入指定資料夾
        crawler = BingImageCrawler(storage={"root_dir": abs_save_dir})
        
        # 爬取 10 張圖片
        crawler.crawl(keyword=dynamic_keyword, max_num=10)
        
        # 尋找下載的圖片
        downloaded_files = glob.glob(os.path.join(abs_save_dir, "0000*.*"))
        if not downloaded_files:
            raise FileNotFoundError("icrawler 未能下載任何圖片。")
            
        # 過濾下載的圖片，確保檔案大小大於 30 KB (30720 bytes)，避免選到破圖
        valid_images = []
        for img in downloaded_files:
            if os.path.exists(img) and os.path.getsize(img) > 30720:
                valid_images.append(img)
                
        if not valid_images:
            raise FileNotFoundError("icrawler 未能下載任何完整的圖片 (或皆小於 30 KB)。")
            
        # 隨機挑選一張圖片
        selected_img = random.choice(valid_images)
        logger.info(f"從 {len(valid_images)} 張完整圖片中隨機選中: {os.path.basename(selected_img)}")
        
        ext = os.path.splitext(selected_img)[1]
        target_path = os.path.join(abs_save_dir, f"good_morning_latest{ext}")
        
        # 將選中的圖片複製並命名為我們的標準檔名 (不刪除原檔供後續檢查)
        import shutil
        shutil.copy2(selected_img, target_path)
        
        # (V10: 取消刪除其他未選中與舊圖片的動作，保留供使用者後續檢查與驗屍)
                    
        logger.info(f"早安圖網路抓取成功！已儲存至: {target_path}")
        return target_path
        
    except Exception as e:
        logger.error(f"網路爬取早安圖失敗: {e}")
        raise RuntimeError(f"圖片爬取完全失敗: {e}")


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
