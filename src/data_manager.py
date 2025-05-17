# src/data_manager.py
import pandas as pd
from pathlib import Path

DATA_FILE = Path(__file__).parent.parent / 'data' / 'vilaboa.csv'

def load_employee_data(file_path=DATA_FILE):
    """Carrega os dados dos funcionários do CSV."""
    try:
        df = pd.read_csv(file_path, dtype={'Matricula': str,'Nome': str ,'CelularWhatsapp': str})
        # Cria dicionários para busca rápida
        nome_to_phone = df.set_index('Nome')['CelularWhatsapp'].to_dict()
        matricula_to_phone = df.set_index('Matricula')['CelularWhatsapp'].to_dict()
        phone_to_matricula = df.set_index('CelularWhatsapp')['Matricula'].to_dict()
        return nome_to_phone, matricula_to_phone, phone_to_matricula
    except FileNotFoundError:
        print(f"Erro: Arquivo de dados não encontrado em {file_path}")
        return None, None
    except Exception as e:
        print(f"Erro ao ler o arquivo de dados: {e}")
        return None, None

# Carrega os dados quando o módulo é importado (pode ser otimizado se necessário)
NOME_TO_PHONE, MATRICULA_TO_PHONE, PHONE_TO_MATRICULA = load_employee_data()
def get_nome(nome: str):
    """Busca o número de WhatsApp pela matrícula."""
    if NOME_TO_PHONE is None:
        print("Erro: Dados dos funcionários não carregados.")
        return None
    return NOME_TO_PHONE.get(str(nome)) # Garante que o nome seja string

def get_whatsapp_number(matricula: str):
    """Busca o número de WhatsApp pela matrícula."""
    if MATRICULA_TO_PHONE is None:
        print("Erro: Dados dos funcionários não carregados.")
        return None
    return MATRICULA_TO_PHONE.get(str(matricula)) # Garante que a matrícula seja string

def get_matricula_by_whatsapp(phone_number: str):
    """Busca a matrícula pelo número de WhatsApp."""
    if PHONE_TO_MATRICULA is None:
        print("Erro: Dados dos funcionários não carregados.")
        return None
    # Normalizar o número recebido para garantir correspondência
    if not phone_number.startswith('whatsapp:'):
        phone_number = f"whatsapp:{phone_number}"
    return PHONE_TO_MATRICULA.get(phone_number)

# Exemplo de uso
if __name__ == '__main__':
    if MATRICULA_TO_PHONE:
        print("Dados carregados.")
        matricula_teste = '123456'
        celular = get_whatsapp_number(matricula_teste)
        print(f"Celular para matrícula {matricula_teste}: {celular}")

        celular_teste = 'whatsapp:+5521988887777'
        matricula = get_matricula_by_whatsapp(celular_teste)
        print(f"Matrícula para celular {celular_teste}: {matricula}")
    else:
        print("Falha ao carregar dados.")
