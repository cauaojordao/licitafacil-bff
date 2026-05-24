# PNCP ETL

Projeto de ETL desenvolvido em Python para consumir dados da API do PNCP, transformar os registros e salvar os dados no MongoDB Atlas.

## Objetivo

Extrair dados públicos de contratações a partir da API do PNCP, tratar os dados e persisti-los em uma base NoSQL.

## Endpoint utilizado

`GET /v1/contratacoes/publicacao`

Parâmetros utilizados:
- `dataInicial`
- `dataFinal`
- `codigoModalidadeContratacao`
- `pagina`

## Estrutura do projeto

```text
pncp_etl/
├── src/
│   ├── config/
│   │   └── settings.py
│   ├── extract/
│   │   └── pncp_extractor.py
│   ├── transform/
│   │   └── pncp_transformer.py
│   ├── load/
│   │   └── mongodb_loader.py
│   └── pipeline/
│       └── etl_pipeline.py
├── .env
├── main.py
├── requirements.txt
└── README.md
```
## Tecnologias utilizadas

- `Python`
- `Requests`
- `PyMongo`
- `MongoDB Atlas`
- `python-dotenv`

## Como executar

### 1. Clonar o repositório
``` git
git clone https://github.com/JoaoLucasmcS/pncp_etl
```
``` cmd
cd pncp_etl
```

### 2. Criar o ambiente virtual
``` python
python -m venv .venv
```
### 3. Ativar o ambiente virtual

No PowerShell:
``` python
.venv\Scripts\Activate.ps1
```

No CMD: 
``` python
.venv\Scripts\activate.bat
```

### 4. Instalar as dependências
``` python
pip install -r requirements.txt
```

### 5. Criar o arquivo .env
``` dotenv
PNCP_BASE_URL=https://pncp.gov.br/api/consulta
MONGO_URI=mongodb+srv://SEU_USUARIO:SUA_SENHA@SEU_CLUSTER.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0
MONGO_DATABASE=pncp_db
MONGO_COLLECTION=contratacoes
```

### 6. Executar o projeto
``` python
python main.py
```

### Exemplo de saída
``` 
ETL executado com sucesso.
Registros extraídos: 20
Registros transformados: 20
Registros processados no MongoDB: 20
```
### Observações
O projeto faz paginação automática da API.
Os dados são tratados antes da carga.
A persistência no MongoDB é feita com upsert para evitar duplicidade.