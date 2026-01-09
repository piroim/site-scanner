# 전체 구조
```markdown
site-scanner/
│  DEVLOG.md                #[기록] 개발로그
│  main.py                  #[메인] 전체 코드를 실행하는 메인파일
│  README.md
│  report.html              #[결과] 결과 파일(나중에 대시보드로 변경)
│  
├─extract
│  │  a_func.py             #[추출] a href 태그 추출
│  │  debug_test.py         #[테스트] 테스트 용도
│  │  ext_form_test.py      #[메인] 추출 및 저장 함수 실행
│  │  ext_result.py         #[출력] 추출한 결과 값을 CLI에 출력
│  │  form_func.py          #[추출] form 태그 추출
│  │  infor_func.py         #[추출] 패턴 기반 정보 추출
│  │  input_func.py         #[추출] 패턴 기반의 정보 추출
│  │  report_test.py        #[저장] 추출결과를 HTML에 저장(추후 파일명 변경) 
│  │  script_func.py        #[추출] script 태그 추출
│  │  session_test.py       #[테스트] 세션 테스트 파일
│  └─ style.css
│
├─module
│  │  console_module.py     #[함수] CLI 화면에 출력할 때 고정적으로 사용할 함수(색상, 배너)
│  │  function.py           #[함수] 사용할 함수 지정(현재는 사용하지 않음)
│  │  headers_module.py     #[공통] Request 모듈의 헤더 정의
│  │  imports.py            #[공통] Library, Module 정의
│  └─ patterns.py           #[미사용] 패턴을 별도로 사용하려 했으나, 아직은 미사용
│
└─save
```
