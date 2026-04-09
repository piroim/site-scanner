"""
scan_results.json 및 scan_data/history/scan_{호스트}.json 자동 저장.
Flask(app)와 run_scan이 공통으로 사용한다.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from scanner.access_list import site_label_to_filename

SCAN_DATA_DIR = Path(__file__).resolve().parent.parent / "scan_data"
RESULTS_FILE = SCAN_DATA_DIR / "scan_results.json"
HISTORY_DIR = SCAN_DATA_DIR / "history"


def save_results_to_file(results, filename=None, *, include_saved_at=True):
    """스캔 결과를 JSON 파일로 저장. 히스토리 전용 파일은 include_saved_at=False 로 날짜 필드를 생략할 수 있다."""
    if filename is None:
        filename = RESULTS_FILE

    if include_saved_at:
        data = {
            "saved_at": datetime.now().isoformat(),
            "results": results,
        }
    else:
        data = {"results": results}

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return filename


def save_to_history(results):
    """
    사이트마다 scan_data/history/scan_{호스트}.json 으로 저장한다.
    파일명에 날짜·타임스탬프는 넣지 않으며, 동일 호스트는 같은 파일을 덮어쓴다.
    반환: 저장된 파일 경로(Path) 목록.
    """
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    sites = results.get("sites") or []
    rows = results.get("results") or []
    if not sites:
        raise ValueError("저장할 사이트가 없습니다")

    written: list[Path] = []
    for site in sites:
        sid = site.get("id")
        if sid is None:
            continue
        label = (site.get("url") or "unknown").strip() or "unknown"
        base = site_label_to_filename(label)
        name = f"scan_{Path(base).stem}.json"
        path = HISTORY_DIR / name
        site_results = [r for r in rows if r.get("siteId") == sid]
        payload = {"sites": [site], "results": site_results}
        save_results_to_file(payload, path, include_saved_at=False)
        written.append(path)
    if not written:
        raise ValueError("유효한 사이트가 없습니다")
    return written
