import sys, unicodedata

"""
    컬러 클래스 생성
"""
class col:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    END = '\033[0m'
    BOLD = '\033[1m'

"""
    색상 컬러를 함수로 사용
"""
def colors(text, style):
    code = getattr(col, style.upper(), '')
    return f"{code}{text}{col.END}"

"""
    printer.overwrite()로 사용하며, 출력 결과 삭제할 때 사용
"""
class ConsolePrinter:
    def overwrite(self, msg):
        sys.stdout.write('\r\033[K' + msg)
        sys.stdout.flush()
    
    def println(self, msg):
        print(msg)
printer = ConsolePrinter()


"""
    배너 출력
"""
def get_display_width(text: str) -> int:
    """문자열의 실제 표시 너비 계산"""
    width = 0
    for char in text:
        # East Asian Width 속성 확인
        if unicodedata.east_asian_width(char) in ('F', 'W'):
            width += 2  # 전각 문자 (한글, 한자 등)
        else:
            width += 1  # 반각 문자 (영문, 숫자 등)
    return width

def banner(text, width=80):
    text_width = get_display_width(text)
    padding_total = width - 2 - text_width  # 양쪽 ║ 제외
    padding_left = padding_total // 2
    padding_right = padding_total - padding_left
    
    top = "╔" + "═" * (width - 2) + "╗"
    mid = "║" + " " * padding_left + text + " " * padding_right + "║"
    bot = "╚" + "═" * (width - 2) + "╝"
    
    return f"{col.CYAN}{top}\n{mid}\n{bot}{col.END}"