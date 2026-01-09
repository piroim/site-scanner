from module.imports import *

""" A태그 추출 함수 """
def a_func(self):
    print(f"{colors('[*] A태그 추출 함수 실행', 'green')}")
    a_tags = []
    # href 속성이 있는 a 태그만 찾기
    for a in self.soup.find_all('a', href=True):
        href = a.get('href', '')
        # href가 비어있지 않은 경우만 추가
        if href:
            a_tags.append({
                'href': href,
                'text': a.get_text(strip=True),  # 텍스트 추출 수정
                'status_code': None,
            })

    #주석 처리된 a 태그의 href 속성 가져오기
    for a_comment in self.soup.find_all(string=lambda text: isinstance(text, Comment)):
        print(f"a_comment: {a_comment}")
        a_data = BeautifulSoup(a_comment.string, 'html.parser')
        for a in a_data.find_all('a', href=True):
            href = a.get('href', '')
            if href:
                a_tags.append({
                    'href': href,
                    'text': a_data.get_text(strip=True),
                    'status_code': None,
                })
    return a_tags