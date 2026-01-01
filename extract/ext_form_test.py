from module.imports import *
from extract.report_test import report_test
from extract.ext_result import print_result

class HTMLParser:
    def __init__(self, url, data):
        self.url = url
        self.data = data
        self.soup = BeautifulSoup(data, 'html.parser')
        self._inputs_in_forms = set() #Input 태그 추출 시 중복 방지를 위해 사용

    def parse_all_elements(self, tags=None):
        print(f"{colors('[*] 모든 요소 추출 함수 실행', 'green')}")
        
        tag_parsers = {
            'forms': self.parser_form,
            'inputs': self.parser_inputs,
            'scripts': self.parser_script,
            'a_tags': self.parser_a,
            'information': self.parser_infomation
        }

        if tags is None:
            tags = list(tag_parsers.keys())

        results = {'url': self.url}
        print(f"tags: {tags}")

        #태그별로 추출 함수 실행(실행 시간이 느릴 수 있음)
        for tag in tags:
            print(f"tag: {tag}")
            if tag in tag_parsers:
                #tag_parsers[tag]() = parser_form() 형식으로 실행
                results[tag] = tag_parsers[tag]()
                print_result(results) #결과 출력
                report_test(results) #결과 저장
                print(f"print_result[tag]: {print_result(results)}")
        print("="*60)

    #form 태그 추출 함수
    def parser_form(self):
        print(f"{colors('[*] form 태그 추출 함수 실행', 'green')}")
        forms = []

        #enumerate는 Index 설정을 위해 사용
        for idx, form in enumerate(self.soup.find_all('form'), 1):
            form_data = {
                'index': idx,
                'id': form.get('id', ''),
                'action': form.get('action', ''),
                'method': form.get('method', 'GET').upper(  ),
                'inputs': [], #아래에 있는 for문에서 inputs 리스트에 추가
                'status_code': None,
                'req_url': urljoin(self.url, form.get('action', ''))
            }
            #form 태그 내 input 태그 추출
            for form_inp in form.find_all(['input']):
                self._inputs_in_forms.add(id(form_inp))
                form_data['inputs'].append({
                    'tag': form_inp.name,
                    'id': form_inp.get('id', ''),
                    'name': form_inp.get('name', ''),
                    'value': form_inp.get('value', ''),
                })
            
            #Request 요청 전송 및 상태코드 반환
            if form_data['method'] == 'POST':
                #POST요청은 데이터가 생성되거나 수정되는 경우가 있기 때문에 요청 전송 X
                #상태코드를 확인할 수 없는데...음 이건 확인 필요
                print(f"POST TEST: {form_data['req_url']}")
                form_data['status_code'] = "999" #POST는 요청하지 않을 거기 때문에 별도 값 사용

            elif form_data['method'] == 'GET':
                # print(f"GET TEST: {form_data['req_url']}")
                #[수정필요] 세션의 헤더 값을 너무 많이 업데이트해서, 코드 복잡도 증가
                session = HTTPSession()
                session.headers.update(get_headers())
                session.headers.update({'Cookie': 'PHPSESSID=2m1k4p037ncv91iadrmp1dpro4'})
                get_res = session.get(url=form_data['req_url'], params=form_data['inputs'][0].get('name'), headers=get_headers())
                # print(f"[{get_res.status_code}] {self.url} {form_data['inputs'][0].get('name')}")
                form_data['status_code'] = get_res.status_code
                # print(f"get_res url : {get_res.url}")
            else:
                print(f"{colors('[*] 메서드 오류', 'red')}")
            # print(f"self._inputs_in_forms: {self._inputs_in_forms}")
            #마지막 단계 forms 리스트에 저장
            forms.append(form_data)

        """
            form 태그는 form_data 리스트에 저장되어 있고,
            form_inp 태그는 form_data['inputs'] 리스트에 저장되어 있음
            -> 출력 및 데이터를 사용할 때는 form 리스트와 form_inp 리스트를 사용
        """
        return forms

    """ form 태그 외부의 Input 태그 수집 """
    def parser_inputs(self):
        # print(f"{colors('[*] form 태그 외부의 Input 태그 수집 함수 실행', 'green')}")
        if not self._inputs_in_forms:
            self.parser_form()
        inputs = []
        for inp in self.soup.find_all(['input']):
            if id(inp) not in self._inputs_in_forms:
                session = HTTPSession()
                session.headers.update(get_headers())
                get_res = session.get(url=self.url, data=inp.get('name', ''))
                inputs.append({
                    'tag': inp.name,
                    'id': inp.get('id', ''),
                    'name': inp.get('name', ''),
                    'method': 'GET',
                    'value': inp.get('value', ''),
                    'req_url': self.url + '?' + inp.get('name', ''),
                    'status_code': get_res.status_code
                })
        return inputs

    """ script 태그 추출 함수
        여기에다가 script 태그 가져왔을 때, AJAX 결과 값 가져오도록 추가하면 될 듯 (26.01.01)
    """
    def parser_script(self):
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
                })
        #script 태그는 우선 src 있는 것만 가져오도록 설정, 나중에 script 태그 내에 API 가져오도록 설정 필요
        # print(f"scripts: {scripts}")
        return scripts

    """ A태그 추출 함수 """
    def parser_a(self):
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

    """ 정보 추출 함수 """
    def parser_infomation(self):
        print(f"{colors('[*] 정보 추출 함수 실행', 'green')}")
        information = []
        
        #정보를 가져오는 패턴식
        patterns = {
            'text': r'pattern',
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

    

def save_test(results):
    #데이터 저장 공통 코드 (print 코드는 나중에 삭제)
    save_file = "extract/save/ext_form.md"
    with open(save_file, "a", encoding="utf-8") as f:
        if results['forms']:
            for form in results['forms']:
                # print(f"[{form['method']}] {form['req_url']} [{form['status_code']}]")
                f.write(f"[{form['method']}] {form['req_url']} [{form['status_code']}]\n")
        if results['inputs']:
            for input in results['inputs']:
                # print(f"[GET] {input['req_url']} {input['status_code']}")
                f.write(f"[GET] {input['req_url']} {input['status_code']}\n")
        if results['scripts']:
            for script in results['scripts']:
                # print(f"[SCRIPT] {script['src']}")
                is_js = script['src'].lower().endswith('.js')
                if is_js:
                    f.write(f"[JS] {script['req_url']}{script['src']}\n")
                else:
                    f.write(f"[SCRIPT] {script['req_url']}{script['src']}\n")

def form_ext2(url, data, tags=None):
    parser = HTMLParser(url, data)
    parser.parse_all_elements(tags=tags)