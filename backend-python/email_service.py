import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


MODO_TESTE = False  # True = usa MailHog, False = envia e-mails de verdade

# Configurações de e-mail (valores fixos)
EMAIL_HOST = 'smtp.gmail.com'  # Gmail SMTP
EMAIL_PORT = 587  # Porta TLS do Gmail  
EMAIL_USER = 'bqgames999'  # Seu email do Gmail
EMAIL_PASSWORD = 'ghme mpkt ecfs gcmc'  # Senha de app do Gmail
EMAIL_FROM = 'Sistema de Eventos <noreply@eventos.com>'


def enviar_email(destinatario, assunto, corpo_html):
    
    if MODO_TESTE:
        return enviar_email_mailhog(destinatario, assunto, corpo_html)
    else:
        return enviar_email_smtp(destinatario, assunto, corpo_html)


def enviar_email_mailhog(destinatario, assunto, corpo_html):
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        mensagem = MIMEMultipart('alternative')
        mensagem['Subject'] = assunto
        mensagem['From'] = EMAIL_FROM
        mensagem['To'] = destinatario
        
        parte_html = MIMEText(corpo_html, 'html', 'utf-8')
        mensagem.attach(parte_html)
        
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as servidor:
            servidor.send_message(mensagem)
        
        print(f"Email enviado para MailHog: {destinatario}")
        return True
        
    except Exception as e:
        print(f"Erro ao enviar email para MailHog: {str(e)}")
        return salvar_email_local(destinatario, assunto, corpo_html)


def enviar_email_smtp(destinatario, assunto, corpo_html):
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        mensagem = MIMEMultipart('alternative')
        mensagem['Subject'] = assunto
        mensagem['From'] = EMAIL_FROM
        mensagem['To'] = destinatario
        
        parte_html = MIMEText(corpo_html, 'html', 'utf-8')
        mensagem.attach(parte_html)
        
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as servidor:
            servidor.starttls()
            servidor.login(EMAIL_USER, EMAIL_PASSWORD)
            servidor.send_message(mensagem)
        
        print(f"E-mail enviado para {destinatario}")
        return True
        
    except Exception as e:
        print(f"Erro ao enviar e-mail: {str(e)}")
        return False


def salvar_email_local(destinatario, assunto, corpo_html):
    try:
        if not os.path.exists('emails_enviados'):
            os.makedirs('emails_enviados')
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        nome_limpo = destinatario.replace('@', '_at_').replace('.', '_')
        nome_arquivo = f"emails_enviados/email_{timestamp}_{nome_limpo}.html"
        
        with open(nome_arquivo, 'w', encoding='utf-8') as f:
            f.write(f"<!-- Para: {destinatario} -->\n")
            f.write(f"<!-- Assunto: {assunto} -->\n")
            f.write(f"<!-- Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} -->\n\n")
            f.write(corpo_html)
        
        print(f"E-mail salvo: {nome_arquivo}")
        return True
        
    except Exception as e:
        print(f"Erro ao salvar e-mail: {str(e)}")
        return False


def enviar_email_inscricao(usuario, evento):
    assunto = f"Inscrição Confirmada - {evento['nome']}"
    
    corpo_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                       color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ background: #f8f9fa; padding: 30px; }}
            .evento-info {{ background: white; padding: 20px; border-radius: 5px; margin: 20px 0; }}
            .footer {{ background: #333; color: white; padding: 20px; text-align: center; 
                      border-radius: 0 0 10px 10px; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Inscrição Confirmada!</h1>
            </div>
            <div class="content">
                <p>Olá, <strong>{usuario['nome']}</strong>!</p>
                
                <p>Sua inscrição foi confirmada com sucesso no evento:</p>
                
                <div class="evento-info">
                    <h2>{evento['nome']}</h2>
                    <p><strong>Data:</strong> {evento.get('data_inicio', 'A definir')}</p>
                    <p><strong>Local:</strong> {evento.get('local', 'A definir')}</p>
                </div>
                
                <p>E os Guri da TI</p>
                
                <p><strong>Importante:</strong> Apresente este e-mail ou seu CPF no dia do evento.</p>
                
                <p>Show de bola Marcio</p>
            </div>
            <div class="footer">
                <p>Sistema de Eventos</p>
                <p>Este é um e-mail automático, não responda.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return enviar_email(usuario['email'], assunto, corpo_html)


def enviar_email_certificado(usuario, evento, certificado):#rever isso aqui
    assunto = f"Certificado Emitido - {evento['nome']}"
    
    corpo_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                       color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ background: #f8f9fa; padding: 30px; }}
            .cert-box {{ background: white; padding: 20px; border-radius: 5px; 
                        margin: 20px 0; border-left: 4px solid #ffc107; }}
            .code {{ background: #eee; padding: 10px; font-family: monospace; 
                    word-break: break-all; border-radius: 5px; }}
            .btn {{ background: #667eea; color: white; padding: 12px 30px; 
                   text-decoration: none; display: inline-block; border-radius: 5px; 
                   margin-top: 15px; }}
            .footer {{ background: #333; color: white; padding: 20px; text-align: center; 
                      border-radius: 0 0 10px 10px; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Certificado Emitido!</h1>
            </div>
            <div class="content">
                <p>Olá, <strong>{usuario['nome']}</strong>!</p>
                
                <p>Parabéns! Seu certificado de participação foi emitido com sucesso.</p>
                
                <div class="cert-box">
                    <h2>{evento['nome']}</h2>
                    <p><strong>Período:</strong> {evento['data_inicio']} a {evento['data_fim']}</p>
                    <p><strong>Local:</strong> {evento['local']}</p>
                    <p><strong>Data de Emissão:</strong> {certificado['data_emissao']}</p>
                </div>
                
                <p><strong>Seu certificado está ANEXADO neste e-mail!</strong></p>
                
                <p><strong>Código de Validação:</strong></p>
                <div class="code">{certificado['codigo_validacao']}</div>
                
                <p style="text-align: center;">
                    <a href="{certificado['url_validacao']}" class="btn">
                        Validar Certificado Online
                    </a>
                </p>
                
                <p><small>Você também pode validar este certificado a qualquer momento usando o código acima.</small></p>
            </div>
            <div class="footer">
                <p>Sistema de Eventos</p>
                <p>Este é um e-mail automático, não responda.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    try: #dando B.O isso aqui ein, rever
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        from email.mime.application import MIMEApplication
        import os
        
        from gerador_pdf import gerar_certificado_pdf
        
        dados_pdf = {
            'nome_participante': usuario['nome'],
            'evento_titulo': evento['nome'],
            'evento_descricao': evento.get('descricao', ''),
            'data_inicio': evento['data_inicio'].split()[0] if ' ' in evento['data_inicio'] else evento['data_inicio'],
            'data_fim': evento['data_fim'].split()[0] if ' ' in evento['data_fim'] else evento['data_fim'],
            'local': evento['local'],
            'carga_horaria': evento.get('carga_horaria'),
            'codigo_validacao': certificado['codigo_validacao'],
            'data_emissao': certificado['data_emissao']
        }
        
        pdf_path = gerar_certificado_pdf(dados_pdf, "certificados_pdf")
        
        if MODO_TESTE:
            print(f"E-mail com PDF anexado seria enviado para {usuario['email']}")
            print(f"   PDF gerado: {pdf_path}")
            return salvar_email_local(usuario['email'], assunto, corpo_html)
        
        mensagem = MIMEMultipart('mixed')
        mensagem['Subject'] = assunto
        mensagem['From'] = EMAIL_FROM
        mensagem['To'] = usuario['email']
        
        parte_html = MIMEText(corpo_html, 'html', 'utf-8')
        mensagem.attach(parte_html)
        
        if os.path.exists(pdf_path):
            with open(pdf_path, 'rb') as f:
                pdf_anexo = MIMEApplication(f.read(), _subtype='pdf')
                nome_arquivo = f"Certificado_{evento['nome'].replace(' ', '_')}.pdf"
                pdf_anexo.add_header('Content-Disposition', 'attachment', filename=nome_arquivo)
                mensagem.attach(pdf_anexo)
        
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as servidor:
            servidor.starttls()
            servidor.login(EMAIL_USER, EMAIL_PASSWORD)
            servidor.send_message(mensagem)
        
        print(f"E-mail com PDF anexado enviado para {usuario['email']}")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao enviar e-mail com anexo: {str(e)}")
        return enviar_email(usuario['email'], assunto, corpo_html)


def enviar_email_cancelamento(usuario, evento):
    assunto = f"Inscrição Cancelada - {evento['nome']}"
    
    corpo_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: #f5576c; color: white; padding: 30px; 
                       text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ background: #f8f9fa; padding: 30px; }}
            .footer {{ background: #333; color: white; padding: 20px; text-align: center; 
                      border-radius: 0 0 10px 10px; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Inscrição Cancelada</h1>
            </div>
            <div class="content">
                <p>Olá, <strong>{usuario['nome']}</strong>!</p>
                
                <p>Sua inscrição no evento <strong>{evento['nome']}</strong> foi cancelada.</p>
                
                <p><strong>Dados do evento:</strong></p>
                <ul>
                    <li><strong>Data:</strong> {evento.get('data_inicio', 'A definir')}</li>
                    <li><strong>Local:</strong> {evento.get('local', 'A definir')}</li>
                </ul>
                
                <p>Ja vai Boltz :(</p>
                
                <p>I'll miss you!</p>
            </div>
            <div class="footer">
                <p>Sistema de Eventos</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return enviar_email(usuario['email'], assunto, corpo_html)


def enviar_email_checkin(usuario, evento):
    assunto = f"Presença Confirmada - {evento['nome']}"
    
    corpo_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); 
                       color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ background: #f8f9fa; padding: 30px; }}
            .checkin-info {{ background: white; padding: 20px; border-radius: 5px; 
                            margin: 20px 0; border-left: 4px solid #38ef7d; }}
            .footer {{ background: #333; color: white; padding: 20px; text-align: center; 
                      border-radius: 0 0 10px 10px; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Presença Confirmada!</h1>
            </div>
            <div class="content">
                <p>Olá, <strong>{usuario['nome']}</strong>!</p>
                
                <p>Sua presença foi registrada com sucesso no evento:</p>
                
                <div class="checkin-info">
                    <h2>{evento['nome']}</h2>
                    <p><strong>Data:</strong> {evento.get('data_inicio', 'A definir')}</p>
                    <p><strong>Local:</strong> {evento.get('local', 'A definir')}</p>
                    <p><strong>Check-in realizado em:</strong> {datetime.now().strftime('%d/%m/%Y às %H:%M')}</p>
                </div>
                
                <p>VAMOOOO! Parabens agora e so pra frente</p>
                
                <p>Aproveite o evento!</p>
            </div>
            <div class="footer">
                <p>Sistema de Eventos</p>
                <p>Este é um e-mail automático, não responda.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return enviar_email(usuario['email'], assunto, corpo_html)

