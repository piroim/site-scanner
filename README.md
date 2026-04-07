# Site Scanner - 실시간 웹 대시보드
Flask 기반의 실시간 웹 스캐너 대시보드입니다.

### 실행 이미지(.gif) 추가예정
---

## 📁 파일 구조

```
site-scanner/
├── app.py                      # Flask: 대시보드·List·스캔/히스토리/access_list API
├── README.md
├── DEVLOG.md
│
├── scanner/                    # 핵심 파이프라인
│   ├── run_scan.py             # Playwright 스캔 (forms / inputs / scripts / info / links)
│   ├── run_list.py             # 히스토리 병합 → 구역별 엔드포인트(GET·POST·LINK·JS) 집계
│   ├── access_list.py          # history → access_list/*.json (List 페이지와 동기)
│   └── config.py               # 사이트별 헤더·쿠키·세션
│
├── templates/                  # UI
│   ├── dashboard.html          # 스캔·필터·히스토리
│   ├── list.html               # 엔드포인트 목록(List)·access_list 뷰
│   ├── settings.html           # 스캔·표시 옵션
│   └── includes/
│       └── app_header.html     # 공통 네비게이션
│
├── scan_data/                  # 로컬 저장 (스캔·동기화의 실제 데이터)
│   ├── scan_results.json       # 마지막 스캔 결과(대시보드 기본)
│   ├── settings.json           # 사용자 설정
│   ├── history/                # scan_*.json (List/access_list 동기화의 기준)
│   └── access_list/            # 사이트별 구역 JSON
│
├── module/                     # HTTP 헤더·공통 import (스캔 보조)
│   ├── headers_module.py
│   └── imports.py
│
├── static/
│   └── style.css               # 다크/라이트 테마
│
└── docs/                       # 이슈·메모
    ├── error_issue_1.md
    ├── edit_issue_1.md
    └── error_template.md
```

## 🚀 실행 방법

### 1. 필요 패키지 설치

```bash
pip install flask requests beautifulsoup4 playwright
playwright install chromium
```

### 2. 서버 실행

```bash
python app.py
```

### 3. 브라우저에서 접속

```
http://localhost:5000
```

## ✨ 주요 기능

| 기능 | 설명 |
|------|------|
| **URL 스캔** | 여러 URL을 줄바꿈으로 입력하여 동시 스캔 |
| **Form 추출** | HTML form 태그 및 action URL 수집 |
| **Input 추출** | 독립적인 input 필드 수집 |
| **Script 추출** | 외부 스크립트 및 인라인 AJAX URL 추출 |
| **Info 추출** | API Key, Password, Token 등 민감 정보 탐지 |
| **a href 추출** | a href 경로 수집 |
| **실시간 진행률** | 스캔 진행 상황 실시간 표시 |
| **필터링** | 타입별, 사이트별, 검색어 필터링 |
| **히스토리** | URL별 스캔 결과 자동 저장 및 불러오기 |
| **다크/라이트 모드** | 테마 전환 지원 |

## 🎶 API 엔드포인트

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/` | 대시보드 페이지 |
| GET | `/settings` | 설정 페이지 |
| GET | `/api/status` | 스캔 상태 조회 |
| GET | `/api/history` | 히스토리 목록 조회 |
| GET | `/api/settings` | 설정 조회 |
| POST | `/api/scan` | 스캔 시작 |
| POST | `/api/stop` | 스캔 중지 |
| POST | `/api/clear` | 결과 초기화 |
| POST | `/api/save` | 결과 저장 |
| POST | `/api/load` | 결과 불러오기 |
| POST | `/api/settings` | 설정 저장 |
| POST | `/api/export/markdown` | 마크다운 내보내기 |
| DELETE | `/api/history/<filename>` | 히스토리 삭제 |

## ⚙️ 설정

### 스캔 옵션 (Settings 페이지)

- **Forms**: HTML 폼 태그 수집
- **Inputs**: 입력 필드 수집
- **Scripts**: 스크립트 및 AJAX URL 수집
- **Info**: 민감 정보 패턴 탐지

### 사이트별 세션 설정 (scanner/config.py)

특정 사이트에 로그인이 필요한 경우:

```python
SITE_SESSIONS = {
    "example.com": parse_headers("""
        Cookie: PHPSESSID=your_session_id
        Authorization: Bearer your_token
    """),
}
```

### 테마 설정

Settings > 표시 설정에서 다크/라이트 모드 전환 가능

## 📝 사용 예시

### 단일 URL 스캔
```
https://example.com
```

### 여러 URL 동시 스캔
```
https://example.com
https://test.com
https://demo.org
```

### 단축키
- `Ctrl + Enter`: URL 입력 후 빠른 스캔 시작

## 📋 변경 이력

- DEVLOG.md 파일을 참고해주세요.