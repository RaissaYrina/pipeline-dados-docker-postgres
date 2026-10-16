# Pipeline da Cotação do Dólar (Banco Central) com Python, Docker e PostgreSQL

> Pipeline ETL que coleta a cotação diária do dólar na API SGS do Banco Central, converte os dados para os tipos corretos e grava em um PostgreSQL rodando em Docker, sem duplicar registros.

## 🎯 Objetivo
Coletar os 20 últimos registros (dias úteis) da cotação do dólar americano (venda, série 1 do SGS/BCB) e armazená-los em um banco PostgreSQL de forma **idempotente**: o pipeline pode ser executado várias vezes sem gerar dados duplicados.

## 📊 Principais resultados
- Carga histórica de **197 cotações** (jan/2026 –out/2026), conferida com `COUNT`, `MIN` e `MAX`
- Idempotência comprovada: reexecutar o pipeline mantém os mesmos 20 registros, sem duplicatas
- Banco de dados sobe com um único comando (`docker compose up -d`), com dados persistidos em volume nomeado

## 🛠️ Tecnologias
Python · Requests · psycopg2 · Docker · Docker Compose · PostgreSQL 16

## 🔄 Pipeline / Etapas
1. **Extract:** cotação do dólar (série 1 do SGS) via [API do Banco Central](https://dadosabertos.bcb.gov.br/dataset/1-taxa-de-cambio---livre---dolar-americano--venda---diario), consultando por período (`dataInicial`/`dataFinal`). Carga histórica de jan/2026 até hoje.
2. **Transform:** conversão da data de texto `dd/mm/aaaa` para `date` e do valor de texto para `Decimal` (precisão adequada para valores monetários)
3. **Load:** criação da tabela (caso não exista) e inserção no PostgreSQL com `ON CONFLICT (data) DO NOTHING`, usando a data como chave primária para garantir uma cotação por dia

## 🛡️ Robustez
O pipeline foi pensado para falhar de forma controlada:

- **Retry com backoff na API:** se a API do Banco Central falhar, o pipeline tenta até 3 vezes, esperando 2s e depois 4s entre as tentativas. Se todas falharem, ele para e mostra o erro.
- **Transação segura no banco:** se a carga falhar no meio, é feito `rollback`, então nenhum dado parcial fica no Postgres. A conexão é sempre encerrada (`finally`).
- **Idempotência:** a coluna `data` é chave primária e o insert usa `ON CONFLICT DO NOTHING`. Rodar o pipeline 2x seguidas mantém o mesmo número de linhas (testado).
- **Credenciais fora do código:** usuário e senha do banco vêm de variáveis de ambiente.
- **Período sem dados:** quando a API responde 404 (ex.: fim de semana, sem cotação), o pipeline não tenta de novo e para com uma mensagem clara, sem abrir conexão com o banco.

## 🧪 Testes de falha
Cenários forçados para validar a robustez:

| Cenário | Resultado esperado | ✅ |
|---|---|---|
| Lote com 1 linha válida + 1 inválida | Rollback: nenhuma linha gravada | ✅ |
| Banco fora do ar (`docker compose stop`) | `OperationalError` claro; volta a funcionar após `start` | ✅ |
| Pipeline executado 2x | Mesmo `COUNT` (idempotente) | ✅ |
| Período só com fim de semana | API retorna 404 → para sem retry e sem tocar no banco | ✅ |
| URL inválida | 3 tentativas com backoff e erro final | ✅ |

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
- `except` sem `raise` "engole" o erro: o pipeline parecia ter dado certo mesmo falhando
- `finally` roda sempre, então é o lugar certo para fechar a conexão, e não para a mensagem de sucesso
- Lendo a resposta de erro da API, descobri que o endpoint `ultimos/N` aceita no máximo 20 registros e passei a consultar por período
- Rollback garante atomicidade: ou o lote inteiro entra, ou nada entra (comprovado com `SELECT` no banco)
- A API do BC não devolve lista vazia para período sem dados, devolve 404. Só descobri testando
- Retry só faz sentido em erros temporários (timeout, 5xx); num 404 é tempo perdido

## 🚀 Próximos passos
- Estender o "sem retry" para os demais erros 4xx (hoje só o 404 é tratado)
- Ao agendar diariamente no Airflow, rever se período vazio deve ser erro ou aviso (fins de semana)

## 👩‍💻 Autora
Raissa — [LinkedIn](https://www.linkedin.com/in/raissamarusso/) · [GitHub](https://github.com/RaissaYrina)