from module.imports import *

""" 정보 추출 함수 """
def info_func(self):
    print(f"{colors('[*] 정보 추출 함수 실행', 'green')}")
    information = []
    
    #정보를 가져오는 패턴식
    patterns = {
        'text': r'Doctype',
    }
    html_text = str(self.soup)
    html_lines = html_text.split('\n')

    for name, pattern in patterns.items():
        for line_num, line in enumerate(html_lines, 1):
            matches = re.search(pattern, line, re.IGNORECASE)
            if matches:
                information.append({
                    'type': name,
                    'match': matches,
                    'line_num': line_num,
                    'line_content': line.strip()
                })
                print(f"information: {name}:{line_num} : {line.strip()}")

    return information