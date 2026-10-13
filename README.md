# Pipeline da Cotação do Dólar (Banco Central) com Python, Docker e PostgreSQL

> Pipeline ETL que coleta a cotação diária do dólar na API SGS do Banco Central, converte os dados para os tipos corretos e grava em um PostgreSQL rodando em Docker, sem duplicar registros.

## 🎯 Objetivo
Coletar os 20 últimos registros (dias úteis) da cotação do dólar americano (venda, série 1 do SGS/BCB) e armazená-los em um banco PostgreSQL de forma **idempotente**: o pipeline pode ser executado várias vezes sem gerar dados duplicados.

## 📊 Principais resultados
- 20 cotações extraídas da API e carregadas no PostgreSQL em uma única execução
- Idempotência comprovada: reexecutar o pipeline mantém os mesmos 20 registros, sem duplicatas
- Banco de dados sobe com um único comando (`docker compose up -d`), com dados persistidos em volume nomeado

## 🛠️ Tecnologias
Python · Requests · psycopg2 · Docker · Docker Compose · PostgreSQL 16

## 🔄 Pipeline / Etapas
1. **Extract:** requisição à [API SGS do Banco Central](https://api.bcb.gov.br/dados/serie/bcdata.sgs.1/dados/ultimos/20?formato=json), que retorna uma lista JSON de `{data, valor}`
2. **Transform:** conversão da data de texto `dd/mm/aaaa` para `date` e do valor de texto para `Decimal` (precisão adequada para valores monetários)
3. **Load:** criação da tabela (caso não exista) e inserção no PostgreSQL com `ON CONFLICT (data) DO NOTHING`, usando a data como chave primária para garantir uma cotação por dia

## 🗄️ Modelo de dados
| Coluna | Tipo | Descrição |
|---|---|---|
| `data` | `date` (PK) | Data da cotação |
| `valor` | `numeric` | Cotação do dólar (venda) em R$ |

## 📁 Estrutura do projeto
```
├── src/
│   └── pipeline.py        # extract, transform e load
├── .env.example           # modelo das variáveis de ambiente
├── .gitignore
├── docker-compose.yml     # serviço PostgreSQL + volume
├── requirements.txt
└── README.md
```

## ▶️ Como executar
**Pré-requisitos:** Docker e Python 3 instalados.

```bash
# 1. Clonar o repositório
git clone https://github.com/RaissaYrina/pipeline-dados-docker-postgres.git
cd pipeline-dados-docker-postgres

# 2. Criar o .env a partir do modelo (e preencher usuário, senha e banco)
cp .env.example .env

# 3. Subir o PostgreSQL
docker compose up -d

# 4. Criar e ativar o ambiente virtual
python -m venv .venv
source .venv/Scripts/activate   # Windows (Git Bash)
# source .venv/bin/activate     # Linux/Mac

# 5. Instalar dependências e rodar o pipeline
pip install -r requirements.txt
python src/pipeline.py
```

**Conferir o resultado no banco** (use o usuário e o banco definidos no seu `.env`):
```bash
docker compose exec db psql -U SEU_USUARIO -d SEU_BANCO -c "SELECT * FROM cotacao_dolar;"
```

## 📚 O que aprendi
- Docker e Docker Compose: imagem, container, volume nomeado e a diferença entre `down` e `down -v`
- Conexão e interação com banco de dados via Python (psycopg2)
- ETL na prática e idempotência com chave primária + `ON CONFLICT`
- Diagnóstico de erros: logs de container e códigos HTTP da API

## 🚀 Próximos passos
- Buscar o histórico completo usando os parâmetros `dataInicial` e `dataFinal` da API
- Criar a tabela automaticamente na inicialização do container, com script SQL
- Rodar o pipeline também em container
- Agendar a execução diária com Airflow

## 👩‍💻 Autora
Raissa — [LinkedIn](https://www.linkedin.com/in/raissamarusso/) · [GitHub](https://github.com/RaissaYrina)