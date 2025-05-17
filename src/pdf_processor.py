# src/pdf_processor.py
import os
import re
from pypdf import PdfReader, PdfWriter
from pathlib import Path

# -- FUNÇÃO 1: Encontrar Páginas (com nova estratégia de Regex) --
def find_payslip_starts(reader: PdfReader):
    """
    Tenta encontrar a matricula buscando por uma linha contendo apenas dígitos,
    seguida por uma linha que começa com 'FUNÇÃO'.
    Adaptação devido à extração de texto desordenada.
    Retorna um dicionário: {matricula: [lista_de_paginas]}
    """
    payslips = {}
    current_matricula = None
    current_pages = []

    # Regex AJUSTADO:
    # ^\s*(\d+)\s*$ : Início da linha (^), espaço opcional (\s*), captura de dígitos (\d+),
    #                 espaço opcional (\s*), fim da linha ($). Captura o número da matrícula no Grupo 1.
    # \n             : Caractere de nova linha.
    # ^\s*FUNÇÃO.*$  : Início da linha (^), espaço opcional (\s*), a palavra literal "FUNÇÃO",
    #                 qualquer caractere restante (.*), fim da linha ($).
    # Flags: re.MULTILINE (para ^ e $ funcionarem por linha) e re.IGNORECASE (para "FUNÇÃO")
    matricula_pattern = re.compile(r"^\s*(\d+)\s*\n\s*FUNÇÃO.*$", re.MULTILINE | re.IGNORECASE)

    first_page_text_printed = False
    print("Iniciando busca por matrículas (Método 2: Número antes de 'FUNÇÃO')...")

    for page_num, page in enumerate(reader.pages):
        try:
            # Extrai o texto da página
            text = page.extract_text()
            if not text:
                 print(f"Aviso: Página {page_num+1} sem texto extraível.")
                 continue

            # --- DEBUG: Imprimir texto da primeira página ---
            if not first_page_text_printed:
                print("\n" + "="*25)
                print(f" Texto Extraído da Página {page_num + 1} (para depuração):")
                print(repr(text)) # Usar repr() para ver caracteres especiais como \n, \r
                print("="*25 + "\n")
                first_page_text_printed = True
            # --- FIM DEBUG ---

            # Encontra todas as ocorrências do padrão na página
            matches = matricula_pattern.finditer(text)
            found_matricula_on_page = None # Armazena a matrícula encontrada nesta página

            for match in matches:
                potential_matricula = match.group(1) # Pega o número capturado
                # Verifica se é a primeira matrícula encontrada nesta página
                # (Evita problemas se o padrão ocorrer acidentalmente mais de uma vez)
                if found_matricula_on_page is None:
                    # Adicione uma validação básica se necessário (ex: comprimento esperado da matrícula)
                    if len(potential_matricula) >= 3 and len(potential_matricula) <= 6: # Ex: Matrícula tem entre 3 e 6 dígitos
                        found_matricula_on_page = potential_matricula
                        print(f"Página {page_num+1}: Matrícula POTENCIAL encontrada: {found_matricula_on_page}")
                    else:
                         print(f"Página {page_num+1}: Número '{potential_matricula}' encontrado antes de 'FUNÇÃO', mas não parece ter tamanho de matrícula válido. Ignorando.")
                else:
                    # Se encontrar mais de uma correspondência na mesma página, avisa.
                    print(f"Aviso: Múltiplos padrões de [número seguido por FUNÇÃO] encontrados na pág {page_num+1}. Usando o primeiro: {found_matricula_on_page}.")
                    break # Usa apenas a primeira ocorrência encontrada na página


            # Processa a matrícula encontrada (ou falta dela) para agrupar páginas
            if found_matricula_on_page:
                # Lógica para agrupar páginas (idêntica à versão anterior)
                if current_matricula is not None and found_matricula_on_page != current_matricula:
                    if current_matricula not in payslips:
                        payslips[current_matricula] = current_pages
                    # Inicia nova matrícula
                    current_matricula = found_matricula_on_page
                    current_pages = [page_num]
                elif current_matricula != found_matricula_on_page: # Primeira matrícula ou mudou
                     current_matricula = found_matricula_on_page
                     current_pages = [page_num]
                elif current_matricula == found_matricula_on_page and page_num not in current_pages: # Mesma matrícula, nova página
                     current_pages.append(page_num)

            # Se não encontrou matrícula nesta página, mas já estava rastreando uma
            elif current_matricula is not None and current_pages and page_num not in current_pages:
                 print(f"Página {page_num+1}: Sem matrícula encontrada via padrão, assumindo continuação da matrícula {current_matricula}")
                 current_pages.append(page_num)

        except Exception as e:
            print(f"Erro inesperado ao processar a página {page_num+1}: {e}")
            import traceback
            traceback.print_exc() # Imprime mais detalhes do erro

    # Adiciona o último holerite encontrado
    if current_matricula is not None and current_matricula not in payslips:
        payslips[current_matricula] = current_pages

    # Mensagem final sobre a busca
    if not payslips:
         print("\nERRO FINAL: Nenhuma matrícula foi encontrada no PDF usando o padrão regex atual.")
         print("          Verifique o 'Texto Extraído da Página 1' impresso acima.")
         print(f"          Padrão regex testado: {matricula_pattern.pattern}")
         print("          Causas possíveis: O texto extraído não contém o padrão esperado (número\\nFUNÇÃO) ou a extração falhou.")
    else:
         print(f"\nBusca de matrículas concluída. Encontradas {len(payslips)} matrículas distintas.")

    return payslips

# -- FUNÇÃO 2: Dividir e Encriptar (Garantir que está definida AQUI, antes do __main__) --
def split_encrypt_pdf(master_pdf_path: str, output_base_dir: str, competence: str):
    # (O código desta função permanece o mesmo da resposta anterior)
    # ... (Cole o código completo da função split_encrypt_pdf aqui) ...
    try:
        reader = PdfReader(master_pdf_path)
    except Exception as e:
        print(f"Erro ao abrir o PDF mestre '{master_pdf_path}': {e}")
        return []

    if reader.is_encrypted:
        print(f"Erro: O PDF mestre '{master_pdf_path}' está criptografado. Remova a senha antes de processar.")
        return []

    print(f"\nProcessando PDF: {master_pdf_path} para competência {competence}...")

    # Chama a função para encontrar as páginas DENTRO desta função
    payslips_pages = find_payslip_starts(reader) # Usa a função atualizada

    if not payslips_pages:
        print("Nenhum holerite individual identificado. Abortando a divisão.")
        return []

    output_dir = Path(output_base_dir) / competence
    output_dir.mkdir(parents=True, exist_ok=True)

    generated_files = []
    print(f"\nGerando {len(payslips_pages)} arquivos PDF individuais em: {output_dir}")

    for matricula, page_indices in payslips_pages.items():
        writer = PdfWriter()
        if not page_indices:
            print(f"Aviso: Nenhuma página associada à matrícula {matricula}. Pulando.")
            continue

        print(f"  -> Criando PDF para Matrícula: {matricula} (Páginas: {[p+1 for p in page_indices]})")
        for page_index in page_indices:
             if 0 <= page_index < len(reader.pages):
                  writer.add_page(reader.pages[page_index])
             else:
                  print(f"Aviso: Índice de página inválido ({page_index}) para matrícula {matricula}. Pulando página.")

        if not writer.pages:
             print(f"Aviso: Nenhuma página válida adicionada para matrícula {matricula}. Pulando.")
             continue

        output_filename = f"{competence}-{matricula}.pdf"
        output_path = output_dir / output_filename

        try:
            # Encripta com a matrícula como senha
            writer.encrypt(user_password=str(matricula), owner_password=None)
        except Exception as e:
            print(f"Erro ao tentar encriptar PDF para matrícula {matricula}: {e}")
            continue # Pula este funcionário

        try:
            with open(output_path, "wb") as f_out:
                writer.write(f_out)
            # print(f"    -> Salvo e protegido: {output_path}") # Log opcional
            generated_files.append(str(output_path))
        except Exception as e:
            print(f"Erro ao tentar salvar PDF para matrícula {matricula}: {e}")

    print(f"\nProcessamento concluído.")
    print(f"Total de arquivos gerados com sucesso: {len(generated_files)}")
    if len(generated_files) < len(payslips_pages):
        print(f"Houve falhas ao gerar {len(payslips_pages) - len(generated_files)} arquivos.")
    return generated_files


# -- Bloco de Execução Principal/Teste (DEPOIS das definições das funções) --
if __name__ == '__main__':
    # Configure o caminho correto para o seu PDF de entrada
    input_pdf_path = Path(__file__).parent.parent / 'input_pdfs' / 'holerites_MAR2025_exemplo.pdf' # Ajuste o nome do arquivo se necessário
    output_folder_path = Path(__file__).parent.parent / 'output_payslips'
    competencia_atual = '032025' # Competência no formato MMAAAA

    print(f"Script de processamento de PDF iniciado.")
    print(f"Arquivo de entrada: {input_pdf_path}")
    print(f"Diretório de saída: {output_folder_path}")
    print(f"Competência: {competencia_atual}")

    if not input_pdf_path.exists():
        print(f"\nERRO CRÍTICO: Arquivo de entrada não encontrado em '{input_pdf_path}'")
        print("             Verifique o caminho e o nome do arquivo.")
    else:
        try:
            # Chama a função principal que orquestra tudo
            split_encrypt_pdf(str(input_pdf_path), str(output_folder_path), competencia_atual)
            print("\nExecução do script finalizada.")

        except Exception as e:
            # Captura qualquer erro inesperado durante a execução
            import traceback
            print(f"\nERRO INESPERADO durante a execução principal:")
            print(traceback.format_exc()) # Imprime o rastreamento completo do erro
