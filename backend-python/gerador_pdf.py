"""
Gerador de Certificados em PDF
Sistema de Eventos - Python/Flask
"""

from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
import os

def gerar_certificado_pdf(dados_certificado, output_path='certificados_pdf'):
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
        print(f"📋 Gerando PDF com dados: {dados_certificado}")
        
        # Validar dados obrigatórios
        campos_obrigatorios = ['nome_participante', 'evento_titulo', 'codigo_validacao', 'data_inicio', 'data_fim', 'local', 'data_emissao']
        for campo in campos_obrigatorios:
            if not dados_certificado.get(campo):
                raise ValueError(f"Campo obrigatório '{campo}' não fornecido")
        
        # Criar pasta se não existir
        if not os.path.exists(output_path):
            os.makedirs(output_path)
            print(f"📁 Pasta criada: {output_path}")
        
        # Nome do arquivo
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        nome_arquivo = f"certificado_{dados_certificado['codigo_validacao'][:8]}_{timestamp}.pdf"
        caminho_completo = os.path.join(output_path, nome_arquivo)
        
        print(f"📄 Criando arquivo: {caminho_completo}")
    
    # Criar o PDF em paisagem (landscape)
    pdf = canvas.Canvas(caminho_completo, pagesize=landscape(A4))
    width, height = landscape(A4)
    
    # ==================== DESIGN DO CERTIFICADO ====================
    
    # Borda decorativa
    pdf.setStrokeColor(HexColor('#667eea'))
    pdf.setLineWidth(3)
    pdf.rect(1*cm, 1*cm, width - 2*cm, height - 2*cm, stroke=1, fill=0)
    
    pdf.setStrokeColor(HexColor('#764ba2'))
    pdf.setLineWidth(1)
    pdf.rect(1.3*cm, 1.3*cm, width - 2.6*cm, height - 2.6*cm, stroke=1, fill=0)
    
    # Título principal
    pdf.setFont("Helvetica-Bold", 40)
    pdf.setFillColor(HexColor('#667eea'))
    pdf.drawCentredString(width/2, height - 4*cm, "CERTIFICADO")
    
    # Subtítulo
    pdf.setFont("Helvetica", 16)
    pdf.setFillColor(HexColor('#333333'))
    pdf.drawCentredString(width/2, height - 5*cm, "Certificamos que")
    
    # Nome do participante (DESTAQUE)
    pdf.setFont("Helvetica-Bold", 28)
    pdf.setFillColor(HexColor('#000000'))
    pdf.drawCentredString(width/2, height - 7*cm, dados_certificado['nome_participante'].upper())
    
    # Linha decorativa sob o nome
    pdf.setStrokeColor(HexColor('#667eea'))
    pdf.setLineWidth(2)
    nome_width = pdf.stringWidth(dados_certificado['nome_participante'].upper(), "Helvetica-Bold", 28)
    pdf.line(width/2 - nome_width/2 - 1*cm, height - 7.3*cm, 
             width/2 + nome_width/2 + 1*cm, height - 7.3*cm)
    
    # Texto principal
    pdf.setFont("Helvetica", 14)
    pdf.setFillColor(HexColor('#333333'))
    
    texto_participacao = f"participou do evento"
    pdf.drawCentredString(width/2, height - 9*cm, texto_participacao)
    
    # Título do evento
    pdf.setFont("Helvetica-Bold", 18)
    pdf.setFillColor(HexColor('#667eea'))
    pdf.drawCentredString(width/2, height - 10.5*cm, dados_certificado['evento_titulo'])
    
    # Descrição do evento (se houver)
    if dados_certificado.get('evento_descricao'):
        pdf.setFont("Helvetica", 12)
        pdf.setFillColor(HexColor('#666666'))
        # Quebrar texto se for muito longo
        descricao = dados_certificado['evento_descricao']
        if len(descricao) > 100:
            descricao = descricao[:97] + "..."
        pdf.drawCentredString(width/2, height - 11.8*cm, descricao)
    
    # Informações do evento
    pdf.setFont("Helvetica", 11)
    pdf.setFillColor(HexColor('#333333'))
    
    y_position = height - 13.5*cm
    
    # Período
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
    
    # Local
    texto_local = f"Local: {dados_certificado['local']}"
    pdf.drawCentredString(width/2, y_position - 0.7*cm, texto_local)
    
    # Carga horária (se informada)
    if dados_certificado.get('carga_horaria'):
        texto_carga = f"Carga horária: {dados_certificado['carga_horaria']} horas"
        pdf.drawCentredString(width/2, y_position - 1.4*cm, texto_carga)
    
    # Data de emissão
    pdf.setFont("Helvetica", 10)
    pdf.setFillColor(HexColor('#666666'))
    if isinstance(dados_certificado['data_emissao'], str):
        data_emissao_fmt = datetime.strptime(dados_certificado['data_emissao'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y')
    else:
        data_emissao_fmt = dados_certificado['data_emissao'].strftime('%d/%m/%Y')
    pdf.drawCentredString(width/2, 3*cm, f"Emitido em: {data_emissao_fmt}")
    
    # Código de validação
    pdf.setFont("Helvetica", 8)
    pdf.setFillColor(HexColor('#999999'))
    pdf.drawCentredString(width/2, 2.3*cm, f"Código de Validação: {dados_certificado['codigo_validacao']}")
    
    # URL de validação
    url_validacao = f"http://seudominio.com/validar/{dados_certificado['codigo_validacao']}"
    pdf.drawCentredString(width/2, 1.8*cm, f"Valide este certificado em: {url_validacao}")
    
    # Assinatura (linha decorativa)
    pdf.setStrokeColor(HexColor('#333333'))
    pdf.setLineWidth(1)
    pdf.line(width/2 - 5*cm, 5*cm, width/2 + 5*cm, 5*cm)
    
    pdf.setFont("Helvetica", 10)
    pdf.setFillColor(HexColor('#333333'))
    pdf.drawCentredString(width/2, 4.5*cm, "Sistema de Eventos - Univates")
    
    # Finalizar PDF
    pdf.save()
    
    print(f"✅ Certificado gerado: {caminho_completo}")
    return caminho_completo

except Exception as e:
    print(f"❌ Erro ao gerar PDF: {str(e)}")
    import traceback
    traceback.print_exc()
    raise e


# ==================== TESTE ====================
if __name__ == '__main__':
    # Dados de exemplo
    dados_teste = {
        'nome_participante': 'Bruno Barp',
        'evento_titulo': 'Workshop de Desenvolvimento Web',
        'evento_descricao': 'Workshop intensivo sobre desenvolvimento web moderno com React, Node.js e boas práticas.',
        'data_inicio': '2025-11-01',
        'data_fim': '2025-11-03',
        'local': 'Auditório Principal - Univates',
        'carga_horaria': 20,
        'codigo_validacao': 'a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6',
        'data_emissao': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    print("🧪 Gerando certificado de teste...\n")
    gerar_certificado_pdf(dados_teste)
    print("\n✅ Teste concluído! Verifique a pasta 'certificados_pdf'")