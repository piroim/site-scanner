from module.imports import *

#form 태그 추출 함수
def form_func(self):
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