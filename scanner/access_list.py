"""
스캔 결과 페이로드(히스토리 JSON과 동일 형식)를 사이트(URL)별로 나누어 List 화면용 구역(get/post/link/script) JSON으로 저장한다.
동기화 시 app은 scan_data/history의 scan_*.json 전부를 병합한 페이로드를 넘긴다. run_scan에서 이미 DOM·경로를 식별하므로 여기서는 HTTP 재요청을 하지 않는다.
저장 디렉터리: scan_data/access_list/
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from scanner.run_list import (
    history_scan_json_paths,
    list_vuln_sections_for_site,
    merge_history_scan_payloads,
)


def site_label_to_filename(site_label: str) -> str:
    """파일명으로 쓸 수 있게 정규화 (확장자 .json)."""
    s = site_label.strip() or "site"
    for a, b in [(":", "-"), ("/", "-"), ("\\", "-")]:
        s = s.replace(a, b)
    for c in '<>:"|?*':
        s = s.replace(c, "-")
    s = re.sub(r"[\s]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-") or "site"
    return f"{s}.json"


def export_access_list_from_scan(
    payload: dict[str, Any],
    output_dir: Path,
) -> list[dict[str, Any]]:
    """
    results.sites 기준으로 사이트마다 list_vuln_sections_for_site 결과를 JSON으로 저장.
    반환: 각 사이트 요약(filename, site_label, site_id, updated_at, counts).

    sites가 비어 있거나 유효한 site가 없으면 파일을 만들지 않고 빈 리스트를 반환한다(오류 아님).
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    block = payload.get("results") or {}
    sites = block.get("sites") or []
    summaries: list[dict[str, Any]] = []
    now = datetime.now().isoformat()

    for site in sites:
        sid = site.get("id")
        label = (site.get("url") or "").strip() or f"site-{sid}"
        if sid is None:
            continue
        sections = list_vuln_sections_for_site(payload, sid)
        fn = site_label_to_filename(label)
        path = output_dir / fn
        record = {
            "site_id": sid,
            "site_label": label,
            "updated_at": now,
            "scan_saved_at": payload.get("saved_at"),
            "sections": sections,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(record, f, ensure_ascii=False, indent=2)
        summaries.append(
            {
                "filename": fn,
                "site_label": label,
                "site_id": sid,
                "updated_at": now,
                "counts": {k: len(v) for k, v in sections.items()},
            }
        )

    return summaries


def export_access_list_from_history_dir(
    history_dir: Path,
    output_dir: Path,
) -> list[dict[str, Any]]:
    """
    history_dir의 scan_*.json을 모두 읽어 병합한 뒤 access_list JSON을 생성한다.
    """
    payloads: list[dict[str, Any]] = []
    for p in history_scan_json_paths(history_dir):
        try:
            with open(p, encoding="utf-8") as f:
                payloads.append(json.load(f))
        except (OSError, json.JSONDecodeError):
            continue
    merged = merge_history_scan_payloads(payloads)
    if merged is None:
        return []
    return export_access_list_from_scan(merged, output_dir)


def delete_history_files_for_site_label(site_label: str, history_dir: Path) -> list[str]:
    """
    scan_data/history의 scan_*.json 중, results.sites에 해당 사이트 url이 포함된 파일을 삭제한다.
    한 파일에 여러 사이트가 있으면 파일 전체가 삭제된다(다른 사이트 스냅샷도 함께 제거).
    """
    deleted: list[str] = []
    target = (site_label or "").strip()
    if not target:
        return deleted
    history_dir = Path(history_dir)
    if not history_dir.is_dir():
        return deleted
    for fp in history_dir.glob("scan_*.json"):
        try:
            with open(fp, encoding="utf-8") as f:
                data = json.load(f)
            sites = data.get("results", {}).get("sites", [])
            urls = {s.get("url") for s in sites if isinstance(s, dict)}
            if target in urls:
                fp.unlink()
                deleted.append(fp.name)
        except (OSError, json.JSONDecodeError):
            continue
    return deleted


def load_access_record(path: Path) -> dict[str, Any] | None:
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def run_access_tests_for_payload(
    payload: dict[str, Any],
    output_dir: Path,
) -> list[dict[str, Any]]:
    return export_access_list_from_scan(payload, output_dir)
