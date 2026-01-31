# Site Scanner - 실시간 웹 대시보드
Flask 기반의 실시간 웹 스캐너 대시보드입니다.

### 실행 이미지(.gif) 추가예정
---

## 📁 파일 구조

```
site-scanner/
├── app.py                      # Flask 웹 서버 (메인 실행 파일)
├── README.md
├── DEVLOG.md                   # 개발 로그
│
├── scanner/                    # 스캔 로직 모듈
│   ├── __init__.py
│   ├── config.py               # 헤더/세션 설정 (사이트별 쿠키 등)
│   └── run_scan.py             # 스캔 함수 (forms, inputs, scripts, info)
│
├── module/                     # 공통 모듈
│   ├── headers_module.py       # HTTP 헤더 정의 및 파싱
│   └── imports.py              # 공통 라이브러리 import
│
├── templates/                  # HTML 템플릿
│   ├── dashboard.html          # 메인 대시보드
│   └── settings.html           # 설정 페이지
│
├── static/                     # 정적 파일
│   └── style.css               # 스타일시트 (다크/라이트 모드)
│
├── scan_data/                  # 스캔 결과 저장
│   ├── scan_results.json       # 최근 스캔 결과
│   ├── settings.json           # 사용자 설정
│   └── history/                # URL별 히스토리
│
└── docs/                       # 문서
    ├── error_issue_1.md        # 오류 리포트
    └── edit_issue_1.md         # 수정 리포트
```

## 🚀 실행 방법

### 1. 필요 패키지 설치

```bash
pip install flask requests beautifulsoup4
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

## ⚠️ 주의사항

- **허가된 대상**에만 사용하세요.
- 과도한 요청은 서버에 부하를 줄 수 있습니다.

## 📋 변경 이력

- DEVLOG.md 파일을 참고해주세요.