import os
import requests
import psycopg2
from dotenv import load_dotenv
from datetime import datetime
from decimal import Decimal
import time

load_dotenv()

URL_DADOS_DOLAR = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.1/dados"

def extract(data_inicial, data_final, url=URL_DADOS_DOLAR, tentativas=3):
    """
    Busca o dado da API do Banco Central do Brasil sobre o valor do dólar.
    """
    params ={
        "formato": "json",
        "dataInicial": data_inicial,
        "dataFinal": data_final
    }
    
    for tentativa in range(1, tentativas + 1):
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 404:
                return []
            response.raise_for_status()  # lança exceção se erro (4xx, 5xx)
            dados = response.json()      # já vira lista de dicionários!
            return dados
        except requests.RequestException as e:
            print(f"Erro de conexão na tentativa {tentativa}: {e}")
            if tentativa < tentativas:
                time.sleep(1)
            else:
                raise
        except Exception as e:
            print(f"Erro ao extrair dados da API: {e}")
            raise

def transform(registros):
    """
    Recebe a lista de dicionários e transforma para uma lista de tuplas (data, valor).
    """
    tuplas =[]

    for registro in registros:
        data = datetime.strptime(registro["data"], "%d/%m/%Y").date()
        valor = Decimal(registro["valor"])
        tuplas.append((data, valor))

    return tuplas
    
    
def load(linhas):
    #realiza a conexão no banco de dados do postgres
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        dbname=os.getenv("POSTGRES_DB"),
    )
    print("Conectado!")
    cur = None
    try: 
        #cria um cursor para executar os comandos no banco de dados
        cur = conn.cursor()       
        #executa a criação da tabela se ela não existir
        cur.execute("CREATE TABLE IF NOT EXISTS cotacao_dolar (data date PRIMARY KEY, valor numeric);")
        # insere as linhas; datas já existentes são ignoradas (idempotente: pode rodar várias vezes)
        cur.executemany(
            "INSERT INTO cotacao_dolar (data, valor) VALUES (%s, %s) ON CONFLICT (data) DO NOTHING;",
            linhas,
        )
        #commita as alterações no banco
        conn.commit()        
        print("Dados salvos no Banco!")    
    except Exception as e:
        print(f"Erro ao salvar no banco: {e}")
        conn.rollback()
        raise

    finally:
        #fecha o cursor
        if cur: 
            cur.close()
        #encerra a conexão com o banco de dados
        conn.close()
        print("Conexão Encerrada")


if __name__ == "__main__":
    dados = extract("01/01/2026","15/10/2026")
    if not dados:
        raise ValueError("Nenhum dado encontrado na API pro periodo selecionado.")
    linhas = transform(dados)
    load(linhas)
    print(f"{len(linhas)} linhas processadas")