from module.imports import *
"""
    결과 출력 함수
    - 태그가 추가될 경우 여기에 추가해서 출력
"""
def print_result(results):
    print(banner("site-scanner banner"))


    #form 태그 출력
    if results['forms']:
        print(section("FORM 결과"))
        for form in results['forms']:
            print(f"[{form['method']}][{form['status_code']}] {form['req_url']}")
            for form_inp in form['inputs']:
                print(f" └ <{form_inp['tag']} name='{form_inp['name']}' id='{form_inp['id']}' value='{form_inp['value']}'>")
        
    if results['inputs']:
        print(section("INPUT 결과"))
        for inputs in results['inputs']:
            print(f"[{inputs['method']}][{inputs['status_code']}] {inputs['req_url']}")

    if results['scripts']:
        print(section("SCRIPT 결과"))
        for script in results['scripts']:
            is_js = script['src'].lower().endswith('.js')
            if is_js:
                print(f"[JS][{script['status_code']}] {script['src']}")
            else:
                print(f"[SCRIPT][{script['status_code']}] {script['src']}")

    if results['information']:
        print(section("INFORMATION 결과"))
        for info in results['information']:
            print(f"[INFO][{info['type']}][{info['line_num']}] {info['line_content']}")

    print(f"{colors('='*80, 'green')}")
    print(f"{colors('[*] 전체 결과 출력', 'green')}")
    print(f"form {len(results['forms'])}개 \ninput {len(results['inputs'])}개 \nscript {len(results['scripts'])}개")
    print(f"{colors('='*80, 'green')}")

def banner(text, width=80):
    """박스 배너 출력 (한글 너비 자동 계산)"""
    import unicodedata
    
    # 실제 표시 너비 계산
    text_width = sum(2 if unicodedata.east_asian_width(c) in ('F', 'W') else 1 for c in text)
    
    padding_total = width - 2 - text_width
    padding_left = padding_total // 2
    padding_right = padding_total - padding_left
    
    top = "╔" + "═" * (width - 2) + "╗"
    mid = "║" + " " * padding_left + text + " " * padding_right + "║"
    bot = "╚" + "═" * (width - 2) + "╝"
    
    return f"{col.CYAN}{top}\n{mid}\n{bot}{col.END}"

def section(text, width=80):
    """섹션 구분선 출력"""
    import unicodedata
    
    text_width = sum(2 if unicodedata.east_asian_width(c) in ('F', 'W') else 1 for c in text)
    
    padding_total = width - 2 - text_width  # 양쪽 공백 포함
    padding_left = padding_total // 2
    padding_right = padding_total - padding_left
    
    return f"{col.YELLOW}{'─' * padding_left} {text} {'─' * padding_right}{col.END}"
