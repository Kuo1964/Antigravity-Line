import unittest
from unittest.mock import patch
from app.services.macos_ui_adapter import macos_ui_adapter

class TestMacOSUIAdapter(unittest.TestCase):
    """
    測試 MacOSUIAdapter 視窗座標取得與過濾邏輯
    """

    @patch("Quartz.CGWindowListCopyWindowInfo")
    def test_get_window_bounds_prefers_main_window_over_auxiliary(self, mock_cg):
        """
        驗證當存在 500x500 輔助視窗與主視窗時，優先排除輔助視窗並選取面積最大/名稱相符的主視窗
        """
        mock_cg.return_value = [
            # 輔助視窗 (Layer: 0, 500x500, x=0, y=482, Name="")
            {
                "kCGWindowOwnerName": "LINE",
                "kCGWindowName": "",
                "kCGWindowLayer": 0,
                "kCGWindowBounds": {"X": 0, "Y": 482, "Width": 500, "Height": 500}
            },
            # 真正的主視窗 (Layer: 0, 946x889, x=221, y=92, Name="LINE")
            {
                "kCGWindowOwnerName": "LINE",
                "kCGWindowName": "LINE",
                "kCGWindowLayer": 0,
                "kCGWindowBounds": {"X": 221, "Y": 92, "Width": 946, "Height": 889}
            }
        ]

        bounds = macos_ui_adapter.get_window_bounds("LINE")
        self.assertEqual(bounds, (221, 92, 946, 889))

    @patch("Quartz.CGWindowListCopyWindowInfo")
    def test_get_window_bounds_fallback_largest_area(self, mock_cg):
        """
        驗證當視窗名稱皆為空時，依然依面積最大者優先選擇主視窗
        """
        mock_cg.return_value = [
            # 較小視窗 (Layer: 0, 320x320)
            {
                "kCGWindowOwnerName": "LINE",
                "kCGWindowName": "",
                "kCGWindowLayer": 0,
                "kCGWindowBounds": {"X": 100, "Y": 100, "Width": 320, "Height": 320}
            },
            # 較大視窗 (Layer: 0, 800x600)
            {
                "kCGWindowOwnerName": "LINE",
                "kCGWindowName": "",
                "kCGWindowLayer": 0,
                "kCGWindowBounds": {"X": 200, "Y": 150, "Width": 800, "Height": 600}
            }
        ]

        bounds = macos_ui_adapter.get_window_bounds("LINE")
        self.assertEqual(bounds, (200, 150, 800, 600))

if __name__ == "__main__":
    unittest.main()
