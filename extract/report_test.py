from module.imports import *

def report_test(results, filename="report.html"):
    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Web Scanner Report</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #eee;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        h1 {{
            text-align: center;
            margin-bottom: 30px;
            color: #00d4ff;
            text-shadow: 0 0 10px rgba(0, 212, 255, 0.5);
        }}
        .stats {{
            display: flex;
            gap: 20px;
            margin-bottom: 30px;
            justify-content: center;
        }}
        .stat-card {{
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 20px 40px;
            text-align: center;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }}
        .stat-card h2 {{
            font-size: 2.5em;
            margin-bottom: 5px;
        }}
        .stat-card.forms h2 {{ color: #ff6b6b; }}
        .stat-card.inputs h2 {{ color: #4ecdc4; }}
        .stat-card.scripts h2 {{ color: #ffe66d; }}
        .section {{
            background: rgba(255, 255, 255, 0.05);
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 20px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }}
        .section-title {{
            font-size: 1.3em;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid rgba(255, 255, 255, 0.2);
        }}
        .section-title.forms {{ color: #ff6b6b; }}
        .section-title.inputs {{ color: #4ecdc4; }}
        .section-title.scripts {{ color: #ffe66d; }}
        .item {{
            background: rgba(0, 0, 0, 0.3);
            border-radius: 8px;
            padding: 12px 15px;
            margin-bottom: 10px;
            font-family: 'Consolas', monospace;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .method {{
            padding: 4px 10px;
            border-radius: 5px;
            font-weight: bold;
            font-size: 0.85em;
        }}
        .method.POST {{ background: #ff6b6b; color: #000; }}
        .method.GET {{ background: #4ecdc4; color: #000; }}
        .method.SCRIPT {{ background: #ffe66d; color: #000; }}
        .status {{
            padding: 4px 10px;
            border-radius: 5px;
            font-size: 0.85em;
        }}
        .status.success {{ background: #2ecc71; color: #000; }}
        .status.error {{ background: #e74c3c; color: #fff; }}
        .url {{
            flex: 1;
            word-break: break-all;
            color: #aaa;
        }}
        .sub-item {{
            margin-left: 30px;
            padding: 8px 12px;
            background: rgba(255, 255, 255, 0.05);
            border-left: 3px solid #666;
            font-size: 0.9em;
            color: #888;
        }}
        .timestamp {{
            text-align: center;
            color: #666;
            margin-top: 30px;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 Web Scanner Report</h1>
        
        <div class="stats">
            <div class="stat-card forms">
                <h2>{len(results['forms'])}</h2>
                <p>Forms</p>
            </div>
            <div class="stat-card inputs">
                <h2>{len(results['inputs'])}</h2>
                <p>Inputs</p>
            </div>
            <div class="stat-card scripts">
                <h2>{len(results['scripts'])}</h2>
                <p>Scripts</p>
            </div>
        </div>
"""
    
    # Forms 섹션
    if results['forms']:
        html += """
        <div class="section">
            <div class="section-title forms">📝 Forms</div>
"""
        for form in results['forms']:
            status_class = "success" if form['status_code'] == 200 else "error"
            html += f"""
            <div class="item">
                <span class="method {form['method']}">{form['method']}</span>
                <span class="url">{form['req_url']}</span>
                <span class="status {status_class}">{form['status_code']}</span>
            </div>
"""
            for inp in form.get('inputs', []):
                html += f"""
            <div class="sub-item">
                └ &lt;{inp['tag']} name="{inp['name']}" id="{inp['id']}" value="{inp['value']}"&gt;
            </div>
"""
        html += "        </div>"
    
    # Inputs 섹션
    if results['inputs']:
        html += """
        <div class="section">
            <div class="section-title inputs">📥 Inputs</div>
"""
        for inp in results['inputs']:
            status_class = "success" if inp.get('status_code') == 200 else "error"
            html += f"""
            <div class="item">
                <span class="method GET">GET</span>
                <span class="url">{inp['req_url']}</span>
                <span class="status {status_class}">{inp.get('status_code', 'N/A')}</span>
            </div>
"""
        html += "        </div>"
    
    # Scripts 섹션
    if results['scripts']:
        html += """
        <div class="section">
            <div class="section-title scripts">📜 Scripts</div>
"""
        for script in results['scripts']:
            status_class = "success" if script.get('status_code') == 200 else "error"
            html += f"""
            <div class="item">
                <span class="method SCRIPT">SCRIPT</span>
                <span class="url">{script['req_url']}{script['src']}</span>
                <span class="status {status_class}">{script.get('status_code', 'N/A')}</span>
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
    
    print(f"[*] ProtoType HTML 리포트 저장 완료: {filename}")