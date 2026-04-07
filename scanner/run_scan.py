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
    """A href 태그 스캔"""
    results = []
    links = soup.find_all('a', href=True)

    for link in links:
        href = link.get('href', '')
        full_url = urljoin(url, href) if href else url
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
    return results, len(links)

# ========================================
# 메인 스캔 함수
# ========================================

def run_scan(urls, options, scan_status, scan_lock, add_log, save_callbacks=None):
    """
    백그라운드 스캔 실행

    Args:
        urls: 스캔할 URL 리스트
        options: 스캔 옵션 (forms, inputs, scripts, info)
        scan_status: 공유 상태 딕셔너리
        scan_lock: 스레드 락
        add_log: 로그 추가 함수
        save_callbacks: 저장 콜백 함수들 (save_results_to_file, save_to_history)
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

    for idx, url in enumerate(urls, 1):
        with scan_lock:
            if not scan_status["is_running"]:
                add_log("스캔이 사용자에 의해 중지됨")
                break

            scan_status["current_url"] = url
            scan_status["progress"] = int((idx - 1) / total_urls * 100)

        add_log(f"스캔 중: {url}")

        # 사이트 추가
        site_id = idx
        with scan_lock:
            scan_status["results"]["sites"].append({
                "id": site_id,
                "url": urlparse(url).netloc or url,
                "lastScan": datetime.now().strftime("%Y-%m-%d %H:%M")
            })

        try:
            # Playwright로 렌더링 후 DOM 수집
            headers = get_headers_for_url(url)
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(extra_http_headers=headers)
                page = context.new_page()

                # 네트워크 응답에서 status_code 캡처
                status_code = 0
                def on_response(res):
                    nonlocal status_code
                    if res.url == url or res.url == url.rstrip('/') + '/':
                        status_code = res.status

                page.on("response", on_response)

                page.goto(
                    url,
                    timeout=REQUEST_CONFIG["timeout"] * 1000,  # ms 단위
                    wait_until="networkidle"
                )

                html_content = page.content()
                browser.close()

            if status_code == 0:
                status_code = 200  # goto 성공 시 기본값

            add_log(f"응답: {status_code}")

            soup = BeautifulSoup(html_content, 'html.parser')
            
            # ================================================
            # 여기부터가 각 태그별로 스캔하는 로직
            # 태그를 추가할 때, 아래에 코드 작성
            # ================================================

            # Form 스캔
            if opt_forms:
                form_results, form_count = scan_forms(soup, url, site_id, status_code)
                add_log(f"Form 발견: {form_count}개")
                with scan_lock:
                    scan_status["results"]["results"].extend(form_results)

            # Input 스캔
            if opt_inputs:
                input_results, input_count = scan_inputs(soup, url, site_id, status_code)
                if input_count > 0:
                    add_log(f"독립 Input 발견: {input_count}개")
                with scan_lock:
                    scan_status["results"]["results"].extend(input_results)

            # Script 스캔
            if opt_scripts:
                script_results, script_count = scan_scripts(soup, url, site_id, status_code)
                add_log(f"Script 발견: {script_count}개")
                with scan_lock:
                    scan_status["results"]["results"].extend(script_results)

            # Information 스캔
            if opt_info:
                info_results, info_count = scan_info(html_content, site_id)
                if info_count > 0:
                    add_log(f"Information 발견: {info_count}개")
                with scan_lock:
                    scan_status["results"]["results"].extend(info_results)

            # a href 스캔
            if opt_links:
                link_results, link_count = scan_links(soup, url, site_id, status_code)
                if link_count > 0:
                    add_log(f"a href 발견: {link_count}개")
                with scan_lock:
                    scan_status["results"]["results"].extend(link_results)
                    
            # URL별 히스토리 저장
            if save_callbacks:
                save_results_to_file, save_to_history = save_callbacks
                # 현재 URL의 결과만 추출하여 저장
                site_data = scan_status["results"]["sites"][-1]  # 현재 사이트
                site_results = [r for r in scan_status["results"]["results"] if r["siteId"] == site_id]
                url_result = {
                    "sites": [site_data],
                    "results": site_results
                }
                save_to_history(url_result)
                add_log(f"히스토리 저장: {site_data['url']}")

        except PlaywrightTimeout:
            add_log(f"타임아웃: {url}")
        except Exception as e:
            add_log(f"오류: {str(e)[:50]}")

        # 진행률 업데이트
        with scan_lock:
            scan_status["progress"] = int(idx / total_urls * 100)

        # 요청 간 딜레이 (서버 부하 방지)
        time.sleep(REQUEST_CONFIG["delay"])

    with scan_lock:
        scan_status["is_running"] = False
        scan_status["current_url"] = ""
        scan_status["progress"] = 100

        # 전체 결과 저장 (scan_results.json)
        if scan_status["results"]["sites"] and save_callbacks:
            save_results_to_file, save_to_history = save_callbacks
            save_results_to_file(scan_status["results"])

    add_log("스캔 완료! (URL별 히스토리 저장됨)")