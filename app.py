"""
Site Scanner - Flask Web Server
실시간 대시보드를 위한 웹 서버

실행: python app.py
접속: http://localhost:5000
"""

from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
from datetime import datetime
import io
import mimetypes
from pathlib import Path
from scanner import run_scan
import threading
import json
import os
import re
import logging
from scanner.access_list import (
    delete_all_access_list_and_history,
    delete_history_files_for_site_label,
    export_access_list_from_history_dir,
    load_access_record,
)
from scanner.export_csv import (
    write_access_list_csv,
    write_access_list_csv_for_file,
    write_access_list_csv_zip_per_site,
)
from scanner.scan_io import HISTORY_DIR, RESULTS_FILE, SCAN_DATA_DIR

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
DATA_DIR = SCAN_DATA_DIR
DATA_DIR.mkdir(exist_ok=True)
HISTORY_DIR.mkdir(exist_ok=True)
# CSV/ZIP 내보내기 임시 저장 후 다운로드 시 삭제
CSV_DATA_DIR = Path(__file__).resolve().parent / "csv_data"
CSV_DATA_DIR.mkdir(exist_ok=True)
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
# save_results_to_file, save_to_history → scanner.scan_io

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


@app.route('/api/access_list/all', methods=['DELETE'])
@app.route('/api/vuln/access/all', methods=['DELETE'])  # 하위 호환
def access_list_delete_all():
    """
    access_list 디렉터리의 저장 URL 목록 JSON과 history의 scan_*.json을 모두 삭제한다.
    """
    try:
        result = delete_all_access_list_and_history(ACCESS_LIST_DIR, HISTORY_DIR)
    except OSError as e:
        logging.error("access_list 전체 삭제 실패: %s", e)
        return jsonify({"error": str(e)}), 500
    access_n = len(result["access_list"])
    hist_n = len(result["history"])
    logging.info(
        "access_list 전체 삭제: access_list=%s개, history=%s개",
        access_n,
        hist_n,
    )
    return jsonify(
        {
            "ok": True,
            "deleted": result["access_list"],
            "history_deleted": result["history"],
        }
    )


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
    
    # 백그라운드 스캔 시작 (결과는 scan_io로 자동 저장)
    thread = threading.Thread(
        target=run_scan,
        args=(urls, options, scan_status, scan_lock, add_log),
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


@app.route('/api/export/csv', methods=['POST'])
def export_access_list_csv():
    """access_list/*.json을 병합한 CSV를 csv_data에 저장하고 파일명을 반환한다."""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = CSV_DATA_DIR / f"access_list_{timestamp}.csv"
        write_access_list_csv(out_path, ACCESS_LIST_DIR)
    except OSError as e:
        logging.exception("CSV 내보내기 실패")
        return jsonify({"error": str(e)}), 500
    add_log(f"CSV 내보내기: {out_path.name}")
    return jsonify(
        {
            "message": "내보내기 완료",
            "filename": out_path.name,
        }
    )


@app.route('/api/access_list/export/csv/site', methods=['POST'])
def access_list_export_csv_site():
    """선택한 access_list JSON 한 건만 CSV로 저장한다."""
    data = request.get_json(silent=True) or {}
    filename = data.get("filename")
    if not filename or not _safe_access_list_filename(str(filename)):
        return jsonify({"error": "잘못된 파일명입니다"}), 400
    path = ACCESS_LIST_DIR / filename
    if not path.is_file():
        return jsonify({"error": "파일을 찾을 수 없습니다"}), 404
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = Path(filename).stem
    out_path = CSV_DATA_DIR / f"access_list_{stem}_{timestamp}.csv"
    try:
        write_access_list_csv_for_file(out_path, path)
    except OSError as e:
        logging.exception("CSV(단일 사이트) 내보내기 실패")
        return jsonify({"error": str(e)}), 500
    logging.info("CSV 단일 사이트: %s", out_path.name)
    return jsonify({"ok": True, "filename": out_path.name})


@app.route('/api/access_list/export/csv/zip', methods=['POST'])
def access_list_export_csv_zip():
    """사이트마다 CSV를 분리해 하나의 ZIP으로 저장한다."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = CSV_DATA_DIR / f"access_list_by_site_{timestamp}.zip"
    try:
        write_access_list_csv_zip_per_site(out_path, ACCESS_LIST_DIR)
    except OSError as e:
        logging.exception("CSV ZIP 내보내기 실패")
        return jsonify({"error": str(e)}), 500
    logging.info("CSV ZIP: %s", out_path.name)
    return jsonify({"ok": True, "filename": out_path.name})


def _mimetype_for_download(name: str) -> str:
    lower = name.lower()
    if lower.endswith(".csv"):
        return "text/csv; charset=utf-8"
    if lower.endswith(".zip"):
        return "application/zip"
    return mimetypes.guess_type(name)[0] or "application/octet-stream"


@app.route('/api/export/download/<filename>')
def download_file(filename):
    """파일 다운로드. csv_data의 CSV/ZIP는 응답 직전에 삭제(생성→다운로드→삭제)."""
    safe_filename = os.path.basename(filename)
    if not safe_filename or safe_filename in (".", "..") or ".." in safe_filename:
        return jsonify({"error": "잘못된 파일명입니다"}), 400

    csv_path = (CSV_DATA_DIR / safe_filename).resolve()
    try:
        csv_path.relative_to(CSV_DATA_DIR.resolve())
    except ValueError:
        return jsonify({"error": "허용되지 않은 경로입니다"}), 400

    if csv_path.is_file():
        try:
            payload = csv_path.read_bytes()
        except OSError:
            return jsonify({"error": "파일을 읽을 수 없습니다"}), 500
        try:
            csv_path.unlink()
        except OSError:
            pass
        return send_file(
            io.BytesIO(payload),
            as_attachment=True,
            download_name=safe_filename,
            mimetype=_mimetype_for_download(safe_filename),
        )

    for directory in (DATA_DIR, HISTORY_DIR):
        filepath = (directory / safe_filename).resolve()
        try:
            filepath.relative_to(directory.resolve())
        except ValueError:
            continue
        if filepath.is_file():
            return send_file(filepath, as_attachment=True)

    return jsonify({"error": "파일을 찾을 수 없습니다"}), 404


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