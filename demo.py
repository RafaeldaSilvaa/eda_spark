"""Demo spark_eda — análise completa em um DataFrame de 500 registros.

Uso:
    python demo.py

Requer PySpark (e Java 17+). Se JAVA_HOME não estiver definido,
o script tenta detectar automaticamente.
"""

from __future__ import annotations

import os
import sys
import subprocess
from pathlib import Path


def _find_java() -> str | None:
    """Tenta localizar o Java no sistema."""
    java_home = os.environ.get("JAVA_HOME")
    if java_home:
        java_bin = Path(java_home) / "bin" / "java.exe"
        if java_bin.is_file():
            return str(java_bin)

    # Lugares comuns no Windows
    candidates = [
        r"C:\Program Files\Java\jdk-17\bin\java.exe",
        r"C:\Program Files\Java\jdk-21\bin\java.exe",
        r"C:\Program Files\Java\jdk-11\bin\java.exe",
        r"C:\Program Files\Eclipse Adoptium\jdk-17.0.14.7-hotspot\bin\java.exe",
        r"C:\Program Files\Eclipse Adoptium\jdk-21.0.6.7-hotspot\bin\java.exe",
        r"C:\Program Files\Microsoft\jdk-17.0.14.7-hotspot\bin\java.exe",
    ]
    for path in candidates:
        if Path(path).is_file():
            return path

    # Tenta no PATH
    try:
        result = subprocess.run(["where", "java"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip().splitlines()[0]
    except Exception:
        pass

    return None


def _setup_env() -> None:
    """Configura JAVA_HOME se necessário."""
    if "JAVA_HOME" in os.environ:
        return

    java_bin = _find_java()
    if java_bin is None:
        print("=" * 60)
        print("Java não encontrado.")
        print()
        print("Instale o JDK 17+ e defina JAVA_HOME:")
        print()
        print("  $env:JAVA_HOME = 'C:\\Program Files\\Java\\jdk-17'")
        print("  python demo.py")
        print()
        print("Ou baixe de: https://adoptium.net/")
        print("=" * 60)
        sys.exit(1)

    java_home = str(Path(java_bin).resolve().parent.parent)
    os.environ["JAVA_HOME"] = java_home
    print(f"JAVA_HOME detectado: {java_home}")


def main() -> None:
    _setup_env()

    from datetime import date, timedelta
    from random import choice, gauss, randint, random, seed

    from pyspark.sql import SparkSession, DataFrame
    from pyspark.sql.types import (
        BooleanType,
        DateType,
        DoubleType,
        IntegerType,
        StringType,
        StructField,
        StructType,
    )

    import spark_eda

    # ── 1. Spark Session ─────────────────────────────────────────────
    print("\n[1/6] Iniciando Spark...")
    spark: SparkSession = (
        SparkSession.builder
        .master("local[*]")
        .appName("spark_eda_demo")
        .config("spark.sql.shuffle.partitions", "4")
        .getOrCreate()
    )

    # ── 2. DataFrame sintético (500 registros) ───────────────────────
    print("[2/6] Gerando 500 registros sintéticos...")
    seed(42)

    schema: StructType = StructType([
        StructField("id", IntegerType(), nullable=False),
        StructField("nome", StringType(), nullable=True),
        StructField("idade", IntegerType(), nullable=True),
        StructField("salario", DoubleType(), nullable=True),
        StructField("departamento", StringType(), nullable=False),
        StructField("data_admissao", DateType(), nullable=True),
        StructField("ativo", BooleanType(), nullable=False),
        StructField("score", DoubleType(), nullable=True),
    ])

    deps = ["Engenharia", "Marketing", "Vendas", "RH", "TI", "Financeiro"]
    nomes = [
        "Ana Silva", "Carlos Santos", None, "Diana Oliveira", "Eduardo Lima",
        "Fernanda Costa", "Gabriel Souza", "Helena Pereira", None, "João Martins",
    ]
    data_base = date(2020, 1, 1)

    data: list[tuple] = []
    for i in range(500):
        nome = nomes[i % len(nomes)]
        idade = randint(18, 65) if random() > 0.08 else None
        salario = round(gauss(5000, 2000), 2) if random() > 0.05 else None
        dept = choice(deps)
        dias = randint(0, 2000)
        adm = data_base + timedelta(days=dias) if random() > 0.12 else None
        ativo = choice([True, False])
        score = round(gauss(0.7, 0.15), 3) if random() > 0.1 else None
        data.append((i, nome, idade, salario, dept, adm, ativo, score))

    df: DataFrame = spark.createDataFrame(data, schema=schema)

    # ── 3. Análise EDA ───────────────────────────────────────────────
    print("[3/6] Executando spark_eda.analyze()...")
    report = spark_eda.analyze(df)

    # ── 4. Qualidade ─────────────────────────────────────────────────
    print("[4/6] Executando spark_eda.assess_quality()...")
    quality = spark_eda.assess_quality(df)
    print(f"\n  Quality Score: {quality.overall:.1f}/100")
    if quality.top_penalizers:
        p = quality.top_penalizers[0]
        print(f"  Top penalizer: {p.name} ({p.severity}) — score={p.score:.2f}")

    # ── 5. AI Commentary (se disponível) ────────────────────────────
    print("[5/6] Verificando AI Commentary...")
    if report.commentary:
        print(f"\n  Executive Analysis:")
        print(f"  {report.commentary.executive_analysis}")
    else:
        print("  (indisponível — OmniRoute não está rodando)")

    # ── 6. Export ────────────────────────────────────────────────────
    print("[6/6] Exportando relatórios...")

    html = report.to_html()
    Path("demo_report.html").write_text(html, encoding="utf-8")
    print(f"  HTML: {Path('demo_report.html').resolve()}")

    js = report.to_json()
    Path("demo_report.json").write_text(js, encoding="utf-8")
    print(f"  JSON: {Path('demo_report.json').resolve()}")

    # Preview no terminal
    print("\n" + "=" * 60)
    print("Resumo do Relatório")
    print("=" * 60)
    print(report)

    spark.stop()
    print("\n✅ Demo concluída com sucesso!")


if __name__ == "__main__":
    main()
