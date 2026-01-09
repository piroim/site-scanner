from module.imports import *
from html import escape
from pathlib import Path

def report_test(results, filename="report.html"):
    # CSS 파일 경로 (report.py 기준)
    css_path = Path(__file__).parent / "style.css"
    
    # CSS 파일 읽기
    with open(css_path, "r", encoding="utf-8") as f:
        css_content = f.read()
    
    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Web Scanner Report</title>
    <style>
{css_content}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 Web Scanner Report</h1>
        
        <div class="stats">
            <div class="stat-card" data-text-color="red">
                <h2>{len(results.get('forms', []))}</h2>
                <p>Forms</p>
            </div>
            <div class="stat-card" data-text-color="green">
                <h2>{len(results.get('inputs', []))}</h2>
                <p>Inputs</p>
            </div>
            <div class="stat-card" data-text-color="yellow">
                <h2>{len(results.get('scripts', []))}</h2>
                <p>Scripts</p>
            </div>
            <div class="stat-card" data-text-color="blue">
                <h2>{len(results.get('information', []))}</h2>
                <p>Information</p>
            </div>
        </div>
"""
    
    # Forms 섹션
    if 'forms' in results:
        html += """
        <div class="section">
            <div class="section-title" data-text-color="red">📝 Forms</div>
"""
        for form in results['forms']:
            status_class = "success" if form['status_code'] == 200 else "error"
            method_color = "red" if form['method'] == "POST" else "green"
            html += f"""
            <div class="item">
                <span class="badge" data-color="{method_color}">{escape(form['method'])}</span>
                <span class="content">{escape(form['req_url'])}</span>
                <span class="badge status {status_class}">{form['status_code']}</span>
            </div>
"""
            for inp in form.get('inputs', []):
                html += f"""
            <div class="sub-item">
                └ &lt;{escape(inp['tag'])} name="{escape(inp['name'])}" id="{escape(inp['id'])}" value="{escape(inp['value'])}"&gt;
            </div>
"""
        html += "        </div>"
    
    # Inputs 섹션
    if 'inputs' in results:
        html += """
        <div class="section">
            <div class="section-title" data-text-color="green">📥 Inputs</div>
"""
        for inp in results['inputs']:
            status_class = "success" if inp.get('status_code') == 200 else "error"
            html += f"""
            <div class="item">
                <span class="badge" data-color="green">GET</span>
                <span class="content">{escape(inp['req_url'])}</span>
                <span class="badge status {status_class}">{inp.get('status_code', 'N/A')}</span>
            </div>
"""
        html += "        </div>"
    
    # Scripts 섹션
    if 'scripts' in results:
        html += """
        <div class="section">
            <div class="section-title" data-text-color="yellow">📜 Scripts</div>
"""
        for script in results['scripts']:
            status_class = "success" if script.get('status_code') == 200 else "error"
            src = script['src'].lower()
            if src.startswith(('http://', 'https://', '//')):
                full_url = src
            else:
                full_url = f"{script['req_url']}{src}"
            html += f"""
            <div class="item">
                <span class="badge" data-color="yellow">SCRIPT</span>
                <span class="content">{escape(full_url)}</span>
                <span class="badge status {status_class}">{script.get('status_code', 'N/A')}</span>
            </div>
"""
        html += "        </div>"
    
    # Information 섹션
    if 'information' in results:
        html += """
        <div class="section">
            <div class="section-title" data-text-color="blue">📝 Information</div>
"""
        for info in results['information']:
            html += f"""
            <div class="item">
                <span class="badge" data-color="blue">{escape(info['type'])}</span>
                <span class="badge" data-color="green">Line {escape(str(info['line_num']))}</span>
                <span class="content">{escape(info['line_content'])}</span>
            </div>
"""
        html += "        </div>"

    # 타임스탬프
    from datetime import datetime
    html += f"""
        <div class="timestamp">
            Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
    </div>
</body>
</html>
"""
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"[*] HTML 리포트 저장 완료: {filename}")