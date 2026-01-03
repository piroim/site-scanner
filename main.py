from module.imports import * 

def main():
    session = HTTPSession()

    #만약 세션이 필요한 사이트라면 별도로 세션을 업데이트 해서 사용
    # session.headers.update({'Cookie': 'PHPSESSID=2m1k4p037ncv91iadrmp1dpro4'})
    set_session = session.headers
    # url = "http://192.168.198.128:22223/board.php"
    url = "https://www.lxhausys.co.kr/"
    res = session.get(url=url)

    if res.status_code == 200:
        #추출할 태그만 설정,기본 값은 전체 추출(None)
        # tags = None #전체추출
        tags = ['scripts'] #특정 태그 추출
        form_ext2(url, res.text, tags)
        # form_ext(res.text)
    else:
        print(f"Failed to fetch form data: {res.status_code}")

if __name__ == "__main__":
    main()
