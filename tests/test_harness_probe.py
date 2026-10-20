"""針對 Harness² .agents 配置與探針腳本 (verify_harness_probe.py) 之單元測試。"""

from __future__ import annotations

import json
from pathlib import Path

from scripts.verify_harness_probe import (
    COMPONENT_FILES,
    build_default_component_contents,
    initialize_agents_directory,
    probe_components,
    probe_macos_frameworks,
    run_probe_report,
)


def test_build_default_component_contents_covers_all_eight() -> None:
    """驗證預設生成的配置內容完整涵蓋 Harness² 的 8 大外圍元件。"""
    contents = build_default_component_contents()
    assert set(contents.keys()) == set(COMPONENT_FILES.keys())
    assert len(contents) == 8
    for key, text in contents.items():
        assert isinstance(text, str) and len(text.strip()) > 20, f"元件 {key} 內容過短或為空"


def test_initialize_and_probe_components_in_temp_dir(tmp_path: Path) -> None:
    """驗證在獨立目錄中初始化 .agents 8 大元件後，探針檢測 8/8 全數通過且 manifest 正確生成。"""
    agents_dir = tmp_path / ".agents"
    created = initialize_agents_directory(agents_dir)
    assert len(created) == 8

    manifest_file = agents_dir / "harness_manifest.json"
    assert manifest_file.is_file()
    manifest_data = json.loads(manifest_file.read_text(encoding="utf-8"))
    assert manifest_data["recursion_mode"] == "Propose-Probe-Compose"

    status = probe_components(agents_dir)
    assert all(status.values()) is True
    assert len(status) == 8


def test_probe_detects_missing_component(tmp_path: Path) -> None:
    """驗證當缺少任一元件（如 guardrails）時，探針能精準識別為 False（Red-capable）。"""
    agents_dir = tmp_path / ".agents"
    initialize_agents_directory(agents_dir)

    # 故意刪除 guardrails 元件檔案以模擬配置缺失
    guardrail_path = agents_dir / COMPONENT_FILES["guardrails"]
    guardrail_path.unlink()

    report = run_probe_report(agents_dir)
    assert report["all_components_ready"] is False
    assert report["components"]["guardrails"] is False
    assert report["component_count"] == "7/8"


def test_probe_macos_frameworks_available() -> None:
    """驗證專案執行環境具備 Quartz、AppKit 與 Vision 框架。"""
    fw_status = probe_macos_frameworks()
    assert fw_status["Quartz"] is True
    assert fw_status["AppKit"] is True
    assert fw_status["Vision"] is True
