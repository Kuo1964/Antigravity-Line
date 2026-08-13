import os
import logging
from typing import Optional
from app.services.mac_unlocker import mac_unlocker
from app.services.macos_ui_adapter import macos_ui_adapter
from app.services.image_crawler import image_crawler

logger = logging.getLogger("mac_system_gateway")

class MacSystemGateway:
    """
    高槓桿、深介面 MacSystemGateway 模組。
    統一管理 macOS 電腦螢幕狀態檢查、自動鎖定解鎖、狀態保存復原與多來源早安圖片抓取。
    """

    def __init__(self):
        self._unlocker = mac_unlocker
        self._ui_adapter = macos_ui_adapter
        self._crawler = image_crawler

    def get_current_screen_state(self) -> str:
        """取得當前螢幕狀態"""
        return "LOCKED" if self._unlocker.is_screen_locked() else "UNLOCKED"

    def ensure_unlocked_and_ready(self, password: str = "") -> bool:
        """
        深層公開主介面：確保 Mac 處於解鎖並已準備好的狀態。
        自動處理解鎖鍵盤輸入、狀態記錄與錯誤備援。
        """
        try:
            self._ui_adapter.save_screen_state()
            success = self._unlocker.ensure_unlocked(password)
            if success:
                logger.info("macOS 螢幕處於開啟用戶端狀態，系統準備完畢")
                return True
            else:
                logger.warning("macOS 螢幕解鎖失敗或處於非防護狀態")
                return False
        except Exception as e:
            logger.error(f"MacSystemGateway 執行解鎖準備過程發生異常: {e}")
            return False

    def restore_display_state(self, initial_state: str = "UNLOCKED") -> bool:
        """深層公開主介面：復原之前的螢幕與電源狀態"""
        try:
            self._ui_adapter.restore_screen_state()
            if initial_state == "LOCKED":
                return self._unlocker.lock_screen()
            return True
        except Exception as e:
            logger.error(f"復原 macOS 螢幕狀態失敗: {e}")
            return False

    def fetch_morning_media(self, keyword: str = "good morning", target_dir: Optional[str] = None) -> Optional[str]:
        """
        深層公開主介面：抓取並快取高品質早安圖片。
        對外隱藏 Unsplash / Bing 圖片爬取重試、快取檢驗與浮水印處理細節。
        """
        try:
            image_path = self._crawler.get_morning_image(keyword=keyword, save_dir=target_dir)
            if image_path and os.path.exists(image_path):
                logger.info(f"成功透過 MacSystemGateway 取得早安圖片: {image_path}")
                return image_path
        except Exception as e:
            logger.error(f"MacSystemGateway 抓取早安圖片失敗: {e}")
        return None

mac_system_gateway = MacSystemGateway()
