# LicitaFácil BFF — Plataforma DataOps

> Backend-for-Frontend e pipeline de dados que captura, enriquece com IA e recomenda
> oportunidades de licitação pública para Microempreendedores Individuais (MEI),
> organizado como um monorepo de aplicações Python.

---

## 📌 Motivação

O **PNCP (Portal Nacional de Contratações Públicas)** publica diariamente milhares de
editais. Para um MEI, garimpar manualmente esse volume em busca de oportunidades
compatíveis com a sua atividade (CNAE) é inviável: o dado é volumoso, pouco
estruturado e cheio de campos aninhados.

O **LicitaFácil** resolve isso transformando o fluxo bruto do PNCP em recomendações
personalizadas:

- **Captura** os editais publicados no PNCP de forma idempotente e contínua.
- **Enriquece** cada edital com IA (Gemini), classificando-o por CNAE, gerando um
  resumo simplificado e um score de confiança.
- **Entrega** ao app do usuário apenas as oportunidades relevantes para os seus CNAEs
  e estados de interesse, ordenadas por confiança, valor ou prazo.

O resultado é uma plataforma que aproxima o pequeno empreendedor das compras públicas,
reduzindo a barreira de entrada nas licitações.

---

## ✅ Requisitos

- **Docker** e **Docker Compose** (forma recomendada de executar).
- Para rodar fora de containers: **Python 3.11+** e **Java 17** (necessário para o PySpark).
- Credenciais externas: **GEMINI_API_KEY**, **SUPABASE_URL**, **SUPABASE_KEY** e acesso ao **MongoDB**.

---

## ⚙️ Configuração

Copie o template e preencha as variáveis:

```bash
cp .env.example .env
```

Variáveis principais (`libs/common/config.py` define os defaults e a validação):

| Variável | Descrição | Default |
|----------|-----------|---------|
| `PNCP_BASE_URL` | Base da API PNCP | `https://pncp.gov.br/api/consulta` |
| `MONGO_URI` | Conexão MongoDB | *(obrigatória)* |
| `MONGO_DATABASE` | Database da Bronze | `pncp_db` |
| `MONGO_COLLECTION` | Coleção da Bronze | `contratacoes` |
| `KAFKA_BOOTSTRAP_SERVERS` | Brokers Kafka | `localhost:9092` |
| `KAFKA_BRONZE_TOPIC` | Tópico da Bronze | `bronze_contratacoes` |
| `GEMINI_API_KEY` | Chave do Gemini (Silver) | *(obrigatória p/ Silver)* |
| `SUPABASE_URL` / `SUPABASE_KEY` | Projeto Supabase | *(obrigatórias)* |
| `ICEBERG_WAREHOUSE_PATH` | Diretório do warehouse Iceberg | `/tmp/iceberg-warehouse` |
| `ICEBERG_DATABASE` / `ICEBERG_TABLE` | Namespace/tabela Silver | `pncp_silver` / `editais_enriched` |
| `SPARK_CHECKPOINT_DIR` | Checkpoint do Spark Streaming | `/tmp/processor-checkpoint-silver` |
| `LOG_LEVEL` | Nível de log (ver Observabilidade) | `INFO` |

---

## 🚀 Como rodar

### Opção 1 — Stack completa com Docker Compose (recomendado)

Sobe Kafka, Zookeeper, MongoDB, Kafka UI, a API e o servidor + worker do Prefect:

```bash
docker-compose up -d --build
```

Serviços expostos:

- **Prefect UI** — http://localhost:4200 (orquestração e acompanhamento dos flows)
- **Kafka UI** — http://localhost:8080 (inspeção de tópicos e mensagens)
- **API (Gold)** — http://localhost:8000 (`/health`, `/api/v1/...` e Swagger em `/docs`)
- **MongoDB** — localhost:27017 (armazenamento Bronze)

### Opção 2 — Executar pipelines manualmente

Com a infra de pé, dispare os flows pelo Prefect ou rode os apps diretamente:

```bash
# Bronze para um intervalo de datas (AAAAMMDD)
docker exec pncp-prefect-worker python run_bronze.py 20260101 20260105

# Via orquestrador Prefect (one-shot)
python orchestrate_prefect.py bronze      # só Bronze
python orchestrate_prefect.py silver      # só Silver
python orchestrate_prefect.py             # pipeline completo (Bronze + Silver)

# Apps individualmente (requer infra + variáveis no ambiente)
python apps/ingestion/src/main.py         # Bronze
python apps/processor/src/main.py         # Silver (Spark Streaming)
python apps/maintenance/src/main.py       # Scheduler de manutenção
```

### Deployments e agendamento (Prefect)

- **`bronze-diario`** (`bronze_pipeline`) — Cron `0 7 * * *` (07h diariamente)
- **`pipeline-completo-diario`** (`full_pipeline`) — Cron `0 7 * * *`
- **`silver-manual`** (`silver_pipeline`) — sob demanda

O flow Bronze faz *retry* (2 tentativas, 60s de intervalo); o Silver tem timeout de
3600s por execução.

---

## 🏛️ Arquitetura

O projeto segue a **arquitetura Medallion (Bronze / Silver / Gold)**, com componentes
transversais de orquestração e manutenção.

![Arquitetura do LicitaFácil — camadas Bronze, Silver e Gold](docs/assets/arquitetura-visao-geral.png)

A camada **Bronze** (`apps/ingestion`) captura o dado cru do PNCP, aplica uma
normalização leve e o persiste no **MongoDB** — um document store que acomoda o formato
semiestruturado e mutável do PNCP, com *upsert* por `numero_controle_pncp` para garantir
idempotência (reprocessar não duplica). Cada registro é publicado no **Apache Kafka**, que
desacopla ingestão de processamento e permite à Silver cair, reprocessar offsets e se
recuperar sem perder eventos.

A camada **Silver** (`apps/processor`) consome o Kafka em micro-batches com **Spark
Structured Streaming** (checkpoint para tolerância a falhas), deduplica e envia cada edital
ao **Gemini 2.5 Flash**, que classifica por CNAE, gera um resumo simplificado e um score de
confiança. O prompt restringe a IA a um catálogo válido e a resposta é validada contra os
CNAEs oficiais (códigos inventados são descartados), com *retry* para falhas transitórias.
O resultado é gravado em **Apache Iceberg** (histórico versionado, com snapshots e time
travel) e no **Supabase/PostgreSQL** (leitura rápida para o app).

A camada **Gold** (`apps/api`) é o BFF em **FastAPI**: cruza os CNAEs e estados do usuário
com as oportunidades enriquecidas e devolve recomendações ordenadas por confiança, valor ou
prazo, com autenticação via **JWT** e isolamento por linha (RLS) no PostgreSQL/Supabase.

O componente **Transversal** (`apps/maintenance` + `orchestrate_prefect.py`) usa o
**Prefect** para orquestrar e agendar os flows (cron, retries, timeouts) e roda jobs de
manutenção do data lake Iceberg (compactação e expiração de snapshots) e de analytics.

---

## 📁 Estrutura do monorepo

```
licitafacil-bff/
├── apps/
│   ├── ingestion/        # Bronze — captura PNCP → MongoDB + Kafka
│   │   └── src/{main.py, core/config.py, services/, repositories/}
│   ├── processor/        # Silver — Spark streaming + Gemini → Iceberg + Supabase
│   │   └── src/{main.py, core/config.py, services/, repositories/}
│   ├── api/              # Gold — FastAPI (recomendações, auth)
│   │   └── src/{main.py, core/, api/v1/routes/, db/, repositories/, services/}
│   └── maintenance/      # Transversal — manutenção Iceberg + analytics agendados
│       └── src/{main.py, core/config.py, services/, cronjob/}
├── libs/
│   ├── clients/          # PNCPClient (cliente da API PNCP)
│   └── common/           # Settings base, KafkaProducer
├── docs/                 # Documentação (ver docs/LicitaFacil-DataOps.md)
├── orchestrate_prefect.py# Flows e deployments do Prefect
├── run_bronze.py         # Execução manual da Bronze (por intervalo de datas)
├── docker-compose.yml    # Stack completa (Kafka, Mongo, Prefect, API…)
├── Dockerfile            # Imagem do worker Prefect (Python + Java + Spark)
├── pyproject.toml        # Metadados e ferramentas (ruff, mypy, pytest)
└── .env.example          # Template de variáveis de ambiente
```

---

## 🖼️ Capturas do pipeline em execução

**Bronze — dados crus no MongoDB e eventos no Kafka**

![Banco MongoDB com os editais crus da camada Bronze](docs/assets/mongodb.png)
![Tópico bronze_contratacoes no Kafka — cada mensagem é um edital](docs/assets/kafka.png)

**Silver — processamento orquestrado e gravação no Supabase**

![Pipeline Silver rodando no Prefect e gravando no Supabase](docs/assets/prefect_supabase.png)

**Gold — API e dados servidos ao app**

![Documentação Swagger dos endpoints de opportunities](docs/assets/swagger_opportunities.png)
![Tabelas da camada Gold no Supabase](docs/assets/table_supa.png)

**Orquestração — deployments e execução no Prefect**

![Os três deployments do pipeline registrados no Prefect](docs/assets/deployments_prefect.png)
![Execução de um flow no Prefect com as tasks concluídas](docs/assets/run_prefect.png)
