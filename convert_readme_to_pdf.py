"""
Script para converter README.md em PDF
Funciona no Windows sem dependências nativas complexas
"""

import markdown
from pathlib import Path
import sys

def markdown_to_pdf_method1(md_file_path, pdf_file_path=None):
    """
    Método 1: Usando xhtml2pdf (puro Python, funciona no Windows)
    """
    try:
        from xhtml2pdf import pisa
        from io import BytesIO
        
        md_path = Path(md_file_path)
        if not md_path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {md_file_path}")
        
        with open(md_path, 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        # Converte markdown para HTML
        html_content = markdown.markdown(
            md_content,
            extensions=['extra', 'codehilite', 'tables', 'fenced_code']
        )
        
        # Processa imagens para resolver caminhos relativos
        import re
        from urllib.parse import urlparse
        
        def process_image_paths(html):
            """Converte caminhos relativos de imagens para absolutos"""
            def replace_img(match):
                alt = match.group(1)
                src = match.group(2)
                
                # Se não for URL absoluta, resolve caminho relativo
                parsed = urlparse(src)
                if not parsed.scheme and not parsed.netloc:
                    # Caminho relativo - converte para absoluto
                    img_path = md_path.parent / src
                    if img_path.exists():
                        return f'<img src="{img_path.absolute()}" alt="{alt}" style="max-width: 100%; height: auto;" />'
                return match.group(0)
            
            # Substitui tags img
            html = re.sub(r'<img\s+src=["\']([^"\']+)["\'][^>]*alt=["\']([^"\']+)["\'][^>]*>', 
                         replace_img, html)
            # Também processa markdown images que podem não ter sido convertidas
            html = re.sub(r'<img\s+src=["\']([^"\']+)["\'][^>]*>', 
                         lambda m: f'<img src="{str((md_path.parent / m.group(1)).absolute())}" style="max-width: 100%; height: auto;" />' 
                         if not urlparse(m.group(1)).scheme else m.group(0), html)
            return html
        
        html_content = process_image_paths(html_content)
        
        # CSS para PDF
        css_style = """
        <style>
            @page {
                size: A4;
                margin: 2cm;
            }
            body {
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
            }
            h1 {
                color: #2c3e50;
                border-bottom: 3px solid #3498db;
                padding-bottom: 10px;
                margin-top: 30px;
            }
            h2 {
                color: #34495e;
                border-bottom: 2px solid #95a5a6;
                padding-bottom: 5px;
                margin-top: 25px;
            }
            h3 {
                color: #7f8c8d;
                margin-top: 20px;
            }
            h4 {
                color: #95a5a6;
                margin-top: 15px;
            }
            code {
                background-color: #f4f4f4;
                padding: 2px 5px;
                font-family: 'Courier New', monospace;
            }
            pre {
                background-color: #f4f4f4;
                padding: 15px;
                border-left: 4px solid #3498db;
            }
            table {
                border-collapse: collapse;
                width: 100%;
                margin: 20px 0;
            }
            th, td {
                border: 1px solid #ddd;
                padding: 12px;
                text-align: left;
            }
            th {
                background-color: #3498db;
                color: white;
                font-weight: bold;
            }
            tr:nth-child(even) {
                background-color: #f2f2f2;
            }
            ul, ol {
                margin: 15px 0;
                padding-left: 30px;
            }
            blockquote {
                border-left: 4px solid #3498db;
                margin: 20px 0;
                padding-left: 20px;
                color: #7f8c8d;
            }
            img {
                max-width: 100% !important;
                height: auto !important;
                width: auto !important;
                max-height: 600px !important;
                display: block;
                margin: 20px auto;
                page-break-inside: avoid;
                break-inside: avoid;
            }
            p img, div img {
                max-width: 100% !important;
                height: auto !important;
                page-break-inside: avoid;
            }
            figure {
                page-break-inside: avoid;
                break-inside: avoid;
                margin: 20px 0;
            }
        </style>
        """
        
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Agente SCR 3040 - Documentação</title>
            {css_style}
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """
        
        if pdf_file_path is None:
            pdf_file_path = md_path.with_suffix('.pdf')
        else:
            pdf_file_path = Path(pdf_file_path)
        
        print(f"🔄 Convertendo {md_path.name} para PDF (método xhtml2pdf)...")
        
        with open(pdf_file_path, 'wb') as pdf_file:
            pisa.CreatePDF(full_html, dest=pdf_file)
        
        print(f"✅ PDF criado com sucesso: {pdf_file_path}")
        return pdf_file_path
        
    except ImportError:
        print("❌ xhtml2pdf não instalado. Tentando método alternativo...")
        return None

def markdown_to_pdf_method2(md_file_path, pdf_file_path=None):
    """
    Método 2: Usando reportlab (puro Python)
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_LEFT, TA_CENTER
        from PIL import Image as PILImage
        import re
        
        md_path = Path(md_file_path)
        if not md_path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {md_file_path}")
        
        with open(md_path, 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        if pdf_file_path is None:
            pdf_file_path = md_path.with_suffix('.pdf')
        else:
            pdf_file_path = Path(pdf_file_path)
        
        print(f"🔄 Convertendo {md_path.name} para PDF (método reportlab)...")
        
        # Cria o documento PDF
        doc = SimpleDocTemplate(str(pdf_file_path), pagesize=A4,
                              rightMargin=2*cm, leftMargin=2*cm,
                              topMargin=2*cm, bottomMargin=2*cm)
        
        # Estilos
        styles = getSampleStyleSheet()
        story = []
        
        # Estilos customizados
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=12,
        )
        
        heading2_style = ParagraphStyle(
            'CustomHeading2',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#34495e'),
            spaceAfter=10,
        )
        
        # Processa o markdown linha por linha
        lines = md_content.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            if not line:
                story.append(Spacer(1, 6))
            elif line.startswith('# '):
                # Título H1
                text = line[2:].strip()
                story.append(Paragraph(text, title_style))
                story.append(Spacer(1, 12))
            elif line.startswith('## '):
                # Título H2
                text = line[3:].strip()
                story.append(Paragraph(text, heading2_style))
                story.append(Spacer(1, 10))
            elif line.startswith('### '):
                # Título H3
                text = line[4:].strip()
                story.append(Paragraph(text, styles['Heading3']))
                story.append(Spacer(1, 8))
            elif line.startswith('#### '):
                # Título H4
                text = line[5:].strip()
                story.append(Paragraph(text, styles['Heading4']))
                story.append(Spacer(1, 6))
            elif re.match(r'^!\[.*?\]\(.*?\)$', line):
                # Imagem markdown: ![alt](path)
                match = re.match(r'^!\[.*?\]\((.*?)\)$', line)
                if match:
                    img_path = match.group(1)
                    # Resolve caminho relativo
                    if not Path(img_path).is_absolute():
                        img_path = md_path.parent / img_path
                    else:
                        img_path = Path(img_path)
                    
                    if img_path.exists():
                        try:
                            # Abre a imagem para obter dimensões
                            pil_img = PILImage.open(img_path)
                            img_width, img_height = pil_img.size
                            
                            # Calcula largura disponível (A4 - margens)
                            available_width = A4[0] - 4*cm  # 2cm de cada lado
                            available_height = A4[1] - 4*cm  # 2cm de cada lado
                            
                            # Calcula escala mantendo proporção
                            width_ratio = available_width / img_width
                            height_ratio = available_height / img_height
                            scale = min(width_ratio, height_ratio, 1.0)  # Não aumenta, só reduz
                            
                            # Dimensões finais
                            final_width = img_width * scale
                            final_height = img_height * scale
                            
                            # Adiciona imagem ao PDF
                            story.append(Spacer(1, 12))
                            img = Image(str(img_path), width=final_width, height=final_height)
                            story.append(img)
                            story.append(Spacer(1, 12))
                        except Exception as e:
                            print(f"⚠️  Erro ao processar imagem {img_path}: {e}")
                            story.append(Paragraph(f"[Imagem: {img_path.name}]", styles['Normal']))
                    else:
                        story.append(Paragraph(f"[Imagem não encontrada: {img_path}]", styles['Normal']))
            elif line.startswith('- ') or line.startswith('* '):
                # Lista
                text = line[2:].strip()
                # Remove markdown formatting básico
                text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
                text = re.sub(r'`(.*?)`', r'<font name="Courier">\1</font>', text)
                story.append(Paragraph(f"• {text}", styles['Normal']))
            elif line.startswith('|'):
                # Tabela (processa múltiplas linhas)
                table_data = []
                while i < len(lines) and lines[i].strip().startswith('|'):
                    row = [cell.strip() for cell in lines[i].strip().split('|')[1:-1]]
                    if row and not all(c.startswith('-') for c in row):  # Ignora linha de separação
                        table_data.append(row)
                    i += 1
                i -= 1  # Ajusta para não pular linha
                
                if table_data:
                    table = Table(table_data)
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 10),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                    ]))
                    story.append(table)
                    story.append(Spacer(1, 12))
            else:
                # Texto normal
                # Remove markdown formatting básico
                text = line
                text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
                text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
                text = re.sub(r'`(.*?)`', r'<font name="Courier">\1</font>', text)
                text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)  # Remove links, mantém texto
                
                if text.strip():
                    story.append(Paragraph(text, styles['Normal']))
                    story.append(Spacer(1, 6))
            
            i += 1
        
        # Gera o PDF
        doc.build(story)
        print(f"✅ PDF criado com sucesso: {pdf_file_path}")
        return pdf_file_path
        
    except ImportError:
        print("❌ reportlab não instalado. Tentando método alternativo...")
        return None

def markdown_to_pdf_simple(md_file_path, pdf_file_path=None):
    """
    Método 3: Usando markdown + HTML e salvando como HTML (mais simples)
    Depois pode ser convertido manualmente para PDF pelo navegador
    """
    md_path = Path(md_file_path)
    if not md_path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {md_file_path}")
    
    with open(md_path, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # Converte markdown para HTML
    html_content = markdown.markdown(
        md_content,
        extensions=['extra', 'codehilite', 'tables', 'fenced_code']
    )
    
    css_style = """
    <style>
        @media print {
            @page {
                size: A4;
                margin: 2cm;
            }
        }
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        h1 {
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }
        h2 {
            color: #34495e;
            border-bottom: 2px solid #95a5a6;
            padding-bottom: 5px;
        }
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 12px;
        }
        th {
            background-color: #3498db;
            color: white;
        }
        img {
            max-width: 100% !important;
            height: auto !important;
            width: auto !important;
            max-height: 600px !important;
            display: block;
            margin: 20px auto;
            page-break-inside: avoid;
            break-inside: avoid;
        }
        p img, div img {
            max-width: 100% !important;
            height: auto !important;
            page-break-inside: avoid;
        }
        figure {
            page-break-inside: avoid;
            break-inside: avoid;
            margin: 20px 0;
        }
    </style>
    """
    
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Agente SCR 3040 - Documentação</title>
        {css_style}
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """
    
    if pdf_file_path is None:
        html_path = md_path.with_suffix('.html')
    else:
        html_path = Path(str(pdf_file_path).replace('.pdf', '.html'))
    
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(full_html)
    
    print(f"✅ HTML criado: {html_path}")
    print("💡 Abra este arquivo no navegador e use Ctrl+P para salvar como PDF")
    return html_path

def main():
    """Função principal que tenta diferentes métodos"""
    readme_path = Path("README.md")
    
    if len(sys.argv) > 1:
        readme_path = Path(sys.argv[1])
    
    if len(sys.argv) > 2:
        output_path = Path(sys.argv[2])
    else:
        output_path = None
    
    print("=" * 60)
    print("📄 Conversor de Markdown para PDF")
    print("=" * 60)
    print()
    
    # Tenta método 1: xhtml2pdf
    result = markdown_to_pdf_method1(readme_path, output_path)
    if result:
        return
    
    # Tenta método 2: reportlab
    result = markdown_to_pdf_method2(readme_path, output_path)
    if result:
        return
    
    # Método 3: HTML (sempre funciona)
    print("\n⚠️  Nenhuma biblioteca PDF encontrada. Gerando HTML...")
    print("💡 Instale uma das opções abaixo para gerar PDF diretamente:\n")
    print("   pip install xhtml2pdf")
    print("   ou")
    print("   pip install reportlab")
    print()
    
    html_path = markdown_to_pdf_simple(readme_path, output_path)
    print(f"\n📄 Arquivo HTML gerado: {html_path.absolute()}")
    print("   Abra no navegador e pressione Ctrl+P para salvar como PDF")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Erro ao converter: {e}")
        import traceback
        traceback.print_exc()
