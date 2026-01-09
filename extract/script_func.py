from module.imports import *
""" script 태그 추출 함수
    여기에다가 script 태그 가져왔을 때, AJAX 결과 값 가져오도록 추가하면 될 듯 (26.01.01)
"""
def script_func(self):
    print(f"{colors('[*] script 태그 추출 함수 실행', 'green')}")
    scripts = []
    for script in self.soup.find_all(['script']):
        src = script.get('src', '')
        if src and 'google' not in src.lower(): #google 관련 스크립트는 제외
            #script 태그 추출 시 요청도 같이 전송
            session = HTTPSession()
            session.headers.update(get_headers())
            get_res = session.get(url=self.url, data=script.get('src', ''))
            scripts.append({
                'req_url': self.url.strip('/'),
                'src': script.get('src', ''),
                'status_code': get_res.status_code,
                'ajax_urls': [], #ajax 요청 URL 추출
            })
        elif not src:
            content = script.get_text(strip=True)
            ajax_urls = get_ajax_urls(self, content)

            #값이 있는 LIST만 추가
            if ajax_urls: 
                # print(f"[DEBUG] ajax_url: {ajax_urls}")
                session = HTTPSession()
                session.headers.update(get_headers())

                if ajax_urls[1] == 'GET':
                    get_res = session.get(url=self.url, data=ajax_urls[0])
                    scripts.append({
                        'req_url': self.url.strip('/'),
                        'src': 'inline',
                        'status_code': get_res.status_code,
                        'ajax_urls': ajax_urls[0]
                    })
                elif ajax_urls[1] == 'POST':
                    # get_res = session.post(url=self.url, data=ajax_urls[0])
                    print(f"POST TEST: {ajax_urls[0]}")
                else:
                    print(f"{colors('[*] 메서드 오류', 'red')}")
    return scripts