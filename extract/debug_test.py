#데이터 추출 함수 DEBUG 코드 (26.01.01)
#BeautifulSoup의 Comment는 주석 내용을 확인하고 파싱해오는 함수
from bs4 import BeautifulSoup, Comment

html = """


"""

soup = BeautifulSoup(html, 'html.parser')

# 주석 내용 확인


for a_comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
    print(f"a_comment: {a_comment}")
    a_data = BeautifulSoup(a_comment.string, 'html.parser')
    a_tags = []
    for a in a_data.find_all('a', href=True):
        href = a.get('href', '')
        if href:
            a_tags.append({
                'href': href,
                'text': a_data.get_text(strip=True),
                'status_code': None,
            })
    print(f"a_tags: {a_tags}")