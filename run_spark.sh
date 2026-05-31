#!/bin/bash
# Executa scripts do projeto com o ambiente correto.
# Uso:
#   ./run_spark.sh              → spark_transformer.py (pipeline completo)
#   ./run_spark.sh main         → ingestão Bronze (main.py)
#   ./run_spark.sh silver       → streaming Silver
#   ./run_spark.sh chat         → Streamlit chat

set -e
cd "$(dirname "$0")"

# ── Java ──────────────────────────────────────────────────────────────────────
# O JAVA_HOME padrão aponta para um OpenJDK Homebrew que não existe.
# Usamos o Oracle JDK 17 instalado no sistema.
export JAVA_HOME=/Library/Java/JavaVirtualMachines/jdk-17.jdk/Contents/Home

if [ ! -f "$JAVA_HOME/bin/java" ]; then
    echo "❌ Java não encontrado em $JAVA_HOME"
    echo "   Instale o JDK 17: https://www.oracle.com/java/technologies/downloads/"
    exit 1
fi

echo "☕ Java: $($JAVA_HOME/bin/java -version 2>&1 | head -1)"

# ── Python (venv com PySpark 4.x instalado no 3.11) ──────────────────────────
PYTHON=./venv/bin/python3.11

if [ ! -f "$PYTHON" ]; then
    echo "❌ Python 3.11 não encontrado no venv"
    echo "   Execute: pip install pyspark>=3.5.0"
    exit 1
fi

echo "🐍 Python: $($PYTHON --version)"
echo "⚡ PySpark: $($PYTHON -c 'import pyspark; print(pyspark.__version__)')"
echo ""

# ── Executar ──────────────────────────────────────────────────────────────────
# Silencia os logs INFO/DEBUG do Spark para deixar só a saída do script.
export PYSPARK_PYTHON=$PYTHON
export SPARK_LOCAL_IP=127.0.0.1
export SPARK_LOCAL_HOSTNAME=localhost
export SPARK_SUBMIT_OPTS="-Dlog4j.rootCategory=WARN,console"

echo "🚀 Iniciando spark_transformer.py..."
echo "──────────────────────────────────────────────────────────"

case "${1:-spark}" in
    main)
        echo "▶  Ingestão Bronze (main.py)"
        $PYTHON main.py
        ;;
    silver)
        echo "▶  Streaming Silver"
        $PYTHON -m src.silver.run_silver_streaming
        ;;
    chat)
        echo "▶  Streamlit Chat"
        $PYTHON -m streamlit run src/chat/app.py
        ;;
    spark|"")
        $PYTHON -m src.transform.spark_transformer "$@"
        ;;
    *)
        echo "❌ Opção inválida: $1"
        echo "   Opções: main | silver | chat | spark (padrão)"
        exit 1
        ;;
esac
