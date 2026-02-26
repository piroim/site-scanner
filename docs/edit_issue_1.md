## 수정 #001: 스캔된 사이트 전체 해제 불가

### 발생일
2026-01-24

### 증상
- 대시보드 좌측 "스캔된 사이트" 목록에서 최소 1개 사이트는 항상 선택되어야 함
- 모든 사이트를 해제하려고 해도 마지막 1개는 해제되지 않음

### 영향받은 파일
- `templates/dashboard.html` - `toggleSite()` 함수

### 원인
사이트 선택 해제 시 최소 1개 유지 조건이 있었음

```javascript
// 문제 코드 (dashboard.html:344-353)
function toggleSite(siteId) {
    const idx = state.selectedSites.indexOf(siteId);
    if (idx > -1) {
        if (state.selectedSites.length > 1) {  // ← 이 조건이 문제
            state.selectedSites.splice(idx, 1);
        }
    } else {
        state.selectedSites.push(siteId);
    }
    renderAll();
}
```

### 해결 방법
```javascript
// 수정된 코드
function toggleSite(siteId) {
    const idx = state.selectedSites.indexOf(siteId);
    if (idx > -1) {
        // 전부 해제 가능하도록 조건 제거
        state.selectedSites.splice(idx, 1);
    } else {
        state.selectedSites.push(siteId);
    }
    renderAll();
}
```

### 확인 방법
1. 여러 사이트 스캔 후 대시보드 확인
2. 좌측 사이트 목록에서 모든 사이트 클릭하여 해제
3. 모든 사이트가 해제되고 결과 테이블이 비어있으면 정상