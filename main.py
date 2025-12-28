from module.imports import * 

# 세션과 헤더만 관리하는 간단한 HTTP 세션 클래스
# class HTTPSession:
#     def __init__(self, verify=False):
#         self.session = requests.Session()
#         self.session.verify = verify
#         self.session.headers.update(get_headers())

        #로그인이 필요한 사이트는 인증세션 추가

def main():
    session = HTTPSession()

    #만약 세션이 필요한 사이트라면 별도로 세션을 업데이트 해서 사용
    session.headers.update({'Cookie': 'PHPSESSID=2m1k4p037ncv91iadrmp1dpro4'})
    set_session = session.headers
    # url = "http://192.168.198.128:22223/board.php"
    url = "https://rtms.lxpantos.com/login.do"
    res = session.get(url=url)

    if res.status_code == 200:
        form_ext2(url, res.text)
        # form_ext(res.text)
    else:
        print(f"Failed to fetch form data: {res.status_code}")

if __name__ == "__main__":
    main()
