#!/bin/bash
set -e

# Auto-configure Spark environment.
# Safety net: checks PySpark works and installs deps if missing.

if python -c "import pyspark" 2>/dev/null; then
    echo "[entrypoint] PySpark is available"
else
    echo "[entrypoint] PySpark not found — auto-configuring..."

    if ! command -v java &>/dev/null; then
        echo "[entrypoint] Java not found, installing openjdk-21-jre-headless..."
        apt-get update -qq && apt-get install -y -qq --no-install-recommends openjdk-21-jre-headless
        rm -rf /var/lib/apt/lists/*
    fi

    if [ -z "$JAVA_HOME" ]; then
        JAVA_HOME=$(dirname "$(dirname "$(readlink -f "$(which java)")")")
        export JAVA_HOME
        echo "[entrypoint] Auto-detected JAVA_HOME=$JAVA_HOME"
    fi

    echo "[entrypoint] Installing PySpark..."
    pip install --no-cache-dir pyspark
fi

exec "$@"