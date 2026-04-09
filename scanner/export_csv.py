"""
access_list 디렉터리의 사이트별 JSON을 읽어 CSV/ZIP로 내보낸다.

출력 경로는 app에서 지정한다(기본: 프로젝트 루트의 csv_data/).
다운로드 응답 후 해당 파일은 app에서 삭제한다.

컬럼: idx, site_label, sections, url, temp
- sections: get | post | link | script | info
- temp: 예약(현재 "-")
"""

from __future__ import annotations

import csv
import io
import zipfile
from pathlib import Path
from typing import Any, Iterator

from scanner.access_list import load_access_record

CSV_FIELDNAMES = ["idx", "site_label", "sections", "url", "temp"]

# access_list sections 키 순서(병합 CSV·단일 파일 공통)
ACCESS_LIST_SECTION_ORDER = ("get", "post", "link", "script", "info")


def iter_rows_for_single_json(json_path: Path) -> Iterator[dict[str, Any]]:
    """한 access_list JSON 파일에 대한 행(idx는 해당 파일 내 1부터)."""
    rec = load_access_record(json_path)
    if not rec:
        return
    idx = 0
    site_label = (rec.get("site_label") or json_path.stem or "").strip() or "-"
    secs = rec.get("sections") or {}
    for sec in ACCESS_LIST_SECTION_ORDER:
        for line in secs.get(sec) or []:
            idx += 1
            url = line.strip() if isinstance(line, str) else str(line)
            yield {
                "idx": idx,
                "site_label": site_label,
                "sections": sec,
                "url": url,
                "temp": "-",
            }


def iter_access_list_csv_rows(access_list_dir: Path) -> Iterator[dict[str, Any]]:
    """access_list/*.json 전부를 병합할 때 전역 idx(1부터)."""
    global_idx = 0
    for path in sorted(access_list_dir.glob("*.json")):
        for row in iter_rows_for_single_json(path):
            global_idx += 1
            merged = dict(row)
            merged["idx"] = global_idx
            yield merged


def write_access_list_csv(output_path: Path, access_list_dir: Path) -> Path:
    """
    access_list_dir의 모든 JSON을 병합한 CSV를 output_path에 쓴다.
    데이터가 없어도 헤더 행은 기록한다. UTF-8 BOM(Excel 호환).
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES, extrasaction="ignore")
        w.writeheader()
        for row in iter_access_list_csv_rows(access_list_dir):
            w.writerow(row)
    return output_path


def write_access_list_csv_for_file(output_path: Path, json_path: Path) -> Path:
    """단일 access_list JSON 파일만 CSV로 저장한다."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES, extrasaction="ignore")
        w.writeheader()
        for row in iter_rows_for_single_json(json_path):
            w.writerow(row)
    return output_path


def write_access_list_csv_zip_per_site(output_zip: Path, access_list_dir: Path) -> Path:
    """
    사이트(JSON)마다 별도 CSV를 만들어 하나의 ZIP에 넣는다.
    ZIP 내 파일명: `<json stem>.csv` (예: www.example.com.csv)
    """
    output_zip.parent.mkdir(parents=True, exist_ok=True)
    paths = sorted(access_list_dir.glob("*.json"))
    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in paths:
            if load_access_record(path) is None:
                continue
            buf = io.StringIO()
            w = csv.DictWriter(buf, fieldnames=CSV_FIELDNAMES, extrasaction="ignore")
            w.writeheader()
            for row in iter_rows_for_single_json(path):
                w.writerow(row)
            payload = "\ufeff".encode("utf-8") + buf.getvalue().encode("utf-8")
            zf.writestr(f"{path.stem}.csv", payload)
    return output_zip
