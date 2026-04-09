"""
스캔 결과 페이로드(히스토리 JSON과 동일 형식)를 사이트(URL)별로 나누어 List 화면용 구역(get/post/link/script/info) JSON으로 저장한다.
동기화 시 app은 scan_data/history의 scan_*.json 전부를 병합한 페이로드를 넘긴다. run_scan에서 이미 DOM·경로를 식별하므로 여기서는 HTTP 재요청을 하지 않는다.
저장 디렉터리: scan_data/access_list/

동일 사이트 파일이 이미 있으면 기존 sections에 이번 스캔 결과를 이어 붙이고(순서 유지), 동일 줄(strip 기준)은 한 번만 남긴다.
파일을 삭제하거나 access_list를 비우기 전까지 누적된다.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from scanner.run_list import (
    DEFAULT_HISTORY_DIR,
    delete_all_access_list_files,
    history_scan_json_paths,
    list_vuln_sections,
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


def _merge_access_sections(
    previous: dict[str, Any] | None,
    incoming: dict[str, list[str]],
) -> dict[str, list[str]]:
    """
    get/post/link/script/info 목록을 병합한다. 이전 목록을 앞에 두고,
    이어서 새 목록에서만 strip 기준으로 아직 없던 줄을 추가한다.
    """
    keys = ("get", "post", "link", "script", "info")
    out: dict[str, list[str]] = {}
    prev = previous or {}
    for k in keys:
        old_list = prev.get(k)
        if not isinstance(old_list, list):
            old_list = []
        new_list = incoming.get(k) or []
        if not isinstance(new_list, list):
            new_list = []
        seen: set[str] = set()
        merged: list[str] = []
        for line in old_list + new_list:
            if not isinstance(line, str):
                line = str(line)
            dedup_key = line.strip()
            if not dedup_key or dedup_key in seen:
                continue
            seen.add(dedup_key)
            merged.append(line)
        out[k] = merged
    return out


def export_access_list_from_scan(
    payload: dict[str, Any],
    output_dir: Path,
) -> list[dict[str, Any]]:
    """
    results.sites 기준으로 사이트마다 list_vuln_sections(payload, site_id) 결과를 JSON으로 저장.
    같은 파일명이 이미 있으면 기존 sections와 병합·중복 제거 후 저장한다.

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
        sections_new = list_vuln_sections(payload, sid)
        fn = site_label_to_filename(label)
        path = output_dir / fn
        prior = load_access_record(path)
        if prior and isinstance(prior.get("sections"), dict):
            sections = _merge_access_sections(prior["sections"], sections_new)
        else:
            sections = sections_new
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


def delete_all_history_scan_files(history_dir: Path | str | None = None) -> list[str]:
    """
    `scan_data/history/` 등에 있는 `scan_*.json` 전부를 삭제한다.
    반환: 삭제에 성공한 파일의 basename 목록(정렬됨). 디렉터리가 없으면 빈 리스트.
    """
    d = Path(history_dir) if history_dir is not None else DEFAULT_HISTORY_DIR
    deleted: list[str] = []
    if not d.is_dir():
        return deleted
    for p in sorted(d.glob("scan_*.json")):
        if not p.is_file():
            continue
        try:
            p.unlink()
            deleted.append(p.name)
        except OSError:
            continue
    return deleted


def delete_all_access_list_and_history(
    access_list_dir: Path | str | None = None,
    history_dir: Path | str | None = None,
) -> dict[str, list[str]]:
    """
    access_list 디렉터리의 `*.json` 전부와 history 디렉터리의 `scan_*.json` 전부를 삭제한다.
    반환: `{"access_list": [...], "history": [...]}` 삭제된 파일명 목록.
    """
    return {
        "access_list": delete_all_access_list_files(access_list_dir),
        "history": delete_all_history_scan_files(history_dir),
    }


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
