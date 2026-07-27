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
import platform
from pathlib import Path

_JAVA_EXE = "java.exe" if platform.system() == "Windows" else "java"


def _setup_env() -> None:
    """Configura JAVA_HOME a partir de argumento ou detecção automática."""
    # Aceita JAVA_HOME via argumento: python demo.py C:\Java\jdk-17
    if len(sys.argv) > 1:
        candidate = sys.argv[1]
        java_home = _resolve_java_home(candidate)
        if java_home:
            os.environ["JAVA_HOME"] = java_home
            print(f"JAVA_HOME (via arg): {java_home}")
            return
        print(f"Aviso: caminho informado não tem bin/{_JAVA_EXE}: {candidate}")

    # Já definido no ambiente
    env_home = os.environ.get("JAVA_HOME", "")
    if env_home:
        resolved = _resolve_java_home(env_home)
        if resolved:
            print(f"JAVA_HOME (via env): {resolved}")
            return
        print(f"Aviso: JAVA_HOME definido mas bin/{_JAVA_EXE} não encontrado: {env_home}")

    # Procura em lugares comuns
    for candidate in _CANDIDATES:
        resolved = _resolve_java_home(candidate)
        if resolved:
            os.environ["JAVA_HOME"] = resolved
            print(f"JAVA_HOME (detectado): {resolved}")
            return

    # Tenta no PATH
    path_java = _find_java_on_path()
    if path_java:
        resolved = str(Path(path_java).resolve().parent.parent)
        if _resolve_java_home(resolved):
            os.environ["JAVA_HOME"] = resolved
            print(f"JAVA_HOME (via PATH): {resolved}")
            return

    print("=" * 60)
    print("Java não encontrado.")
    print()
    print("Instale o JDK 17+ (https://adoptium.net/) e configure:")
    print()
    print("  $env:JAVA_HOME = 'C:\\Program Files\\Java\\jdk-17'")
    print("  python demo.py")
    print()
    print("Ou passe o caminho como argumento:")
    print()
    print("  python demo.py C:\\Program Files\\Java\\jdk-17")
    print("=" * 60)
    sys.exit(1)


_CANDIDATES: list[str] = [
    r"C:\Program Files\Java\jdk-19",
    r"C:\Program Files\Java\jdk-21",
    r"C:\Program Files\Java\jdk-11",
    r"C:\Program Files\Eclipse Adoptium\jdk-17.0.14.7-hotspot",
    r"C:\Program Files\Eclipse Adoptium\jdk-21.0.6.7-hotspot",
    r"C:\Program Files\Microsoft\jdk-17.0.14.7-hotspot",
]


def _resolve_java_home(candidate: str) -> str | None:
    """Valida se candidate contém bin/java e retorna o path."""
    java_exe = Path(candidate) / "bin" / _JAVA_EXE
    return candidate if java_exe.is_file() else None


def _find_java_on_path() -> str | None:
    """Retorna o caminho completo do java.exe encontrado no PATH."""
    try:
        result = subprocess.run(
            ["where", "java"], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip().splitlines()[0]
    except Exception:
        pass
    return None


def _diagnose() -> None:
    """Mostra info do ambiente pra debug."""
    import subprocess as _sp

    print("\n── Diagnóstico ──")
    jh = os.environ.get("JAVA_HOME", "(não definido)")
    print(f"  JAVA_HOME: {jh}")
    java_bin = Path(jh) / "bin" / _JAVA_EXE if jh != "(não definido)" else None
    if java_bin and java_bin.is_file():
        try:
            ver = _sp.run(
                [str(java_bin), "-version"],
                capture_output=True, text=True, timeout=10,
            )
            msg = ver.stderr or ver.stdout or "(sem output)"
            print(f"  Java version: {msg.strip().splitlines()[0]}")
        except Exception as e:
            print(f"  Java version: erro ao executar — {e}")
    else:
        print(f"  {_JAVA_EXE}: não encontrado")

    import pyspark
    print(f"  PySpark: {pyspark.__version__} ({pyspark.__file__})")
    import sys as _sys
    print(f"  Python: {_sys.version}")
    print("── Fim diagnóstico ──\n")


def main() -> None:
    _setup_env()
    _diagnose()

    from datetime import date, timedelta
    from random import choice, gauss, randint, random, seed

    # Configura PySpark antes de qualquer import do spark_eda
    import pyspark
    pyspark.SparkConf().set("spark.driver.host", "127.0.0.1")

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

    # ── 1. Spark Session ─────────────────────────────────────────────
    print("\n[1/6] Iniciando Spark...")
    spark: SparkSession = (
        SparkSession.builder
        .master("local[*]")
        .appName("spark_eda_demo")
        .config("spark.sql.shuffle.partitions", "4")
        .config("spark.driver.host", "127.0.0.1")
        .getOrCreate()
    )

    import spark_eda

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

    out = Path("reports")
    out.mkdir(exist_ok=True)

    from spark_eda.adapters.renderers import HTMLRenderer, JSONSerializer, TextRenderer

    html = HTMLRenderer.render_report(report)
    (out / "demo_report.html").write_text(html, encoding="utf-8")
    print(f"  HTML: {(out / 'demo_report.html').resolve()}")

    js = JSONSerializer.serialize_report(report)
    (out / "demo_report.json").write_text(js, encoding="utf-8")
    print(f"  JSON: {(out / 'demo_report.json').resolve()}")

    # Preview no terminal
    print("\n" + "=" * 60)
    print("Resumo do Relatório")
    print("=" * 60)
    print(TextRenderer.render_report(report))

    spark.stop()
    print("\n✅ Demo concluída com sucesso!")


if __name__ == "__main__":
    main()
