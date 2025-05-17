# --- Script de envio proativo ---
# src/proactive_sender.py
import sys
import os
from pathlib import Path
from pdf_processor import split_encrypt_pdf
from data_manager import get_whatsapp_number
from whatsapp_sender import send_whatsapp_message
# Importe aqui a função para fazer upload para a nuvem e obter URL (ex: upload_to_s3)
# from cloud_uploader import upload_and_get_url # Módulo hipotético

def run_proactive_distribution(master_pdf_path: str, competence: str, output_base_dir: str):
    """
    Executa a divisão do PDF e o envio proativo dos holerites.
    """
    print(f"Iniciando distribuição proativa para competência {competence}...")

    # 1. Processar o PDF mestre
    generated_files = split_encrypt_pdf(master_pdf_path, output_base_dir, competence)

    if not generated_files:
        print("Nenhum arquivo PDF individual foi gerado. Encerrando.")
        return

    print(f"\nIniciando envio para {len(generated_files)} funcionários...")

    success_count = 0
    fail_count = 0

    for pdf_path_str in generated_files:
        pdf_path = Path(pdf_path_str)
        filename = pdf_path.name # Ex: 032025-123456.pdf

        # Extrair matrícula do nome do arquivo
        try:
            # Assume formato COMPETENCE-MATRICULA.pdf
            matricula = filename.split('-')[1].split('.')[0]
        except IndexError:
            print(f"Erro: Não foi possível extrair matrícula do nome do arquivo: {filename}")
            fail_count += 1
            continue

        # 2. Obter número de WhatsApp
        whatsapp_number = get_whatsapp_number(matricula)
        if not whatsapp_number:
            print(f"Aviso: Número de WhatsApp não encontrado para matrícula {matricula}. Pulando.")
            fail_count += 1
            continue

        # 3. **[PONTO CRÍTICO]** Fazer upload do PDF e obter URL pública
        # Substitua esta linha pela sua lógica de upload real
        print(f"  Simulando upload para {matricula} ({whatsapp_number})...")
        # pdf_public_url = upload_and_get_url(str(pdf_path)) # Exemplo com função de upload
        # --- SIMULAÇÃO ---
        # Para teste SEM upload real, você pode precisar de um URL de exemplo,
        # mas o envio da Twilio FALHARÁ ao tentar buscar um arquivo inexistente.
        # Comente a linha abaixo se for usar upload real.
        pdf_public_url = f"http://example.com/pdfs/{competence}/{filename}" # URL Fictícia!
        # ----------------

        if not pdf_public_url:
             print(f"Erro: Falha ao obter URL pública para {filename}. Pulando.")
             fail_count += 1
             continue

        # 4. Enviar mensagem via Twilio
        competence_display = f"{competence[:2]}/{competence[2:]}" # Formata para MM/YYYY
        message_body = (
            f"Olá! Seu holerite referente à competência {competence_display} está disponível.\n"
            f"Para abrir o PDF, utilize sua matrícula como senha."
            #f"Para abrir o PDF, utilize sua matrícula ({matricula}) como senha."
        )

        print(f"  Enviando para {matricula} ({whatsapp_number}) com URL: {pdf_public_url} ...")
        message_sid = send_whatsapp_message(
            to_number=whatsapp_number,
            body=message_body,
            #media_url=pdf_public_url - Correto
            media_url=None # Teste
        )

        if message_sid:
            print(f"  -> Envio para {matricula} bem-sucedido (SID: {message_sid}).")
            success_count += 1
            # Opcional: Mover ou registrar o arquivo como enviado
        else:
            print(f"  -> Falha no envio para {matricula}.")
            fail_count += 1
            # Opcional: Registrar a falha para tentativa posterior

    print("\nDistribuição proativa concluída.")
    print(f"Sucessos: {success_count}")
    print(f"Falhas: {fail_count}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: python src/proactive_sender.py <caminho_pdf_mestre> <competencia_MMYYYY>")
        print("Exemplo: python src/proactive_sender.py input_pdfs/holerites_032025.pdf 032025")
        sys.exit(1)

    master_pdf = sys.argv[1]
    competence_arg = sys.argv[2]
    output_dir_base = Path(__file__).parent.parent / 'output_payslips'

    if not Path(master_pdf).exists():
        print(f"Erro: Arquivo PDF mestre não encontrado em '{master_pdf}'")
        sys.exit(1)

    # Validação simples da competência (MMYYYY)
    if not (len(competence_arg) == 6 and competence_arg.isdigit()):
         print("Erro: Formato da competência inválido. Use MMYYYY (ex: 032025).")
         sys.exit(1)

    run_proactive_distribution(master_pdf, competence_arg, str(output_dir_base))
