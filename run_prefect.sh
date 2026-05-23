#!/bin/bash
set -e

echo "🎛️  PNCP MEI Pipeline — Prefect Orchestrator"
echo ""

# ───────────────────────────────────────────────────────────────────────────
# Validações
# ───────────────────────────────────────────────────────────────────────────

if [ ! -f ".env" ]; then
    echo "❌ Arquivo .env não encontrado"
    echo "   Execute: cp .env.example .env"
    exit 1
fi

# Ativar venv
if [ -z "$VIRTUAL_ENV" ]; then
    if [ -f ".venv/bin/activate" ]; then
        source .venv/bin/activate
    else
        echo "❌ Ambiente virtual não encontrado"
        echo "   Execute: python -m venv .venv && source .venv/bin/activate"
        exit 1
    fi
fi

# ───────────────────────────────────────────────────────────────────────────
# Menu
# ───────────────────────────────────────────────────────────────────────────

echo "Escolha uma opção:"
echo "──────────────────────────────────────────────────────────"
echo "1) Executar uma vez (sem Prefect)"
echo "2) Executar com Prefect Server (dashboard + logs)"
echo "3) Iniciar deployment agendado (diário às 7h)"
echo "4) Parar todos os processos Prefect"
echo ""
read -p "Opção [1-4]: " option

case $option in
    1)
        echo ""
        echo "▶️  Executando pipeline uma vez..."
        echo ""

        # Subir Docker se não estiver rodando
        if ! docker-compose ps | grep -q "Up"; then
            echo "🐳 Iniciando Kafka + MongoDB..."
            docker-compose up -d
            sleep 30
        fi

        python orchestrate_prefect.py
        ;;

    2)
        echo ""
        echo "🚀 Iniciando Prefect Server..."
        echo ""

        # Subir Docker
        if ! docker-compose ps | grep -q "Up"; then
            echo "🐳 Iniciando Kafka + MongoDB..."
            docker-compose up -d
            sleep 30
        fi

        # Iniciar Prefect Server em background
        echo "📡 Iniciando servidor Prefect..."
        prefect server start &
        PREFECT_PID=$!

        # Aguardar servidor iniciar
        sleep 10

        echo ""
        echo "✅ Prefect Server rodando!"
        echo "   Dashboard: http://localhost:4200"
        echo ""
        echo "▶️  Executando pipeline com Prefect..."
        python orchestrate_prefect.py

        echo ""
        echo "✅ Pipeline concluído!"
        echo "   Veja os logs no dashboard: http://localhost:4200"
        echo ""
        read -p "Pressione Enter para parar o servidor Prefect..."

        kill $PREFECT_PID
        ;;

    3)
        echo ""
        echo "📅 Configurando deployment agendado..."
        echo ""

        # Subir Docker
        if ! docker-compose ps | grep -q "Up"; then
            echo "🐳 Iniciando Kafka + MongoDB..."
            docker-compose up -d
            sleep 30
        fi

        echo "🚀 Iniciando Prefect Server..."
        prefect server start &
        PREFECT_PID=$!
        sleep 10

        echo "📦 Criando deployment..."
        python orchestrate_prefect.py serve &
        SERVE_PID=$!

        echo ""
        echo "✅ Deployment criado e ativo!"
        echo "   Dashboard: http://localhost:4200"
        echo "   Agendamento: Diário às 7h"
        echo ""
        echo "🤖 O pipeline rodará automaticamente todos os dias."
        echo "   Pressione Ctrl+C para parar"
        echo ""

        # Aguardar Ctrl+C
        wait
        ;;

    4)
        echo ""
        echo "🛑 Parando processos Prefect..."
        pkill -f "prefect server" || true
        pkill -f "prefect agent" || true
        pkill -f "orchestrate_prefect" || true
        echo "✅ Processos parados"
        ;;

    *)
        echo "❌ Opção inválida"
        exit 1
        ;;
esac
