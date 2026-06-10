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
    """Converts standard Markdown formatting to styled, professional HTML."""
    lines = markdown_text.splitlines()
    html_lines = []
    in_list = False
    
    for line in lines:
        line = line.strip()
        if not line:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append("<br/>")
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
    
    # Wrap in a gorgeous CSS document template
    template = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>AI Career Assistant Export</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: #333333;
            max-width: 800px;
            margin: 40px auto;
            padding: 0 20px;
            background-color: #ffffff;
        }}
        h1 {{
            color: #0f172a;
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 12px;
            font-size: 28px;
            font-weight: 700;
        }}
        h2 {{
            color: #1e293b;
            font-size: 20px;
            font-weight: 600;
            margin-top: 30px;
            border-bottom: 1px solid #f1f5f9;
            padding-bottom: 6px;
        }}
        h3 {{
            color: #475569;
            font-size: 16px;
            font-weight: 600;
            margin-top: 20px;
        }}
        p, li {{
            font-size: 14.5px;
            color: #334155;
        }}
        ul {{
            padding-left: 20px;
        }}
        li {{
            margin-bottom: 8px;
        }}
        a {{
            color: #2563eb;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        hr {{
            border: 0;
            height: 1px;
            background: #e2e8f0;
            margin: 30px 0;
        }}
        strong {{
            color: #0f172a;
            font-weight: 600;
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
    """Converts standard Markdown formatting to a cleanly formatted, print-ready PDF using fpdf2."""
    pdf = PDF()
    pdf.add_page()
    pdf.set_margins(20, 20, 20)
    pdf.set_auto_page_break(auto=True, margin=15)
    
    lines = markdown_text.splitlines()
    for line in lines:
        line = line.strip()
        if not line:
            pdf.ln(3)
            continue
            
        # Title Header
        if line.startswith("# "):
            pdf.set_font("helvetica", "B", 18)
            pdf.set_text_color(15, 23, 42) # Slate-900 (#0f172a)
            pdf.multi_cell(0, 9, line[2:])
            pdf.ln(1)
        # H2 Header
        elif line.startswith("## "):
            pdf.set_font("helvetica", "B", 13)
            pdf.set_text_color(30, 41, 59) # Slate-800 (#1e293b)
            pdf.ln(3)
            pdf.multi_cell(0, 7, line[3:])
            pdf.ln(1)
        # H3 Header
        elif line.startswith("### "):
            pdf.set_font("helvetica", "B", 11)
            pdf.set_text_color(71, 85, 105) # Slate-600 (#475569)
            pdf.multi_cell(0, 6, line[4:])
            pdf.ln(1)
        # Horizontal Rule
        elif line == "---":
            pdf.set_draw_color(226, 232, 240) # Slate-200 (#e2e8f0)
            x = pdf.get_x()
            y = pdf.get_y()
            pdf.line(x, y + 2, x + 170, y + 2)
            pdf.ln(5)
        # Bullet Points
        elif line.startswith("* ") or line.startswith("- "):
            pdf.set_font("helvetica", "", 10)
            pdf.set_text_color(51, 65, 85) # Slate-700 (#334155)
            
            # Clean bold text formatting and links for PDF output
            content = line[2:]
            content = content.replace("**", "")
            content = re.sub(r'\[(.*?)\]\((.*?)\)', r'\1', content)
            
            bullet_char = chr(149) # Standard bullet symbol
            pdf.set_x(25)
            pdf.multi_cell(0, 5, f"{bullet_char}  {content}")
        # Standard Paragraph
        else:
            pdf.set_font("helvetica", "", 10)
            pdf.set_text_color(51, 65, 85)
            
            content = line.replace("**", "")
            content = re.sub(r'\[(.*?)\]\((.*?)\)', r'\1', content)
            
            pdf.set_x(20)
            pdf.multi_cell(0, 5, content)
            
    pdf.output(output_path)
