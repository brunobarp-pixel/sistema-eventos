from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import cm, inch
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from datetime import datetime, date
import os

def gerar_certificado_pdf(dados_certificado, output_path):
    """
    Gera um certificado em PDF com design bonito e profissional
    
    Args:
        dados_certificado: dict contendo:
            - nome_participante: str
            - evento_titulo: str
            - evento_descricao: str (opcional)
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
        
        # Bordas decorativas
        pdf.setStrokeColor(HexColor('#667eea'))
        pdf.setLineWidth(3)
        pdf.rect(1*cm, 1*cm, width - 2*cm, height - 2*cm, stroke=1, fill=0)
        
        pdf.setStrokeColor(HexColor('#764ba2'))
        pdf.setLineWidth(1)
        pdf.rect(1.3*cm, 1.3*cm, width - 2.6*cm, height - 2.6*cm, stroke=1, fill=0)
        
        # Título "CERTIFICADO"
        pdf.setFont("Helvetica-Bold", 40)
        pdf.setFillColor(HexColor("#3256f8"))
        pdf.drawCentredString(width/2, height - 4*cm, "CERTIFICADO")
        
        # "Certificamos que"
        pdf.setFont("Helvetica", 16)
        pdf.setFillColor(HexColor('#333333'))
        pdf.drawCentredString(width/2, height - 5*cm, "Certificamos que")
        
        # Nome do participante
        pdf.setFont("Helvetica-Bold", 28)
        pdf.setFillColor(HexColor('#000000'))
        pdf.drawCentredString(width/2, height - 7*cm, dados_certificado['nome_participante'].upper())
        
        # Linha sob o nome
        pdf.setStrokeColor(HexColor("#3256f8"))
        pdf.setLineWidth(2)
        nome_width = pdf.stringWidth(dados_certificado['nome_participante'].upper(), "Helvetica-Bold", 28)
        pdf.line(width/2 - nome_width/2 - 1*cm, height - 7.3*cm, 
                 width/2 + nome_width/2 + 1*cm, height - 7.3*cm)
        
        # "participou do evento"
        pdf.setFont("Helvetica", 14)
        pdf.setFillColor(HexColor('#333333'))
        texto_participacao = f"participou do evento"
        pdf.drawCentredString(width/2, height - 9*cm, texto_participacao)
        
        # Título do evento
        pdf.setFont("Helvetica-Bold", 18)
        pdf.setFillColor(HexColor('#667eea'))
        pdf.drawCentredString(width/2, height - 10.5*cm, dados_certificado['evento_titulo'])
        
        # Descrição do evento (se fornecida)
        if dados_certificado.get('evento_descricao'):
            pdf.setFont("Helvetica", 12)
            pdf.setFillColor(HexColor('#666666'))
            descricao = dados_certificado['evento_descricao']
            if len(descricao) > 100:
                descricao = descricao[:97] + "..."
            pdf.drawCentredString(width/2, height - 11.8*cm, descricao)
        
        # Informações do evento
        pdf.setFont("Helvetica", 11)
        pdf.setFillColor(HexColor('#333333'))
        
        y_position = height - 13.5*cm
        
        # Formatação das datas
        def formatar_data(data_str):
            """Função para formatar datas em múltiplos formatos"""
            if not isinstance(data_str, str):
                return data_str.strftime('%d/%m/%Y')
            
            # Remover microsegundos e timezone se existirem
            data_limpa = data_str.split('.')[0].split('+')[0].strip()
            
            formatos = [
                '%Y-%m-%d',
                '%d-%m-%Y',
                '%Y-%m-%d %H:%M:%S',
                '%d-%m-%Y %H:%M:%S',
                '%Y/%m/%d',
                '%d/%m/%Y'
            ]
            
            for formato in formatos:
                try:
                    return datetime.strptime(data_limpa, formato).strftime('%d/%m/%Y')
                except ValueError:
                    continue
            
            # Se nenhum formato funcionar, retornar como string
            return str(data_str)
        
        data_inicio_fmt = formatar_data(dados_certificado['data_inicio'])
        data_fim_fmt = formatar_data(dados_certificado['data_fim'])
        
        # Período do evento
        texto_periodo = f"Realizado no período de {data_inicio_fmt} a {data_fim_fmt}"
        pdf.drawCentredString(width/2, y_position, texto_periodo)
        
        # Local
        texto_local = f"Local: {dados_certificado['local']}"
        pdf.drawCentredString(width/2, y_position - 0.7*cm, texto_local)
        
        # Carga horária (se fornecida)
        if dados_certificado.get('carga_horaria'):
            texto_carga = f"Carga horária: {dados_certificado['carga_horaria']} horas"
            pdf.drawCentredString(width/2, y_position - 1.4*cm, texto_carga)
        
        # Data de emissão
        pdf.setFont("Helvetica", 10)
        pdf.setFillColor(HexColor('#666666'))
        
        def formatar_data_emissao(data_str):
            """Função específica para formatar data de emissão"""
            if not isinstance(data_str, str):
                return data_str.strftime('%d/%m/%Y')
            
            # Remover microsegundos e timezone se existirem
            data_limpa = data_str.split('.')[0].split('+')[0].strip()
            
            formatos = [
                '%Y-%m-%d %H:%M:%S',
                '%d-%m-%Y %H:%M:%S',
                '%Y-%m-%d',
                '%d-%m-%Y',
                '%Y/%m/%d %H:%M:%S',
                '%d/%m/%Y %H:%M:%S',
                '%Y/%m/%d',
                '%d/%m/%Y'
            ]
            
            for formato in formatos:
                try:
                    return datetime.strptime(data_limpa, formato).strftime('%d/%m/%Y')
                except ValueError:
                    continue
            
            # Se nenhum formato funcionar, retornar como string
            return str(data_str)
        
        data_emissao_fmt = formatar_data_emissao(dados_certificado['data_emissao'])
        pdf.drawCentredString(width/2, 3*cm, f"Emitido em: {data_emissao_fmt}")
        
        # Código de validação
        pdf.setFont("Helvetica", 8)
        pdf.setFillColor(HexColor('#999999'))
        pdf.drawCentredString(width/2, 2.3*cm, f"Código de Validação: {dados_certificado['codigo_validacao']}")
        
        # URL de validação
        url_validacao = f"http://seudominio.com/validar/{dados_certificado['codigo_validacao']}"
        pdf.drawCentredString(width/2, 1.8*cm, f"Valide este certificado em: {url_validacao}")
        
        # Linha de assinatura
        pdf.setStrokeColor(HexColor('#333333'))
        pdf.setLineWidth(1)
        pdf.line(width/2 - 5*cm, 5*cm, width/2 + 5*cm, 5*cm)
        
        # Nome da instituição
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