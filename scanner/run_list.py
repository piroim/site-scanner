"""
스캔 결과에서 엔드포인트·구역별 URL 목록을 만든다 (List 화면과 동기).

- EndPoint 표기: url/path?parameter (GET/POST)
- GET·POST는 form/input만 처리, LINK·JS(script)는 type별 URL 목록.

List 페이지는 저장된 히스토리(`scan_data/history/scan_*.json` 전부 병합)를 기준으로 자동 동기화할 때
`list_vuln_sections_for_site` 등을 사용해 `scan_data/access_list/` JSON을 갱신한다(별도 클릭 없이).
"""

import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

# 프로젝트 기본 스캔 결과·히스토리 경로
DEFAULT_SCAN_RESULTS = Path(__file__).resolve().parent.parent / "scan_data" / "scan_results.json"
DEFAULT_HISTORY_DIR = Path(__file__).resolve().parent.parent / "scan_data" / "history"


def _details_fingerprint(details: Any) -> str:
    """details(리스트·중첩 구조 포함)를 set 키로 쓸 수 있는 문자열로 정규화."""
    if details is None:
        return ""
    try:
        return json.dumps(details, sort_keys=True, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        return repr(details)


def history_scan_json_paths(history_dir: Path | str | None = None) -> list[Path]:
    """scan_*.json 전부를 수정 시각 오름차순으로 반환한다."""
    d = Path(history_dir) if history_dir is not None else DEFAULT_HISTORY_DIR
    if not d.is_dir():
        return []
    files = [p for p in d.glob("scan_*.json") if p.is_file()]
    return sorted(files, key=lambda p: p.stat().st_mtime)


def merge_history_scan_payloads(payloads: list[dict[str, Any]]) -> dict[str, Any] | None:
    """
    여러 히스토리 JSON을 하나의 스캔 결과 형식으로 병합한다.
    동일 사이트 URL은 하나의 site id로 묶고, results 행은 siteId만 재매핑해 합친다(동일 행은 중복 제거).
    """
    if not payloads:
        return None
    merged_sites: list[dict[str, Any]] = []
    url_to_id: dict[str, int] = {}
    merged_results: list[dict[str, Any]] = []
    seen_row: set[tuple[Any, str, str, str, str]] = set()

    for payload in payloads:
        block = payload.get("results") or {}
        sites = block.get("sites") or []
        old_to_global: dict[Any, int] = {}

        for s in sites:
            if not isinstance(s, dict):
                continue
            oid = s.get("id")
            url = (s.get("url") or "").strip()
            if not url or oid is None:
                continue
            if url not in url_to_id:
                gid = len(merged_sites)
                url_to_id[url] = gid
                ns = dict(s)
                ns["id"] = gid
                merged_sites.append(ns)
            else:
                gid = url_to_id[url]
                merged_sites[gid].update({k: v for k, v in s.items() if k != "id"})
                merged_sites[gid]["id"] = gid
            old_to_global[oid] = url_to_id[url]

        for entry in block.get("results") or []:
            if not isinstance(entry, dict):
                continue
            oid = entry.get("siteId")
            if oid not in old_to_global:
                continue
            ne = dict(entry)
            ne["siteId"] = old_to_global[oid]
            t = (ne.get("type") or "").lower()
            u = (ne.get("url") or "").strip()
            m = (ne.get("method") or "").upper()
            fp = (ne["siteId"], t, u, m, _details_fingerprint(ne.get("details")))
            if fp in seen_row:
                continue
            seen_row.add(fp)
            merged_results.append(ne)

    if not merged_sites:
        return None
    saved_ats = [str(p.get("saved_at") or "") for p in payloads]
    saved_at = max(saved_ats) if saved_ats else ""
    return {
        "saved_at": saved_at,
        "results": {"sites": merged_sites, "results": merged_results},
    }


def extract_param_names_from_details(details: Any) -> list[str]:
    """form/input의 details 문자열 목록에서 name 속성만 순서 유지·중복 제거로 추출."""
    if not details or isinstance(details, dict):
        return []
    names: list[str] = []
    for line in details:
        if not isinstance(line, str):
            continue
        for m in re.finditer(r'name\s*=\s*["\']([^"\']*)["\']', line):
            n = m.group(1).strip()
            if n:
                names.append(n)
    seen: set[str] = set()
    out: list[str] = []
    for n in names:
        if n not in seen:
            seen.add(n)
            out.append(n)
    return out


def _merge_url_with_param_names(url: str, param_names: list[str]) -> str:
    """기존 쿼리스트링과 details에서 나온 파라미터 이름을 합쳐 url/path?a=&b= 형태로 만든다."""
    p = urlparse(url)
    pairs = list(parse_qsl(p.query, keep_blank_values=True))
    existing_keys = {k for k, _ in pairs}
    for name in param_names:
        if name not in existing_keys:
            pairs.append((name, ""))
            existing_keys.add(name)
    query = urlencode(pairs, doseq=True)
    path = p.path if p.path else "/"
    return urlunparse((p.scheme, p.netloc, path, "", query, ""))


def format_get_endpoint(url: str, param_names: list[str]) -> str:
    """GET: 쿼리 파라미터로 전송되는 경우의 url/path?parameter 표기."""
    return _merge_url_with_param_names(url, param_names)


def format_post_endpoint(url: str, param_names: list[str]) -> str:
    """POST: 본문 필드명을 같은 표기 규칙으로 나열(경로·이름 정리용). 값은 비움."""
    return _merge_url_with_param_names(url, param_names)


def endpoint_from_result_entry(entry: dict[str, Any]) -> str | None:
    """
    스캔 결과 한 건을 GET/POST 전용 포맷으로 변환.
    method가 GET·POST가 아니거나 url이 비어 있으면 None.
    """
    method = (entry.get("method") or "").upper()
    url = (entry.get("url") or "").strip()
    if not url or method not in ("GET", "POST"):
        return None
    names = extract_param_names_from_details(entry.get("details"))
    if method == "GET":
        return format_get_endpoint(url, names)
    return format_post_endpoint(url, names)


def load_scan_results(path: Path | str | None = None) -> dict[str, Any]:
    """scan_results.json 등 스캔 결과 JSON을 로드한다."""
    p = Path(path) if path else DEFAULT_SCAN_RESULTS
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def list_endpoints_from_scan_payload(payload: dict[str, Any]) -> list[tuple[str, str]]:
    """
    results.results 배열을 순회해 (method, url/path?parameter) 목록을 만든다.
    GET·POST만 포함.
    """
    out: list[tuple[str, str]] = []
    block = payload.get("results") or {}
    rows = block.get("results") or []
    for entry in rows:
        if not isinstance(entry, dict):
            continue
        method = (entry.get("method") or "").upper()
        line = endpoint_from_result_entry(entry)
        if line is None:
            continue
        out.append((method, line))
    return out


def list_vuln_sections(payload: dict[str, Any]) -> dict[str, list[str]]:
    """
    Vuln 화면용: GET/POST는 form·input만, LINK·JS(script)는 type별 URL 목록.
    링크/스크립트는 URL 기준 중복 제거(순서 유지).
    """
    block = payload.get("results") or {}
    rows = block.get("results") or []
    get_lines: list[str] = []
    post_lines: list[str] = []
    link_lines: list[str] = []
    script_lines: list[str] = []
    seen_link: set[str] = set()
    seen_script: set[str] = set()

    for entry in rows:
        if not isinstance(entry, dict):
            continue
        t = (entry.get("type") or "").lower()
        url = (entry.get("url") or "").strip()
        method = (entry.get("method") or "").upper()

        if t == "link" and url:
            if url not in seen_link:
                seen_link.add(url)
                link_lines.append(url)
            continue
        if t == "script" and url:
            if url not in seen_script:
                seen_script.add(url)
                script_lines.append(url)
            continue
        if t not in ("form", "input"):
            continue
        line = endpoint_from_result_entry(entry)
        if line is None:
            continue
        if method == "GET":
            get_lines.append(line)
        elif method == "POST":
            post_lines.append(line)

    return {
        "get": get_lines,
        "post": post_lines,
        "link": link_lines,
        "script": script_lines,
    }


def list_vuln_sections_for_site(payload: dict[str, Any], site_id: int) -> dict[str, list[str]]:
    """특정 siteId에 대해서만 list_vuln_sections와 동일한 구조로 수집."""
    block = payload.get("results") or {}
    rows = block.get("results") or []
    get_lines: list[str] = []
    post_lines: list[str] = []
    link_lines: list[str] = []
    script_lines: list[str] = []
    seen_link: set[str] = set()
    seen_script: set[str] = set()

    for entry in rows:
        if not isinstance(entry, dict):
            continue
        if entry.get("siteId") != site_id:
            continue
        t = (entry.get("type") or "").lower()
        url = (entry.get("url") or "").strip()
        method = (entry.get("method") or "").upper()

        if t == "link" and url:
            if url not in seen_link:
                seen_link.add(url)
                link_lines.append(url)
            continue
        if t == "script" and url:
            if url not in seen_script:
                seen_script.add(url)
                script_lines.append(url)
            continue
        if t not in ("form", "input"):
            continue
        line = endpoint_from_result_entry(entry)
        if line is None:
            continue
        if method == "GET":
            get_lines.append(line)
        elif method == "POST":
            post_lines.append(line)

    return {
        "get": get_lines,
        "post": post_lines,
        "link": link_lines,
        "script": script_lines,
    }