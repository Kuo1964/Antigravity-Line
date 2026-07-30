import pytest
from unittest.mock import patch, MagicMock
from app.services.scheduler_service import run_good_morning_workflow

def test_run_good_morning_workflow_success():
    with patch("app.services.scheduler_service.unlock_mac") as mock_unlock, \
         patch("app.services.scheduler_service.fetch_latest_good_morning_image") as mock_fetch, \
         patch("app.services.scheduler_service.copy_image_to_clipboard") as mock_copy, \
         patch("app.services.scheduler_service.search_and_send_image") as mock_send:
        
        mock_fetch.return_value = "/tmp/test_good_morning.jpg"
        mock_copy.return_value = True
        mock_send.return_value = True

        result = run_good_morning_workflow(target_name="Private", mac_password="dummy_password")

        assert result["success"] is True
        assert result["target"] == "Private"
        assert result["image_path"] == "/tmp/test_good_morning.jpg"
        mock_unlock.assert_called_once_with("dummy_password")
        mock_fetch.assert_called_once()
        mock_copy.assert_called_once_with("/tmp/test_good_morning.jpg")
        mock_send.assert_called_once_with("Private", "/tmp/test_good_morning.jpg")

def test_run_good_morning_workflow_copy_failure():
    with patch("app.services.scheduler_service.unlock_mac"), \
         patch("app.services.scheduler_service.fetch_latest_good_morning_image") as mock_fetch, \
         patch("app.services.scheduler_service.copy_image_to_clipboard") as mock_copy, \
         patch("app.services.scheduler_service.search_and_send_image"):
        
        mock_fetch.return_value = "/tmp/test_good_morning.jpg"
        mock_copy.return_value = False

        result = run_good_morning_workflow(target_name="Private")

        assert result["success"] is False
        assert "剪貼簿失敗" in result["message"]
