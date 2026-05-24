FROM python:3.11.12-slim

WORKDIR /app

# Instala dependências antes de copiar o código fonte
# para aproveitar o cache de camadas do Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia apenas o necessário para execução
COPY src/ src/
COPY main.py .
COPY orchestrate_prefect.py .

# Executa como usuário não-root (segurança)
RUN adduser --disabled-password --gecos "" appuser
USER appuser

CMD ["python", "orchestrate_prefect.py"]
