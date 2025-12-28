# 📋 [site_scanner] Development Log

---

## [2025.12.28]

### ✅ 완료
- script 태그 추출 시 google 도메인 필터링 추가
- HTML 리포트 대시보드 스타일로 구현 (이거는 나중에 추가 설정 필요)
- save_test 함수 리팩토링 (with open 중복 제거)
- script 태그 src 기반으로 추출하는 함수 구현

### 🔧 진행중
- script 태그 내, 특정 문자열 추출 기능 구현중(parser_infomation 함수)
    - 정보 추출을 어떻게 표현할지 구상해야 할 필요 있음 
- script 태그 내, AJAX 부분의 API 추출 기능 구현 예정
- 결과 출력 부분 상세하게 변경 필요
- 각 태그에 맞춰서 어떤 데이터 출력되는지 CLI 화면에 구현 필요

### 📌 TODO


### 💡 메모
- script 태그의 src 외에 ajax 또는 단순 script 태그 안의 데이터 추출 함수 구현 추가 필요
- .js 파일은 별도의 항목으로 구분해야 할 것 같음 SCIPRT 태그 또는 JS 태그로
---