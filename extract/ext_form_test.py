from module.imports import *
from extract.report_test import report_test
from extract.ext_result import print_result
from module.patterns import get_ajax_urls
from extract.infor_func import info_func
from extract.a_func import a_func
from extract.form_func import form_func
from extract.input_func import input_func
from extract.script_func import script_func

class HTMLParser:
    def __init__(self, url, data):
        self.url = url
        self.data = data
        self.soup = BeautifulSoup(data, 'html.parser')
        self._inputs_in_forms = set() #Input 태그 추출 시 중복 방지를 위해 사용

    def parse_tags(self, tags):
        tags_parser = {
            'information': info_func(self),
            'a_tags': a_func(self),
            'forms': form_func(self),
            'inputs': input_func(self),
            'scripts': script_func(self),
        }

        if tags is None:
            tags = list(tags_parser.keys())
        results = {'url': self.url} #[260109] URL을 넣어주는 이유는, 결과 출력할 때 URL을 같이 보여주기 위함

        #태그별로 추출 함수 실행(실행 시간이 느릴 수 있음)
        for tag in tags:
            print(f"{colors('[DEBUG] tag', 'red')}: {tag}")
            if tag in tags_parser:
                #tag_parsers[tag]() = parser_form() 형식으로 실행
                results[tag] = tags_parser[tag]
                print(f"{colors('[DEBUG] results', 'red')}: {results}")
        print_result(results) #결과 출력
        report_test(results) #결과 저장
        print("="*60)

def form_ext2(url, data, tags=None):
    parser = HTMLParser(url, data)
    parser.parse_tags(tags=tags)
    # parser.parse_all_elements(tags=tags)