from module.imports import *
""" form 태그 외부의 Input 태그 수집 """
def input_func(self):
    # print(f"{colors('[*] form 태그 외부의 Input 태그 수집 함수 실행', 'green')}")
    if not self._inputs_in_forms:
        form_func(self)
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