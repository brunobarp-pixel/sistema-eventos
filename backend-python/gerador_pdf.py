from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
import os

def gerar_certificado_pdf(dados_certificado, output_path='certificados_pdf'):#rever isso aqui
    """
    Gera um certificado em PDF
    
    Args:
        dados_certificado: dict com os dados do certificado
            - nome_participante: str
            - evento_titulo: str
            - evento_descricao: str
            - data_inicio: str (formato: YYYY-MM-DD)
            - data_fim: str (formato: YYYY-MM-DD)
            - local: str
            - carga_horaria: int (opcional)
            - codigo_validacao: str
            - data_emissao: str
        output_path: caminho da pasta para salvar o PDF
    
    Returns:
        str: caminho do arquivo PDF gerado
    """
    
    try:
        print(f"Gerando PDF com dados: {dados_certificado}")
        
        campos_obrigatorios = ['nome_participante', 'evento_titulo', 'codigo_validacao', 'data_inicio', 'data_fim', 'local', 'data_emissao']
        for campo in campos_obrigatorios:
            if not dados_certificado.get(campo):
                raise ValueError(f"Campo obrigatório '{campo}' não fornecido")
        
        if not os.path.exists(output_path):
            os.makedirs(output_path)
            print(f"Pasta criada: {output_path}")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        nome_arquivo = f"certificado_{dados_certificado['codigo_validacao'][:8]}_{timestamp}.pdf"
        caminho_completo = os.path.join(output_path, nome_arquivo)
        
        print(f"Criando arquivo: {caminho_completo}")
    
    pdf = canvas.Canvas(caminho_completo, pagesize=landscape(A4))
    width, height = landscape(A4)
    
    
    pdf.setStrokeColor(HexColor('#667eea'))
    pdf.setLineWidth(3)
    pdf.rect(1*cm, 1*cm, width - 2*cm, height - 2*cm, stroke=1, fill=0)
    
    pdf.setStrokeColor(HexColor('#764ba2'))
    pdf.setLineWidth(1)
    pdf.rect(1.3*cm, 1.3*cm, width - 2.6*cm, height - 2.6*cm, stroke=1, fill=0)
    
    pdf.setFont("Helvetica-Bold", 40)
    pdf.setFillColor(HexColor("#3256f8"))
    pdf.drawCentredString(width/2, height - 4*cm, "CERTIFICADO")
    
    pdf.setFont("Helvetica", 16)
    pdf.setFillColor(HexColor('#333333'))
    pdf.drawCentredString(width/2, height - 5*cm, "Certificamos que")
    
    pdf.setFont("Helvetica-Bold", 28)
    pdf.setFillColor(HexColor('#000000'))
    pdf.drawCentredString(width/2, height - 7*cm, dados_certificado['nome_participante'].upper())
    
    pdf.setStrokeColor(HexColor("#3256f8"))
    pdf.setLineWidth(2)
    nome_width = pdf.stringWidth(dados_certificado['nome_participante'].upper(), "Helvetica-Bold", 28)
    pdf.line(width/2 - nome_width/2 - 1*cm, height - 7.3*cm, 
             width/2 + nome_width/2 + 1*cm, height - 7.3*cm)
    
    pdf.setFont("Helvetica", 14)
    pdf.setFillColor(HexColor('#333333'))
    
    texto_participacao = f"participou do evento"
    pdf.drawCentredString(width/2, height - 9*cm, texto_participacao)
    
    pdf.setFont("Helvetica-Bold", 18)
    pdf.setFillColor(HexColor('#667eea'))
    pdf.drawCentredString(width/2, height - 10.5*cm, dados_certificado['evento_titulo'])
    
    if dados_certificado.get('evento_descricao'):
        pdf.setFont("Helvetica", 12)
        pdf.setFillColor(HexColor('#666666'))
        descricao = dados_certificado['evento_descricao']
        if len(descricao) > 100:
            descricao = descricao[:97] + "..."
        pdf.drawCentredString(width/2, height - 11.8*cm, descricao)
    
    pdf.setFont("Helvetica", 11)
    pdf.setFillColor(HexColor('#333333'))
    
    y_position = height - 13.5*cm
    
    if isinstance(dados_certificado['data_inicio'], str):
        data_inicio_fmt = datetime.strptime(dados_certificado['data_inicio'], '%Y-%m-%d').strftime('%d/%m/%Y')
    else:
        data_inicio_fmt = dados_certificado['data_inicio'].strftime('%d/%m/%Y')
        
    if isinstance(dados_certificado['data_fim'], str):
        data_fim_fmt = datetime.strptime(dados_certificado['data_fim'], '%Y-%m-%d').strftime('%d/%m/%Y')
    else:
        data_fim_fmt = dados_certificado['data_fim'].strftime('%d/%m/%Y')
    
    texto_periodo = f"Realizado no período de {data_inicio_fmt} a {data_fim_fmt}"
    pdf.drawCentredString(width/2, y_position, texto_periodo)
    
    texto_local = f"Local: {dados_certificado['local']}"
    pdf.drawCentredString(width/2, y_position - 0.7*cm, texto_local)
    
    if dados_certificado.get('carga_horaria'):
        texto_carga = f"Carga horária: {dados_certificado['carga_horaria']} horas"
        pdf.drawCentredString(width/2, y_position - 1.4*cm, texto_carga)
    
    pdf.setFont("Helvetica", 10)
    pdf.setFillColor(HexColor('#666666'))
    if isinstance(dados_certificado['data_emissao'], str):
        data_emissao_fmt = datetime.strptime(dados_certificado['data_emissao'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y')
    else:
        data_emissao_fmt = dados_certificado['data_emissao'].strftime('%d/%m/%Y')
    pdf.drawCentredString(width/2, 3*cm, f"Emitido em: {data_emissao_fmt}")
    
    pdf.setFont("Helvetica", 8)
    pdf.setFillColor(HexColor('#999999'))
    pdf.drawCentredString(width/2, 2.3*cm, f"Código de Validação: {dados_certificado['codigo_validacao']}")
    
    url_validacao = f"http://seudominio.com/validar/{dados_certificado['codigo_validacao']}"
    pdf.drawCentredString(width/2, 1.8*cm, f"Valide este certificado em: {url_validacao}")
    
    pdf.setStrokeColor(HexColor('#333333'))
    pdf.setLineWidth(1)
    pdf.line(width/2 - 5*cm, 5*cm, width/2 + 5*cm, 5*cm)
    
    pdf.setFont("Helvetica", 10)
    pdf.setFillColor(HexColor('#333333'))
    pdf.drawCentredString(width/2, 4.5*cm, "Sistema de Eventos - Univates")
    
    pdf.save()
    
    print(f"Certificado gerado: {caminho_completo}")
    return caminho_completo

except Exception as e:
    print(f"Erro ao gerar PDF: {str(e)}")
    import traceback
    traceback.print_exc()
    raise e