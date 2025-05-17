# src/whatsapp_sender.py
import os
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv() # Carrega variáveis do .env

ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")

if not all([ACCOUNT_SID, AUTH_TOKEN, TWILIO_NUMBER]):
    print("Erro: Variáveis de ambiente da Twilio não configuradas no .env")
    # exit() ou levantar um erro

try:
    client = Client(ACCOUNT_SID, AUTH_TOKEN)
except Exception as e:
    print(f"Erro ao inicializar cliente Twilio: {e}")
    client = None # Impede chamadas subsequentes se a inicialização falhar

def send_whatsapp_message(to_number: str, body: str, media_url: str = None):
    """Envia uma mensagem de WhatsApp, opcionalmente com mídia."""
    if not client:
        print("Erro: Cliente Twilio não inicializado.")
        return None
    if not to_number:
        print(f"Erro: Número de destino inválido ou não fornecido.")
        return None

    try:
        message = client.messages.create(
            from_=TWILIO_NUMBER,
            body=body,
            to=to_number,
            media_url=[media_url] if media_url else None # media_url deve ser uma lista
        )
        print(f"Mensagem enviada para {to_number}. SID: {message.sid}")
        return message.sid
    except Exception as e:
        print(f"Erro ao enviar mensagem para {to_number}: {e}")
        # Log detalhado do erro pode ser útil aqui
        # print(e.status, e.uri, e.body)
        return None

