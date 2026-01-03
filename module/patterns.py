from module.imports import *

""" Script 태그 내에서 AJAX URL 추출 함수 """
def get_ajax_urls(self, script_content):
    ajax_urls = []
    patterns = [
        r'url\s*:\s*"([^"]+)"',
        r'type\s*:\s*"([^"]+)"'
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, script_content)
        for match in matches:
            ajax_urls.append(match)
    # print(f"ajax_urls: {ajax_urls}")
    return ajax_urls