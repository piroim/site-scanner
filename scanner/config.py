"""
스캔 설정 파일
- 사이트별 세션/쿠키 설정
- 기본 헤더 설정
- headers_module과 연계
"""

from module.headers_module import get_headers, parse_headers


# ========================================
# 기본 헤더 (headers_module 사용)
# ========================================
DEFAULT_HEADERS = get_headers()

# ========================================
# 사이트별 세션 설정
# - 키: 도메인 (예: "example.com")
# - 값: 헤더 딕셔너리
# ========================================
SITE_SESSIONS = {
    # 예시: PHP 세션이 필요한 사이트
    # "example.com": parse_headers("""
    #     GET /board.php HTTP/1.1
    #     Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7
    #     Accept-Encoding: gzip, deflate
    #     Accept-Language: ko,en-US;q=0.9,en;q=0.8,zh-CN;q=0.7,zh;q=0.6
    #     Connection: keep-alive
    #     Cookie: wp-settings-time-1=1764486488; PHPSESSID=n4tgb66n5r65jkk2rgivq7knsh
    #     Host: example.com
    #     Referer: http://example.com/board.php
    #     Upgrade-Insecure-Requests: 1
    #     User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36
    # """)

    # 예시: 여러 헤더가 필요한 사이트 (Burp에서 복사한 헤더 그대로 사용 가능)
    # "api.example.com": parse_headers("""
    #     Authorization: Bearer your_token_here
    #     Cookie: session=xyz789
    #     X-Custom-Header: custom_value
    # """),
}

# ========================================
# 요청 설정
# ========================================
REQUEST_CONFIG = {
    "timeout": 10,          # 요청 타임아웃 (초)
    "verify_ssl": False,    # SSL 인증서 검증 여부
    "delay": 0.5,           # 요청 간 딜레이 (초)
}