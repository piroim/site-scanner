# Site Scanner 오류 리포트

## 오류 #001: 히스토리 파일 저장 실패 (Windows 파일명 오류)

### 발생일
2026-01-24

### 증상
- 특정 사이트 스캔 후 `.json` 히스토리 파일이 저장되지 않음
- 파일이 0 bytes로 생성되거나 확장자 없이 생성됨

### 영향받은 파일
- `app.py` - `save_to_history()` 함수

### 원인
Windows 파일 시스템에서 파일명에 사용할 수 없는 문자가 포함됨

```python
# 문제 코드 (app.py:95)
site_names = "_".join([s['url'].replace('.', '-')[:20] for s in results.get('sites', [])[:3]])
```

**예시:**
- 입력: `192.168.198.128:22223`
- 변환 후: `192-168-198-128:22223` (콜론 `:` 그대로 남음)
- 결과: Windows에서 파일 생성 실패

### Windows 파일명 금지 문자
```
: / \ * ? " < > |
```

### 해결 방법
```python
# 수정된 코드
site_names = "_".join([
    s['url'].replace('.', '-').replace(':', '-').replace('/', '-')[:20]
    for s in results.get('sites', [])[:3]
])
```

### 확인 방법
```bash
# 히스토리 폴더 확인
ls -la scan_data/history/

# 정상: 파일 크기 > 0, .json 확장자 있음
-rw-r--r-- 1 user 2234 scan_20260124_154128_192-168-198-128-22223.json

# 비정상: 파일 크기 = 0, .json 확장자 없음
-rw-r--r-- 1 user    0 scan_20260124_154055_192-168-198-128
```

### 예방 조치
URL에서 파일명 생성 시 항상 특수문자 치환 필요:
```python
import re

def sanitize_filename(name):
    """파일명에 사용 불가능한 문자 제거"""
    return re.sub(r'[\\/:*?"<>|]', '-', name)
```
