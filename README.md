# 전체 구조
```
scanners/
├── core/
│   └── target.py           # URL Wordlist 설정
│
├── extract                 # 정보 추출 디렉터리
│   ├── ext_form.py         # 태그 추출 메인 코드
│   ├── ext_form_test.py    # 태그 추출 테스트 코드
│   └── ext_save.py         # 추출한 정보 저장
│
├── utils/
│
└── module/
    ├── console_module.py   # CLI에 출력할 때 사용하는 모듈
    ├── function.py         # 함수로 변환해서 편리하게 사용
    ├── headers_module.py   # Request 모듈
    └── imports.py          # Python Library 모듈

```
