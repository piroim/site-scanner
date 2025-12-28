from module.imports import *
# Python에서 request library를 사용할 때, header 정보를 자동으로 변환 및 입력하는 코드
# "from headers_module.py import get_headers, get_data" 로 사용 
#

class HTTPSession(requests.Session):
    def __init__(self, verify=False):
        super().__init__() #기본 생성자 호출, 부모클래스인 request.Session의 __init__을 호출
        self.verify = verify
        # self.headers.update(get_headers())

"""burp_request 헤더 입력 시, 자동 변환 (유동적인 값은 .update 사용)"""
def get_headers() -> dict:
    #원문 헤더 문자열 변환
    header_data = """
        User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36
        Accept-Encoding: gzip, deflate, br
        Accept: */*
        Connection: keep-alive
    """
    return parse_headers(header_data)

def parse_headers(header_data: str) -> dict:
    #HTTP 헤더를 Dictionary로 파싱
    headers = {}

    for line in header_data.strip().splitlines():
        if ": " in line:
            key, value = line.split(": ", 1)
            headers[key.strip()] = value.strip()
    return headers

"""매개변수를 data 형식으로 변환 (고정된 값일 경우 사용)"""
def get_data() -> dict:
    """ 원문 데이터 문자열 변환 """
    data_string = ""
    return parse_data(data_string)

def parse_data(data_string: str) -> dict:
    """ URL 데이터를 Dictionary로 파싱 """
    datas = {}
    
    params = data_string.split('&')
    for param in params:
        if '=' in param:
            key, value = param.split('=', 1)
            datas[key] = value
    
    return datas

#BurpSuite Proxy Setting
def get_proxy():
    proxy_set = {"http": "127.0.0.1:8080","https": "127.0.0.1:8080"}
    return proxy_set
