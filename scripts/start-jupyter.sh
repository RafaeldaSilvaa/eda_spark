#!/bin/bash
# spark-eda Jupyter Notebook startup script
set -e

echo "========================================"
echo "  spark-eda Jupyter Notebook"
echo "========================================"
echo ""
echo "  Java:    $(java -version 2>&1 | head -1)"
echo "  Python:  $(python --version 2>&1)"
echo "  PySpark: $(python -c 'import pyspark; print(pyspark.__version__)' 2>/dev/null || echo 'not found')"
echo "  spark_eda: $(python -c 'import spark_eda; print(spark_eda.__version__)' 2>/dev/null || echo 'not found')"
echo ""
echo "  Start coding with:"
echo "    from pyspark.sql import SparkSession"
echo "    import spark_eda"
echo ""
echo "    spark = SparkSession.builder \\"
echo "        .master('local[*]') \\"
echo "        .appName('eda') \\"
echo "        .getOrCreate()"
echo ""
echo "    report = spark_eda.analyze(df)"
echo "========================================"
echo ""

exec jupyter notebook \
    --ip=0.0.0.0 \
    --port=8888 \
    --no-browser \
    --allow-root \
    --NotebookApp.token='' \
    --NotebookApp.password='' \
    --NotebookApp.notebook_dir=/home/jovyan/work/notebooks
