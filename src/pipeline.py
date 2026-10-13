import os
import requests
import psycopg2
from dotenv import load_dotenv
from datetime import datetime
from decimal import Decimal

load_dotenv()

URL_DADOS_DOLAR = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.1/dados/ultimos/20?formato=json"

def extract():
    """
    Busca o dado da API do Banco Central do Brasil sobre o valor do dólar.
    """
    response = requests.get(URL_DADOS_DOLAR)
    response.raise_for_status()  # lança exceção se erro (4xx, 5xx)
    dados = response.json()      # já vira lista de dicionários!
    return dados

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
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        dbname=os.getenv("POSTGRES_DB"),
    )
    print("Conectado!")

    cur = conn.cursor()      
    cur.execute("CREATE TABLE IF NOT EXISTS cotacao_dolar (data date PRIMARY KEY, valor numeric);")
    cur.executemany(
        "INSERT INTO cotacao_dolar (data, valor) VALUES (%s, %s) ON CONFLICT (data) DO NOTHING;",
        linhas,
    )
    conn.commit()            
    cur.close()
    conn.close()
    
    print("Dados salvos no Banco!")
    

if __name__ == "__main__":
    dados = extract()
    linhas = transform(dados)
    load(linhas)
    print(f"{len(linhas)} linhas processadas")