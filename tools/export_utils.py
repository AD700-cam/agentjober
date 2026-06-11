import re
import math
from fpdf import FPDF

class PDF(FPDF):
    def footer(self):
        """Draw page numbers at the bottom of each page."""
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def markdown_to_html(markdown_text: str) -> str:
    """Converts standard Markdown formatting to styled, professional, print-friendly HTML."""
    lines = markdown_text.splitlines()
    html_lines = []
    in_list = False
    
    for line in lines:
        line = line.strip()
        if not line:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            continue
            
        # Headers
        if line.startswith("# "):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<h1>{line[2:]}</h1>")
        elif line.startswith("## "):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<h2>{line[3:]}</h2>")
        elif line.startswith("### "):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<h3>{line[4:]}</h3>")
        # Horizontal rule
        elif line == "---":
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append("<hr/>")
        # Bullet list items
        elif line.startswith("* ") or line.startswith("- "):
            if not in_list:
                html_lines.append("<ul>")
                in_list = True
            content = line[2:]
            html_lines.append(f"<li>{content}</li>")
        else:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<p>{line}</p>")
            
    if in_list:
        html_lines.append("</ul>")
        
    html_content = "\n".join(html_lines)
    
    # Render inline bold styling (**text**)
    html_content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html_content)
    
    # Render inline links ([text](url))
    html_content = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2" target="_blank">\1</a>', html_content)
    
    # Wrap in a gorgeous print-ready CSS template (optimized for single-page or two-page resumes)
    template = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>ATS Optimized Resume</title>
    <style>
        @page {{
            size: A4;
            margin: 0;
        }}
        body {{
            font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
            line-height: 1.4;
            color: #1e293b;
            margin: 0;
            padding: 0;
            background-color: #ffffff;
            -webkit-print-color-adjust: exact;
        }}
        h1 {{
            color: #0f172a;
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 6px;
            font-size: 24px;
            font-weight: 700;
            margin-top: 15px;
            margin-bottom: 8px;
            text-align: center;
        }}
        h2 {{
            color: #0f172a;
            font-size: 14px;
            font-weight: 700;
            margin-top: 18px;
            margin-bottom: 6px;
            border-bottom: 1px solid #94a3b8;
            padding-bottom: 2px;
            text-transform: uppercase;
            letter-spacing: 0.8px;
        }}
        h3 {{
            color: #334155;
            font-size: 12.5px;
            font-weight: 600;
            margin-top: 8px;
            margin-bottom: 2px;
        }}
        p, li {{
            font-size: 11px;
            color: #334155;
            margin-top: 0;
            margin-bottom: 4px;
        }}
        ul {{
            padding-left: 18px;
            margin-top: 0;
            margin-bottom: 6px;
        }}
        li {{
            margin-bottom: 2px;
        }}
        a {{
            color: #2563eb;
            text-decoration: none;
        }}
        hr {{
            border: 0;
            height: 1px;
            background: #cbd5e1;
            margin: 15px 0;
        }}
        strong {{
            color: #0f172a;
            font-weight: 600;
        }}
        /* Page break helper */
        .page-break {{
            page-break-before: always;
        }}
    </style>
</head>
<body>
    {html_content}
</body>
</html>
"""
    return template

def markdown_to_pdf(markdown_text: str, output_path: str):
    """Converts standard Markdown formatting to a cleanly styled, print-ready PDF using Playwright page.pdf."""
    html_content = markdown_to_html(markdown_text)
    
    import tempfile
    import os
    from playwright.sync_api import sync_playwright
    
    # Write to a temporary HTML file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w", encoding="utf-8") as tmp:
        tmp.write(html_content)
        tmp_path = tmp.name
        
    try:
        with sync_playwright() as p:
            # Use headless browser for quick rendering
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Navigate to temporary HTML page
            file_url = "file:///" + os.path.abspath(tmp_path).replace("\\", "/")
            page.goto(file_url)
            page.wait_for_load_state("networkidle")
            
            # Print page as PDF with 0.6 inch margins matching target dimensions
            page.pdf(
                path=output_path,
                format="A4",
                print_background=True,
                margin={"top": "0.6in", "bottom": "0.6in", "left": "0.6in", "right": "0.6in"}
            )
            browser.close()
    finally:
        # Delete the temporary file
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass
