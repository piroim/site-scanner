from module.imports import * 

def main():
    session = HTTPSession()

    #만약 세션이 필요한 사이트라면 별도로 세션을 업데이트 해서 사용
    # session.headers.update({'Cookie': 'PHPSESSID=2m1k4p037ncv91iadrmp1dpro4'})
    set_session = session.headers
    # url = "http://192.168.198.128:22223/board.php"
    url = "https://url/login.do"
    res = session.get(url=url)

    if res.status_code == 200:
        form_ext2(url, res.text)
        # form_ext(res.text)
    else:
        print(f"Failed to fetch form data: {res.status_code}")

if __name__ == "__main__":
    main()
