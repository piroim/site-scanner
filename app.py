"""
Site Scanner - Flask Web Server
실시간 대시보드를 위한 웹 서버

실행: python app.py
접속: http://localhost:5000
"""

from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
from datetime import datetime
from pathlib import Path
from scanner import run_scan
import threading
import json
import os
import re
import logging
from scanner.access_list import (
    delete_history_files_for_site_label,
    export_access_list_from_history_dir,
    load_access_record,
)

logging.basicConfig(
    filename='flask_debug.log', 
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'  # 한글 깨짐 방지
)

app = Flask(__name__)

# ========================================
# 저장 경로 설정
# ========================================
DATA_DIR = Path(__file__).parent / "scan_data"
DATA_DIR.mkdir(exist_ok=True)
RESULTS_FILE = DATA_DIR / "scan_results.json"
HISTORY_DIR = DATA_DIR / "history"
HISTORY_DIR.mkdir(exist_ok=True)
# scan_data/access_list (구 vuln_access 디렉터리는 최초 기동 시 이름 변경·병합)
_legacy_access_dir = DATA_DIR / "vuln_access"
ACCESS_LIST_DIR = DATA_DIR / "access_list"
if _legacy_access_dir.is_dir():
    if not ACCESS_LIST_DIR.exists():
        _legacy_access_dir.rename(ACCESS_LIST_DIR)
    else:
        ACCESS_LIST_DIR.mkdir(parents=True, exist_ok=True)
        for _p in _legacy_access_dir.glob("*.json"):
            _dest = ACCESS_LIST_DIR / _p.name
            if not _dest.exists():
                _p.rename(_dest)
        try:
            _legacy_access_dir.rmdir()
        except OSError:
            pass
else:
    ACCESS_LIST_DIR.mkdir(parents=True, exist_ok=True)
SETTINGS_FILE = DATA_DIR / "settings.json"

# 기본 설정값
DEFAULT_SETTINGS = {
    "scan_options": {
        "forms": True,
        "inputs": True,
        "scripts": True,
        "info": True,
        "links": True
    },
    "display_options": {
        "dark_mode": True
    }
}

# ========================================
# 스캔 상태 관리
# ========================================
scan_status = {
    "is_running": False,
    "progress": 0,
    "current_url": "",
    "results": {
        "sites": [],
        "results": []
    },
    "logs": []
}

scan_lock = threading.Lock()


# ========================================
# 파일 저장/로드 함수
# ========================================

def save_results_to_file(results, filename=None):
    """스캔 결과를 JSON 파일로 저장"""
    if filename is None:
        filename = RESULTS_FILE
    
    data = {
        "saved_at": datetime.now().isoformat(),
        "results": results
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return filename


def load_results_from_file(filename=None):
    """JSON 파일에서 스캔 결과 로드"""
    if filename is None:
        filename = RESULTS_FILE
    
    if not os.path.exists(filename):
        return None
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"파일 로드 오류: {e}")
        return None


def has_history_scan_files():
    """히스토리 JSON이 하나라도 있으면 True (List UI 활성화용)."""
    if not HISTORY_DIR.is_dir():
        return False
    return any(HISTORY_DIR.glob("scan_*.json"))


def save_to_history(results):
    """스캔 결과를 히스토리에 저장 (타임스탬프 포함, 동일 사이트 이전 히스토리 삭제)"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 사이트 이름으로 파일명 생성 (파일명에 사용 불가능한 문자 제거: : / \ * ? " < > |)
    site_names = "_".join([
        s['url'].replace('.', '-').replace(':', '-').replace('/', '-')[:20]
        for s in results.get('sites', [])[:3]
    ])
    if not site_names:
        site_names = "unknown"

    # 동일 사이트의 이전 히스토리 파일 삭제
    current_sites = set(s['url'] for s in results.get('sites', []))
    for old_file in HISTORY_DIR.glob("scan_*.json"):
        try:
            with open(old_file, 'r', encoding='utf-8') as f:
                old_data = json.load(f)
            old_sites = set(s['url'] for s in old_data.get('results', {}).get('sites', []))
            # 동일한 사이트 구성이면 삭제
            if old_sites == current_sites:
                old_file.unlink()
        except Exception:
            pass

    filename = HISTORY_DIR / f"scan_{timestamp}_{site_names}.json"
    save_results_to_file(results, filename)

    return filename


def get_history_list():
    """저장된 히스토리 목록 조회"""
    history = []
    
    for file in sorted(HISTORY_DIR.glob("scan_*.json"), reverse=True):
        logging.info(file)
        try:
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            sites = data.get('results', {}).get('sites', [])
            results_count = len(data.get('results', {}).get('results', []))
            
            history.append({
                "filename": file.name,
                "saved_at": data.get('saved_at', ''),
                "sites": [s['url'] for s in sites],
                "results_count": results_count
            })
        except Exception as e:
            print(f"히스토리 로드 오류 ({file}): {e}")
    
    return history[:50]  # 최근 50개만


def export_to_markdown(results):
    """스캔 결과를 Markdown 형식으로 내보내기"""
    md_lines = []
    md_lines.append("# Site Scanner Report")
    md_lines.append(f"\n> Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # 사이트 목록
    md_lines.append("## 📌 스캔 대상")
    for site in results.get('sites', []):
        md_lines.append(f"- **{site['url']}** (스캔: {site.get('lastScan', 'N/A')})")
    
    # 요약 통계
    all_results = results.get('results', [])
    form_count = len([r for r in all_results if r['type'] == 'form'])
    input_count = len([r for r in all_results if r['type'] == 'input'])
    script_count = len([r for r in all_results if r['type'] == 'script'])
    info_count = len([r for r in all_results if r['type'] == 'info'])
    
    md_lines.append("\n## 📊 요약")
    md_lines.append(f"| 항목 | 개수 |")
    md_lines.append(f"|------|------|")
    md_lines.append(f"| Forms | {form_count} |")
    md_lines.append(f"| Inputs | {input_count} |")
    md_lines.append(f"| Scripts | {script_count} |")
    md_lines.append(f"| Information | {info_count} |")
    md_lines.append(f"| **Total** | **{len(all_results)}** |")
    
    # 상세 결과
    for result_type, emoji, label in [
        ('form', '📝', 'Forms'),
        ('input', '⌨️', 'Inputs'),
        ('script', '📜', 'Scripts'),
        ('info', 'ℹ️', 'Information')
    ]:
        type_results = [r for r in all_results if r['type'] == result_type]
        if type_results:
            md_lines.append(f"\n## {emoji} {label}")
            md_lines.append("")
            
            for r in type_results:
                site = next((s for s in results['sites'] if s['id'] == r['siteId']), {})
                site_url = site.get('url', 'Unknown')
                
                if result_type == 'form':
                    md_lines.append(f"### `{r.get('method', 'GET')}` {r.get('url', 'N/A')}")
                    md_lines.append(f"- **Site**: {site_url}")
                    md_lines.append(f"- **Status**: {r.get('status', 'N/A')}")
                    if r.get('details'):
                        md_lines.append("- **Inputs**:")
                        for d in r['details']:
                            md_lines.append(f"  - `{d}`")
                    md_lines.append("")
                    
                elif result_type == 'script':
                    md_lines.append(f"- `{r.get('url', 'N/A')}` ({site_url})")
                    
                elif result_type == 'info':
                    md_lines.append(f"- **{site_url}**: `{r.get('content', 'N/A')[:80]}...`")
                    if r.get('details'):
                        md_lines.append(f"  - {', '.join(r['details'])}")
                    
                else:
                    md_lines.append(f"- {r.get('url', 'N/A')} ({site_url})")
    
    return "\n".join(md_lines)

# ========================================
# 설정 관리
# ========================================
def load_settings():
    """설정 파일에서 설정 불러오기"""
    try:
        if SETTINGS_FILE.exists():
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logging.error(f"설정 로드 오류: {e}")
    return DEFAULT_SETTINGS.copy()

def save_settings_to_file(settings):
    """설정을 파일에 저장"""
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logging.error(f"설정 저장 오류: {e}")
        return False

@app.route('/settings')
def settings_page():
    """설정 페이지"""
    return render_template('settings.html')

@app.route('/api/settings', methods=['GET'])
def get_settings():
    """설정 조회 API"""
    settings = load_settings()
    return jsonify(settings)

@app.route('/api/settings', methods=['POST'])
def update_settings():
    """설정 저장 API"""
    try:
        new_settings = request.get_json()
        current_settings = load_settings()

        # 기존 설정과 병합
        if 'scan_options' in new_settings:
            current_settings['scan_options'] = new_settings['scan_options']
        if 'display_options' in new_settings:
            current_settings['display_options'] = new_settings['display_options']

        if save_settings_to_file(current_settings):
            return jsonify({"success": True, "message": "설정이 저장되었습니다"})
        else:
            return jsonify({"error": "설정 저장 실패"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ========================================
# 라우트 정의
# ========================================

@app.route('/')
def index():
    """메인 대시보드 페이지"""
    # 자동 로드 제거 - 사용자가 직접 불러오기 해야 함
    return render_template('dashboard.html')


def _safe_access_list_filename(name: str) -> bool:
    """access_list JSON 파일명만 허용 (경로 조작 방지)."""
    if not name or name != os.path.basename(name) or ".." in name:
        return False
    return bool(re.match(r"^[A-Za-z0-9._-]+\.json$", name))


@app.route('/list')
def list_page():
    """엔드포인트 목록: 사이트별 저장 데이터를 사이드바에서 선택해 표시."""
    has_history = has_history_scan_files()
    return render_template('list.html', has_history_file=has_history)


@app.route('/vuln')
def vuln_legacy_redirect():
    """기존 /vuln 경로는 /list로 이동."""
    return redirect(url_for('list_page'), code=301)


@app.route('/api/access_list/list')
@app.route('/api/vuln/access/list')  # 하위 호환
def access_list_items():
    """access_list 디렉터리에 저장된 JSON 목록 (최신 수정 순)."""
    items = []
    for p in sorted(
        ACCESS_LIST_DIR.glob("*.json"),
        key=lambda x: x.stat().st_mtime,
        reverse=True,
    ):
        data = load_access_record(p)
        if not data:
            continue
        items.append(
            {
                "filename": p.name,
                "site_label": data.get("site_label", p.stem),
                "updated_at": data.get("updated_at", ""),
            }
        )
    return jsonify({"items": items})


@app.route('/api/access_list/file/<filename>')
@app.route('/api/vuln/access/file/<filename>')  # 하위 호환
def access_list_get_file(filename):
    """저장된 접근 테스트 레코드 한 건."""
    if not _safe_access_list_filename(filename):
        return jsonify({"error": "잘못된 파일명입니다"}), 400
    path = ACCESS_LIST_DIR / filename
    if not path.is_file():
        return jsonify({"error": "파일을 찾을 수 없습니다"}), 404
    data = load_access_record(path)
    if data is None:
        return jsonify({"error": "파일을 읽을 수 없습니다"}), 500
    return jsonify(data)


@app.route('/api/access_list/file/<filename>', methods=['DELETE'])
@app.route('/api/vuln/access/file/<filename>', methods=['DELETE'])  # 하위 호환
def access_list_delete_file(filename):
    """저장된 access_list JSON 삭제. 동일 사이트가 포함된 히스토리(scan_*.json)도 함께 삭제."""
    if not _safe_access_list_filename(filename):
        return jsonify({"error": "잘못된 파일명입니다"}), 400
    path = ACCESS_LIST_DIR / filename
    if not path.is_file():
        return jsonify({"error": "파일을 찾을 수 없습니다"}), 404
    record = load_access_record(path)
    site_label = (record or {}).get("site_label") or ""
    try:
        path.unlink()
        logging.info("access_list 삭제: %s", filename)
    except OSError as e:
        logging.error("access_list 삭제 실패: %s", e)
        return jsonify({"error": str(e)}), 500
    history_deleted: list[str] = []
    if site_label:
        history_deleted = delete_history_files_for_site_label(site_label, HISTORY_DIR)
        if history_deleted:
            logging.info(
                "access_list 삭제에 따른 히스토리 삭제: site=%s files=%s",
                site_label,
                history_deleted,
            )
    return jsonify({"ok": True, "history_deleted": history_deleted})


@app.route('/api/access_list/run', methods=['POST'])
@app.route('/api/vuln/access/run', methods=['POST'])  # 하위 호환
def access_list_run():
    """
    scan_data/history/scan_*.json 전부를 병합한 뒤 사이트(URL)별로 access_list에 저장.
    scan_results.json이 아닌 히스토리를 기준으로 하여, 다수 스냅샷·삭제 후에도 싱크가 맞도록 한다.
    """
    if not has_history_scan_files():
        return jsonify(
            {
                "error": "히스토리가 없거나 읽을 수 없습니다. 대시보드에서 스캔하거나 히스토리를 불러오세요."
            }
        ), 400
    try:
        summaries = export_access_list_from_history_dir(HISTORY_DIR, ACCESS_LIST_DIR)
    except Exception as e:
        logging.exception("access_list 내보내기 오류")
        return jsonify({"error": str(e)}), 500
    logging.info("access_list 저장 완료: %s개 사이트", len(summaries))
    return jsonify({"ok": True, "summaries": summaries})


@app.route('/api/scan', methods=['POST'])
def start_scan():
    """스캔 시작 API"""
    global scan_status
    
    with scan_lock:
        if scan_status["is_running"]:
            return jsonify({"error": "스캔이 이미 진행 중입니다"}), 400
    
    data = request.json
    urls = data.get('urls', [])
    options = data.get('options', {})
    
    if not urls:
        return jsonify({"error": "URL을 입력해주세요"}), 400
    
    # 백그라운드 스캔 시작
    save_callbacks = (save_results_to_file, save_to_history)
    thread = threading.Thread(
        target=run_scan,
        args=(urls, options, scan_status, scan_lock, add_log, save_callbacks)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({"message": "스캔이 시작되었습니다", "urls": urls})


@app.route('/api/status')
def get_status():
    """스캔 상태 조회 API"""
    with scan_lock:
        return jsonify(scan_status)


@app.route('/api/stop', methods=['POST'])
def stop_scan():
    """스캔 중지 API"""
    global scan_status
    
    with scan_lock:
        scan_status["is_running"] = False
        add_log("스캔이 중지되었습니다")
    
    return jsonify({"message": "스캔이 중지되었습니다"})


@app.route('/api/clear', methods=['POST'])
def clear_results():
    """결과 초기화 API"""
    global scan_status
    
    with scan_lock:
        scan_status["results"] = {"sites": [], "results": []}
        scan_status["logs"] = []
        scan_status["progress"] = 0
        add_log("결과가 초기화되었습니다")
    
    return jsonify({"message": "초기화 완료"})


@app.route('/api/save', methods=['POST'])
def save_results():
    """현재 결과를 파일로 저장"""
    global scan_status
    
    with scan_lock:
        results = scan_status["results"]
    
    if not results.get('sites'):
        return jsonify({"error": "저장할 결과가 없습니다"}), 400
    
    # 현재 결과 저장 (자동 저장용)
    save_results_to_file(results)
    
    # 히스토리에도 저장
    history_file = save_to_history(results)
    add_log(f"결과 저장 완료: {history_file.name}")
    
    return jsonify({
        "message": "저장 완료",
        "filename": history_file.name
    })


@app.route('/api/load', methods=['POST'])
def load_results():
    """저장된 결과 불러오기"""
    global scan_status

    data = request.get_json(silent=True) or {}
    filename = data.get("filename")

    if filename:
        safe_name = os.path.basename(str(filename).strip())
        if not safe_name or safe_name in (".", ".."):
            return jsonify({"error": "잘못된 파일명입니다"}), 400
        history_root = HISTORY_DIR.resolve()
        try:
            filepath = (history_root / safe_name).resolve()
            filepath.relative_to(history_root)
        except ValueError:
            return jsonify({"error": "허용되지 않은 경로입니다"}), 400
        except OSError:
            return jsonify({"error": "경로를 확인할 수 없습니다"}), 400
    else:
        filepath = RESULTS_FILE

    loaded = load_results_from_file(filepath)

    if loaded is None:
        return jsonify({"error": "저장된 결과가 없습니다"}), 404

    try:
        with scan_lock:
            scan_status["results"] = loaded.get("results", {"sites": [], "results": []})
            fp_name = getattr(filepath, "name", None) or "scan_results.json"
            add_log(f"결과 로드 완료: {fp_name}")
    except Exception as e:
        logging.exception("결과 로드 적용 오류")
        return jsonify({"error": f"로드 처리 중 오류: {e}"}), 500

    return jsonify(
        {
            "message": "로드 완료",
            "saved_at": loaded.get("saved_at"),
            "results": scan_status["results"],
        }
    )


@app.route('/api/history')
def get_history():
    """저장된 히스토리 목록 조회"""
    history = get_history_list()
    return jsonify({"history": history})


@app.route('/api/history/<filename>', methods=['DELETE'])
def delete_history(filename):
    """히스토리 파일 삭제"""
    filepath = HISTORY_DIR / filename
    
    if not filepath.exists():
        return jsonify({"error": "파일을 찾을 수 없습니다"}), 404
    
    try:
        filepath.unlink()
        add_log(f"히스토리 삭제: {filename}")
        return jsonify({"message": "삭제 완료"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/export/markdown', methods=['POST'])
def export_markdown():
    """결과를 Markdown으로 내보내기"""
    global scan_status
    
    with scan_lock:
        results = scan_status["results"]
    
    if not results.get('sites'):
        return jsonify({"error": "내보낼 결과가 없습니다"}), 400
    
    md_content = export_to_markdown(results)
    
    # 파일로 저장
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    md_filename = DATA_DIR / f"report_{timestamp}.md"
    
    with open(md_filename, 'w', encoding='utf-8') as f:
        f.write(md_content)
    
    add_log(f"Markdown 내보내기 완료: {md_filename.name}")
    
    return jsonify({
        "message": "내보내기 완료",
        "filename": md_filename.name,
        "content": md_content
    })


@app.route('/api/export/download/<filename>')
def download_file(filename):
    """파일 다운로드"""
    # 보안: 경로 조작 방지
    safe_filename = os.path.basename(filename)
    
    # JSON 또는 MD 파일 찾기
    for directory in [DATA_DIR, HISTORY_DIR]:
        filepath = directory / safe_filename
        if filepath.exists():
            return send_file(filepath, as_attachment=True)


# ========================================
# 스캔 로직
# ========================================

def add_log(message):
    """로그 추가"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    scan_status["logs"].append(f"[{timestamp}] {message}")
    # 최근 100개만 유지
    if len(scan_status["logs"]) > 100:
        scan_status["logs"] = scan_status["logs"][-100:]




# ========================================
# 메인 실행
# ========================================

if __name__ == '__main__':
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    print("=" * 50)
    print("  Site Scanner Dashboard")
    print("  http://localhost:5000")
    print("=" * 50)
    
    # debug 필요한 경우, True 로 변경
    app.run(debug=False, host='0.0.0.0', port=5000)