from module.imports import *

def ext_save(result):
    print(f"\033[92m[DEBUG] result: {result}\033[0m")

    result_str = str(result)
    with open("ext_form.md", "w", encoding="utf-8") as f:
        f.write(result_str)