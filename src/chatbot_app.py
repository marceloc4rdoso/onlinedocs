# src/chatbot_app.py
import os
import re
from flask import Flask, request, Response
from twilio.twiml.messaging_response import MessagingResponse
from dotenv import load_dotenv
from pathlib import Path

from data_manager import get_matricula_by_whatsapp, get_whatsapp_number # Reutiliza o data manager
from whatsapp_sender import send_whatsapp_message # Reutiliza o sender
# Importe aqui a função para fazer upload para a nuvem e obter URL
# from cloud_uploader import upload_and_get_url # Módulo hipotético

load_dotenv()

app = Flask(__name__)

OUTPUT_PAYSIPS_DIR = Path(__file__).parent.parent / 'output_payslips'

@app.route("/whatsapp_webhook", methods=['POST'])
def whatsapp_webhook():
    """Recebe mensagens do WhatsApp via Twilio e responde."""
    incoming_msg = request.values.get('Body', '').strip()
    from_number = request.values.get('From', '') # Formato: whatsapp:+55...

    print(f"Mensagem recebida de {from_number}: '{incoming_msg}'")

    response = MessagingResponse()
    responded = False # Flag para saber se já enviamos uma resposta

    # 1. Identificar o funcionário pelo número de telefone
    matricula = get_matricula_by_whatsapp(from_number)

    if not matricula:
        print(f"Número {from_number} não encontrado na base de dados.")
        response.message("Desculpe, seu número não está cadastrado em nosso sistema.")
        responded = True
    else:
        # 2. Analisar a mensagem para identificar o pedido de holerite
        # Exemplo: "holerite 03/2025", "quero holerite março 2025", "032025"
        # Usar regex para extrair a competência MM/YYYY ou MMYYYY
        match = re.search(r"(\d{2})[/-]?(\d{4})", incoming_msg) # Busca MM/YYYY ou MM-YYYY ou MMYYYY
        competence_req = None
        if match:
            mes, ano = match.groups()
            competence_req = f"{mes}{ano}" # Formato MMYYYY
            print(f"Competência solicitada: {competence_req} por {matricula}")
        else:
            # Tentar entender pedidos mais simples como "último holerite" (requer lógica adicional)
            # ou apenas pedir o formato correto
            response.message("Por favor, informe a competência desejada no formato MM/AAAA (ex: 03/2025) ou MM-AAAA ou MMAAAA.")
            responded = True

        if competence_req and not responded:
            # 3. Localizar o arquivo PDF correspondente
            pdf_filename = f"{competence_req}-{matricula}.pdf"
            pdf_path = OUTPUT_PAYSIPS_DIR / competence_req / pdf_filename

            if pdf_path.exists():
                print(f"Arquivo encontrado: {pdf_path}")

                # 4. **[PONTO CRÍTICO]** Fazer upload do PDF e obter URL pública
                # Substitua esta linha pela sua lógica de upload real
                print(f"  Simulando upload do arquivo {pdf_filename}...")
                # pdf_public_url = upload_and_get_url(str(pdf_path))
                # --- SIMULAÇÃO ---
                # Comente a linha abaixo se for usar upload real.
                pdf_public_url = f"http://example.com/pdfs/{competence_req}/{pdf_filename}" # URL Fictícia!
                # -----------------

                if pdf_public_url:
                    # 5. Enviar o link do PDF via mensagem (não pode responder diretamente com mídia no TwiML)
                    # Usaremos a API REST para enviar uma *nova* mensagem com a mídia
                    competence_display = f"{competence_req[:2]}/{competence_req[2:]}"
                    message_body = (
                        f"Aqui está o seu holerite para {competence_display}.\n"
                        f"Lembre-se, a senha para abrir é a sua matrícula: {matricula}"
                    )

                    print(f"Enviando PDF {pdf_filename} para {from_number}...")
                    send_whatsapp_message(
                        to_number=from_number, # Envia de volta para quem pediu
                        body=message_body,
                        media_url=pdf_public_url
                    )
                    # Não envie uma resposta TwiML vazia se usou a API REST para responder
                    # Apenas retorne uma resposta HTTP 200 OK para o Twilio
                    # Se não enviar nada aqui, o Twilio pode entender como erro
                    # Podemos enviar uma msg simples de confirmação via TwiML se preferir
                    # response.message(f"Enviando seu holerite de {competence_display}...")
                    # responded = True

                    # Devolver uma resposta vazia (HTTP 200) indica ao Twilio que processamos o webhook
                    return Response(status=200)

                else:
                    print(f"Erro ao obter URL pública para {pdf_path}")
                    response.message("Ocorreu um erro ao preparar seu holerite. Tente novamente mais tarde.")
                    responded = True
            else:
                print(f"Arquivo não encontrado: {pdf_path}")
                response.message(f"Não encontrei o holerite para a competência {competence_req[:2]}/{competence_req[2:]}. Verifique a data ou entre em contato com o RH.")
                responded = True

    # Se nenhuma resposta específica foi enviada, envie uma padrão ou de erro
    if not responded:
         response.message("Não entendi sua solicitação. Para pedir um holerite, envie 'holerite MM/AAAA'.")

    # Retorna a resposta TwiML para o Twilio
    return str(response)

if __name__ == "__main__":
    # Para rodar localmente com ngrok:
    # 1. Instale ngrok: https://ngrok.com/download
    # 2. Rode: ngrok http 5000 (ou a porta que o Flask usar)
    # 3. Copie a URL https://xxxx-xxxx-xxxx.ngrok.io
    # 4. Configure essa URL + /whatsapp_webhook no webhook do seu número Twilio WhatsApp
    print("Iniciando servidor Flask para o chatbot...")
    print(f"Webhook esperado em /whatsapp_webhook")
    print(f"Use ngrok ou similar para expor a porta 5000 publicamente.")
    app.run(debug=True, port=5000, host='0.0.0.0') # Escuta em todas as interfaces
