"""
스캔 로직 모듈
- 각 스캔 함수를 개별적으로 관리
- 새로운 스캔 항목 추가/제거 용이
"""

import re
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from .config import DEFAULT_HEADERS, SITE_SESSIONS, REQUEST_CONFIG
from .run_list import dedupe_scan_result_rows
from .scan_io import save_results_to_file, save_to_history


# ========================================
# 헤더 설정 함수
# ========================================

def get_headers_for_url(url):
    """URL에 맞는 헤더 반환 (사이트별 세션 적용)"""
    headers = DEFAULT_HEADERS.copy()

    # 도메인 추출
    domain = urlparse(url).netloc

    # 사이트별 세션 적용
    if domain in SITE_SESSIONS:
        headers.update(SITE_SESSIONS[domain])

    return headers


# ========================================
# 개별 스캔 함수
# ========================================

# Form 스캔 함수
def scan_forms(soup, url, site_id, status_code):
    """Form 태그 스캔"""
    results = []
    forms = soup.find_all('form')

    for form in forms:
        method = form.get('method', 'GET').upper()
        action = form.get('action', '')
        full_action = urljoin(url, action) if action else url

        # Form 내 input 수집
        inputs = []
        for inp in form.find_all(['input', 'textarea', 'select']):
            inputs.append(f"<{inp.name} name=\"{inp.get('name', '')}\" type=\"{inp.get('type', '')}\">")

        results.append({
            "siteId": site_id,
            "type": "form",
            "method": method,
            "url": full_action,
            "status": status_code,
            "details": inputs  # 모든 input 태그 포함 (개수 제한 없음 26-01-31)
        })

    return results, len(forms)

# Input 스캔 함수
def scan_inputs(soup, url, site_id, status_code):
    """Form 외부 Input 태그 스캔"""
    results = []

    standalone_inputs = soup.find_all('input')
    form_inputs = set()
    for form in soup.find_all('form'):
        for inp in form.find_all('input'):
            form_inputs.add(id(inp))

    outside_inputs = [inp for inp in standalone_inputs if id(inp) not in form_inputs]

    for inp in outside_inputs:  # 모든 input 태그 포함 (개수 제한 없음 26-01-31)
        results.append({
            "siteId": site_id,
            "type": "input",
            "method": "GET",
            "url": url,
            "status": status_code,
            "details": [f"name=\"{inp.get('name', '')}\" type=\"{inp.get('type', '')}\""]
        })

    return results, len(outside_inputs)

# Script 스캔 함수
def scan_scripts(soup, url, site_id, status_code):
    """Script 태그 스캔 (외부 스크립트 + 인라인 AJAX URL 추출)"""
    results = []
    script_count = 0

    for script in soup.find_all('script'):
        src = script.get('src', '')

        if src:
            # 외부 스크립트 (google 관련 제외), 제외할 항목 있으면 여기에 추가
            if 'google' not in src.lower():
                full_src = urljoin(url, src)
                results.append({
                    "siteId": site_id,
                    "type": "script",
                    "method": "-",
                    "url": full_src,
                    "status": status_code,
                    "details": None
                })
                script_count += 1
        else:
            # 인라인 스크립트에서 AJAX URL 추출
            content = script.get_text(strip=True)
            if content:
                ajax_urls = get_ajax_urls(content)

                for ajax in ajax_urls:
                    full_ajax_url = urljoin(url, ajax["url"])
                    results.append({
                        "siteId": site_id,
                        "type": "script",
                        "method": ajax["method"],
                        "url": full_ajax_url,
                        "status": status_code,
                        "details": ["ajax", f"inline"]
                    })
                    script_count += 1

    return results, script_count

# 부모 함수 : 스크립트 태그 내에서 AJAX URL 및 메서드 추출
def get_ajax_urls(script_content):
    """Script 태그 내에서 AJAX URL 및 메서드 추출"""
    ajax_list = []

    # URL 추출 패턴 (추가할 패턴이 있다면 여기에 작성 26-01-31)
    url_patterns = [
        r'url\s*:\s*["\']([^"\']+)["\']',           # url: "/api/data"
        r'\$\.ajax\s*\(\s*["\']([^"\']+)["\']',       # $.ajax("/api/data")
        r'\$\.get\s*\(\s*["\']([^"\']+)["\']',        # $.get("/api/data")
        r'\$\.post\s*\(\s*["\']([^"\']+)["\']',       # $.post("/api/data")
        r'fetch\s*\(\s*["\']([^"\']+)["\']',        # fetch("/api/data")
        r'XMLHttpRequest.*?open\s*\([^,]+,\s*["\']([^"\']+)["\']',  # xhr.open("GET", "/api")
    ]

    # 메서드 추출 패턴
    method_patterns = [
        r'type\s*:\s*["\']([^"\']+)["\']',          # type: "POST"
        r'method\s*:\s*["\']([^"\']+)["\']',        # method: "POST"
    ]

    # URL 추출
    urls_found = []
    for pattern in url_patterns:
        matches = re.findall(pattern, script_content, re.IGNORECASE | re.DOTALL)
        urls_found.extend(matches)

    # 메서드 추출
    methods_found = []
    for pattern in method_patterns:
        matches = re.findall(pattern, script_content, re.IGNORECASE)
        methods_found.extend([m.upper() for m in matches])

    # 기본 메서드는 GET
    default_method = methods_found[0] if methods_found else "GET"

    # URL과 메서드 조합
    for ajax_url in urls_found:
        # 빈 URL, javascript:, # 등 제외
        if ajax_url and not ajax_url.startswith(('javascript:', '#', 'data:')):
            ajax_list.append({
                "url": ajax_url,
                "method": default_method
            })

    return ajax_list

# Information 스캔 함수
def scan_info(html_content, site_id):
    """Information 패턴 스캔 (민감 정보 탐지)"""
    results = []

    # 추출할 패턴을 변경하거나 추가할 때 아래에 작성
    patterns = {
        'API_KEY': r'(?i)(api[_-]?key|apikey)\s*[=:]\s*["\']?[\w-]{20,}',
        'PASSWORD': r'(?i)(password|passwd|pwd)\s*[=:]\s*["\'][^"\']+["\']',
        'TOKEN': r'(?i)(token|secret|auth)\s*[=:]\s*["\']?[\w-]{20,}',
        'EMAIL': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        'IP_ADDRESS': r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
        'AWS_KEY': r'AKIA[0-9A-Z]{16}',
        'JWT_TOKEN': r'ey[a-zA-Z0-9_-]{24,}'
    }

    lines = html_content.split('\n')
    info_count = 0

    for line_num, line in enumerate(lines, 1):
        for pattern_name, pattern in patterns.items():
            if re.search(pattern, line):
                info_count += 1
                masked_line = line.strip()[:100] + ('...' if len(line) > 100 else '')

                results.append({
                    "siteId": site_id,
                    "type": "info",
                    "method": "-",
                    "url": "",
                    "content": masked_line,
                    "status": 200,
                    "details": [f"Type: {pattern_name}", f"Line: {line_num}"]
                })

    return results, info_count

#a href 스캔 함수
def scan_links(soup, url, site_id, status_code):
    """A href 태그 스캔 (제외 패턴이 URL에 포함되면 결과에서 제외)"""
    results = []
    links = soup.find_all('a', href=True)
    # full_url(절대 URL)에 아래 문자열 중 하나라도 포함되면 제외 (대소문자 무시)
    exclude_url_substrings = [
        "google",
        "mircorsoft",
        "javascript:;",
    ]

    for link in links:
        href = link.get('href', '')
        full_url = urljoin(url, href) if href else url
        url_lower = full_url.lower()
        if any(sub in url_lower for sub in exclude_url_substrings):
            continue

        link_text = link.get_text(strip=True)

        results.append({
            "siteId": site_id,
            "type": "link",
            "method": "GET",
            "url": full_url,
            "status": status_code,
            "details": {
                "text": link_text,
                "target": link.get('target', ''),
                "rel": link.get('rel', []),
                "original_href": href
            }
        })
    return results, len(results)


# ========================================
# 메인 스캔 함수
# ========================================

def run_scan(urls, options, scan_status, scan_lock, add_log):
    """
    백그라운드 스캔 실행. 완료 시 scan_results.json·히스토리 JSON은 scan_io로 자동 저장한다.
    """

    with scan_lock:
        scan_status["is_running"] = True
        scan_status["progress"] = 0
        scan_status["results"] = {"sites": [], "results": []}
        scan_status["logs"] = []

    add_log(f"스캔 시작: {len(urls)}개 URL")

    # 옵션 파싱(추가할 옵션이 있으면 추가하고, True/False 값으로 처리)
    opt_forms = options.get('forms', True)
    opt_inputs = options.get('inputs', True)
    opt_scripts = options.get('scripts', True)
    opt_info = options.get('info', True)
    opt_links = options.get('links', True)
    total_urls = len(urls)
    denom = total_urls if total_urls else 1
    # 동일 스킴+호스트 URL을 한 사이트로 묶음(입력 순서 유지)
    order: list[str] = []
    groups: dict[str, list[str]] = {}
    for u in urls:
        p = urlparse(u.strip())
        key = (u.strip() or "unknown") if not p.netloc else f"{(p.scheme or 'http').lower()}://{p.netloc.lower()}"
        if key not in groups:
            order.append(key)
            groups[key] = []
        groups[key].append(u)
    grouped = [(k, groups[k]) for k in order]
    stopped = False
    processed = 0

    for site_id, (_origin, url_list) in enumerate(grouped, 1):
        if stopped:
            break

        first_url = url_list[0]
        netloc = urlparse(first_url).netloc or first_url
        site_data = {
            "id": site_id,
            "url": netloc,
            "lastScan": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "scanned_urls": list(url_list),
        }
        with scan_lock:
            scan_status["results"]["sites"].append(site_data)

        for url in url_list:
            with scan_lock:
                if not scan_status["is_running"]:
                    add_log("스캔이 사용자에 의해 중지됨")
                    stopped = True
                    break
                scan_status["current_url"] = url
                scan_status["progress"] = int((processed / denom) * 100)

            add_log(f"스캔 중: {url}")
            processed += 1

            try:
                headers = get_headers_for_url(url)
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    context = browser.new_context(extra_http_headers=headers)
                    page = context.new_page()

                    status_code = 0

                    def on_response(res):
                        nonlocal status_code
                        if res.url == url or res.url == url.rstrip('/') + '/':
                            status_code = res.status

                    page.on("response", on_response)

                    page.goto(
                        url,
                        timeout=REQUEST_CONFIG["timeout"] * 1000,
                        wait_until="networkidle"
                    )

                    html_content = page.content()
                    browser.close()

                if status_code == 0:
                    status_code = 200

                add_log(f"응답: {status_code}")

                soup = BeautifulSoup(html_content, 'html.parser')
                batch = []

                if opt_forms:
                    form_results, form_count = scan_forms(soup, url, site_id, status_code)
                    add_log(f"Form 발견: {form_count}개")
                    batch.extend(form_results)

                if opt_inputs:
                    input_results, input_count = scan_inputs(soup, url, site_id, status_code)
                    if input_count > 0:
                        add_log(f"독립 Input 발견: {input_count}개")
                    batch.extend(input_results)

                if opt_scripts:
                    script_results, script_count = scan_scripts(soup, url, site_id, status_code)
                    add_log(f"Script 발견: {script_count}개")
                    batch.extend(script_results)

                if opt_info:
                    info_results, info_count = scan_info(html_content, site_id)
                    if info_count > 0:
                        add_log(f"Information 발견: {info_count}개")
                    batch.extend(info_results)

                if opt_links:
                    link_results, link_count = scan_links(soup, url, site_id, status_code)
                    if link_count > 0:
                        add_log(f"a href 발견: {link_count}개")
                    batch.extend(link_results)

                if batch:
                    with scan_lock:
                        scan_status["results"]["results"].extend(batch)
                        scan_status["results"]["results"] = dedupe_scan_result_rows(
                            scan_status["results"]["results"]
                        )

                with scan_lock:
                    scan_status["progress"] = int((processed / denom) * 100)

            except PlaywrightTimeout:
                add_log(f"타임아웃: {url}")
            except Exception as e:
                add_log(f"오류: {str(e)[:50]}")

            time.sleep(REQUEST_CONFIG["delay"])

        site_data["lastScan"] = datetime.now().strftime("%Y-%m-%d %H:%M")

        with scan_lock:
            site_results = dedupe_scan_result_rows(
                [r for r in scan_status["results"]["results"] if r.get("siteId") == site_id]
            )
        url_result = {"sites": [site_data], "results": site_results}
        save_to_history(url_result)
        add_log(f"히스토리 저장(호스트 통합): {site_data['url']} ({len(url_list)}개 URL)")

        if stopped:
            break

    with scan_lock:
        scan_status["is_running"] = False
        scan_status["current_url"] = ""
        scan_status["progress"] = 100

        if scan_status["results"]["sites"]:
            scan_status["results"]["results"] = dedupe_scan_result_rows(
                scan_status["results"]["results"]
            )
            save_results_to_file(scan_status["results"])

    add_log("스캔 완료! (호스트별 히스토리 저장됨)")