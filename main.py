import argparse
import sys
import os
import subprocess # Para executar o chatbot
from pathlib import Path

# --- Configuração de Caminhos Base ---
# Assume que main.py está na raiz do projeto
BASE_DIR = Path(__file__).resolve().parent
INPUT_DIR = BASE_DIR / 'input_pdfs'
OUTPUT_DIR = BASE_DIR / 'output_payslips'
SRC_DIR = BASE_DIR / 'src'

# Adiciona a pasta 'src' ao sys.path para que possamos importar os módulos
# Isso garante que os imports dentro dos módulos de 'src' também funcionem corretamente
sys.path.insert(0, str(SRC_DIR))

# --- Imports dos Módulos do Projeto ---
try:
    # Importa as funções específicas que serão chamadas
    from pdf_processor import split_encrypt_pdf
    from proactive_sender import run_proactive_distribution
    # Não precisamos importar chatbot_app diretamente, vamos executá-lo como script
except ImportError as e:
    print(f"Erro: Não foi possível importar módulos necessários da pasta 'src'.")
    print(f"Verifique se a estrutura de pastas está correta e se existe um __init__.py em 'src'.")
    print(f"Detalhe do erro: {e}")
    sys.exit(1)

def run_process(args):
    """Executa a Fase 1: Processamento do PDF Mestre."""
    print("--- Executando Fase 1: Processamento de PDF ---")
    master_pdf_path = Path(args.pdf)
    competence = args.competence

    if not master_pdf_path.is_absolute():
        master_pdf_path = INPUT_DIR / master_pdf_path # Assume que está em input_pdfs se não for absoluto

    if not master_pdf_path.exists():
        print(f"Erro: Arquivo PDF mestre não encontrado em '{master_pdf_path}'")
        sys.exit(1)

    # Validação simples da competência
    if not (len(competence) == 6 and competence.isdigit()):
         print("Erro: Formato da competência inválido. Use MMYYYY (ex: 032025).")
         sys.exit(1)

    print(f"Processando arquivo: {master_pdf_path}")
    print(f"Competência: {competence}")
    print(f"Diretório de Saída: {OUTPUT_DIR}")

    try:
        generated_files = split_encrypt_pdf(str(master_pdf_path), str(OUTPUT_DIR), competence)
        print(f"--- Processamento concluído. {len(generated_files)} arquivos gerados. ---")
    except Exception as e:
        print(f"Erro durante o processamento do PDF: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def run_send(args):
    """Executa a Fase 4: Envio Proativo dos Holerites."""
    print("--- Executando Fase 4: Envio Proativo de Holerites ---")
    master_pdf_path = Path(args.pdf) # A função run_proactive_distribution chama o split_encrypt_pdf
    competence = args.competence

    if not master_pdf_path.is_absolute():
        master_pdf_path = INPUT_DIR / master_pdf_path # Assume que está em input_pdfs se não for absoluto

    if not master_pdf_path.exists():
        print(f"Erro: Arquivo PDF mestre não encontrado em '{master_pdf_path}' para iniciar o envio.")
        sys.exit(1)

    # Validação simples da competência
    if not (len(competence) == 6 and competence.isdigit()):
         print("Erro: Formato da competência inválido. Use MMYYYY (ex: 032025).")
         sys.exit(1)

    print(f"Iniciando envio para competência: {competence}")
    print(f"Usando PDF mestre: {master_pdf_path}")
    print(f"Diretório de Saída (para PDFs processados): {OUTPUT_DIR}")
    print("Certifique-se que seu arquivo .env está configurado com as credenciais do Twilio.")
    print("Lembre-se da necessidade de uma 'media_url' pública para os PDFs (configurada dentro de proactive_sender.py ou via servidor/ngrok).")

    try:
        run_proactive_distribution(str(master_pdf_path), competence, str(OUTPUT_DIR))
        print(f"--- Envio proativo concluído. Verifique os logs para detalhes. ---")
    except Exception as e:
        print(f"Erro durante o envio proativo: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def run_chatbot(args):
    """Executa a Fase 5: Inicia o Servidor do Chatbot."""
    print("--- Executando Fase 5: Iniciando Servidor do Chatbot ---")
    chatbot_script_path = SRC_DIR / 'chatbot_app.py'

    if not chatbot_script_path.exists():
        print(f"Erro: Script do chatbot não encontrado em '{chatbot_script_path}'")
        sys.exit(1)

    print(f"Iniciando {chatbot_script_path}...")
    print("O chatbot ficará rodando neste terminal. Pressione Ctrl+C para parar.")
    print("Certifique-se que o webhook do Twilio está configurado corretamente.")
    print("Se estiver rodando localmente, lembre-se de usar o ngrok.")
    print("-------------------------------------------------------------")

    try:
        # Executa o script Flask. Ele assumirá o controle do terminal.
        # Usamos sys.executable para garantir que estamos usando o mesmo interpretador Python.
        subprocess.run([sys.executable, str(chatbot_script_path)], check=True)
    except KeyboardInterrupt:
        print("\n--- Servidor do Chatbot interrompido pelo usuário. ---")
    except subprocess.CalledProcessError as e:
        print(f"\nErro: O script do chatbot terminou com erro (código {e.returncode}).")
    except Exception as e:
        print(f"\nErro inesperado ao tentar iniciar o chatbot: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Orquestrador do Projeto de Distribuição de Holerites.")

    subparsers = parser.add_subparsers(dest='action', required=True, help='Ação a ser executada')

    # --- Sub-comando para Processar PDFs ---
    parser_process = subparsers.add_parser('process', help='Executa apenas a divisão e encriptação dos PDFs (Fase 1).')
    parser_process.add_argument('--pdf', required=True, help='Caminho para o arquivo PDF mestre (relativo a input_pdfs/ ou absoluto).')
    parser_process.add_argument('--competence', required=True, help='Competência no formato MMYYYY (ex: 032025).')
    parser_process.set_defaults(func=run_process)

    # --- Sub-comando para Enviar Holerites ---
    parser_send = subparsers.add_parser('send', help='Processa e envia os holerites da competência via WhatsApp (Fase 4).')
    parser_send.add_argument('--pdf', required=True, help='Caminho para o arquivo PDF mestre (relativo a input_pdfs/ ou absoluto).')
    parser_send.add_argument('--competence', required=True, help='Competência no formato MMYYYY (ex: 032025).')
    parser_send.set_defaults(func=run_send)

    # --- Sub-comando para Iniciar o Chatbot ---
    parser_chatbot = subparsers.add_parser('chatbot', help='Inicia o servidor do chatbot para responder solicitações (Fase 5).')
    parser_chatbot.set_defaults(func=run_chatbot)

    # Analisa os argumentos passados na linha de comando
    args = parser.parse_args()

    # Chama a função associada à ação escolhida
    args.func(args)