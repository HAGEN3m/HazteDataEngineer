# 🚀 Lección 03.B (Módulo 08): CI/CD &amp; DataOps para Pipelines: GitHub Actions, Validación de Terraform, Linting y Testing

&gt; **Propósito**: Implementar la filosofía **DataOps** mediante la automatización de integración y despliegue continuo (**CI/CD**) para pipelines de datos e infraestructura. Aprenderás a construir workflows de GitHub Actions para validación estática de código (Ruff, SQLFluff), análisis de seguridad e imprevistos en Terraform (`terraform plan`), y ejecución automatizada de pruebas unitarias/integración antes de autorizar Pull Requests.

---

## 📌 1\. ¿Qué es DataOps y por qué el CI/CD Tradicional No Basta?

**DataOps** es una disciplina enfocada en reducir el tiempo de ciclo de desarrollo, elevar la calidad de los datos y garantizar entregas continuas y confiables de analítica.

A diferencia del DevOps tradicional (donde el software compilado es determinista), en **DataOps** el código se ejecuta contra datos en vivo que cambian constantemente en volumen, velocidad y estructura.

```
       ┌─────────────────────────────────────────────────────────────┐
       │                       PLANO DE CÓDIGO                       │
       │   [ Git Repo ] ──&gt; [ CI: Lint / Test ] ──&gt; [ CD: Deploy ]   │
       └──────────────────────────────┬──────────────────────────────┘
                                      │ (Ejecuta transformaciones)
       ┌──────────────────────────────▼──────────────────────────────┐
       │                       PLANO DE DATOS                        │
       │   [ Raw Data ] ──&gt; [ Quality Gates ] ──&gt; [ Prod Tables ]    │
       └─────────────────────────────────────────────────────────────┘

```

### Principios Fundamentales de DataOps en CI/CD:

1. **Infraestructura e Integración Inmutable**: Todo código de pipeline (PySpark, dbt, SQL) y todo recurso de nube (S3, IAM) vive en control de versiones.
2. **Shift-Left Quality Control**: Atrapar errores de sintaxis, violaciones de tipos, vulnerabilidades de IAM o consultas SQL ineficientes **antes** de fusionar a la rama principal (`main`).
3. **Ambientes Efímeros de Pruebas (*Ephemeral Staging*)**: Probar cambios en aislamiento usando esquemas de base de datos o ubicaciones S3 temporales que se destruyen al cerrar el Pull Request.

---

## 🛡️ 2\. Linting &amp; Análisis Estático de Código: Python &amp; SQL

El primer paso de cualquier pipeline de CI/CD es garantizar que el código cumpla con los estándares de estilo, rendimiento y seguridad sin necesidad de ejecutar cómputo costoso.

### A. Python &amp; PySpark: Ruff &amp; Bandit

* **Ruff**: El linter/formatter extremadamente rápido escrito en Rust que reemplaza a `Flake8`, `Black`, `isort` y `pylint`.
* **Bandit**: Herramienta de análisis estático enfocada en detectar agujeros de seguridad en código Python (ej. contraseñas hardcodeadas, llamadas insecure `exec()`).

### B. SQL: SQLFluff

En Data Engineering, SQL es código de primera clase. **SQLFluff** garantiza que las consultas escritas para Snowflake, BigQuery, Redshift o Spark SQL sigan estándares estrictos.

```
# Ej. Configuración .sqlfluff para proyectos de datos
[sqlfluff]
dialect = sparksql
templater = dbt
rules = L001, L003, L010, L014

[sqlfluff:rules:capitalisation.keywords]
capitalisation_policy = upper

[sqlfluff:rules:capitalisation.identifiers]
capitalisation_policy = lower

```

---

## 🏗️ 3\. CI/CD para Infraestructura como Código (Terraform)

El despliegue automatizado de Terraform requiere un flujo de trabajo defensivo para evitar modificar infraestructura crítica accidentalmente.

### El Flujo "Plan en PR / Apply en Merge":

```
[ Pull Request Creado ]
       │
       ▼
 [ terraform fmt -check ] ──&gt; [ terraform validate ] ──&gt; [ tfsec / Checkov ]
       │
       ▼
 [ terraform plan ] ──&gt; (Comenta el plan detallado directamente en el PR)
       │
       ▼
 [ PR Aprobado &amp; Merge a main ]
       │
       ▼
 [ terraform apply -auto-approve ] ──&gt; (Aprovisiona cambios en Producción)

```

1. **Seguridad con `tfsec` / `checkov`**: Escanea archivos `.tf` en búsqueda de buckets S3 públicos, faltas de cifrado o permisos de IAM excesivos antes de ejecutar el plan.
2. **Visibilidad**: El bot de CI/CD debe comentar el resultado de `terraform plan` directamente en el PR para que los revisores humanos vean exactamente qué recursos se crearán (`+`), modificarán (`~`) o destruirán (`-`).

---

## ⚙️ 4\. Automatización con GitHub Actions: Pipeline de CI Completo

A continuación se presenta un workflow de GitHub Actions listo para producción (`.github/workflows/dataops_ci.yml`) que valida código Python, modelos SQL y recursos de Terraform:

```
name: DataOps &amp; Infrastructure CI

on:
  pull_request:
    branches: [ main, master ]
    paths:
      - 'pipelines/**'
      - 'terraform/**'
      - '.github/workflows/**'

jobs:
  python-lint-and-test:
    name: 🐍 Python &amp; PySpark Quality Gates
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Repo
        uses: actions/checkout@v4

      - name: Set up Python 3.12
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install Dependencies
        run: |
          python -m pip install --upgrade pip
          pip install ruff pytest polars pyarrow

      - name: Run Ruff Linter
        run: ruff check pipelines/

      - name: Run Ruff Formatter Check
        run: ruff format --check pipelines/

      - name: Run Unit Tests with PyTest
        run: pytest pipelines/tests/ -v

  terraform-ci:
    name: 🧱 Terraform Validation &amp; Security
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: ./terraform
    steps:
      - name: Checkout Repo
        uses: actions/checkout@v4

      - name: Setup HashiCorp Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: 1.7.0

      - name: Terraform Format Check
        run: terraform fmt -check

      - name: Terraform Init (Backend reconfigure)
        run: terraform init -backend=false

      - name: Terraform Validate
        run: terraform validate

      - name: Run Security Scanner (tfsec)
        uses: aquasecurity/tfsec-action@v1.0.0
        with:
          working_directory: ./terraform

```

---

## 🏋️‍♂️ Ejercicio Práctico Hands-On: Test Unitario Defensivo en PySpark/Polars para CI/CD

Los pipelines de CI deben probar las funciones de transformación con datasets de prueba pequeños en memoria (*In-Memory Fixtures*) sin requerir conexiones a clústeres reales.

A continuación se muestra una suite de prueba con `pytest` y `polars` lista para integrarse en el CI:

```
# File: pipelines/transforms/medallion_silver.py
import polars as pl

def clean_raw_telemetry(df_raw: pl.DataFrame) -&gt; pl.DataFrame:
    """Limpia lecturas de telemetría, descarta valores nulos y convierte unidades."""
    return (
        df_raw
        .filter(pl.col("device_id").is_not_null())
        .filter(pl.col("temperature_celsius").between(-50.0, 100.0))
        .with_columns(
            (pl.col("temperature_celsius") * 1.8 + 32).alias("temperature_fahrenheit")
        )
    )

# --------------------------------------------------------------------
# File: pipelines/tests/test_medallion_silver.py
# --------------------------------------------------------------------
import pytest
import polars as pl
from pipelines.transforms.medallion_silver import clean_raw_telemetry

def test_clean_raw_telemetry_valid_data():
    # Arrange: Dataset simulado de entrada
    raw_data = pl.DataFrame({
        "device_id": ["DEV_01", "DEV_02", None, "DEV_04"],
        "temperature_celsius": [20.0, -100.0, 25.0, 0.0]  # DEV_02 es un outlier anómalo
    })

    # Act: Ejecutar la transformación
    result_df = clean_raw_telemetry(raw_data)

    # Assert: Validar resultados esperados
    assert len(result_df) == 2  # Solo DEV_01 y DEV_04 deben sobrevivir
    assert "temperature_fahrenheit" in result_df.columns

    # Validar la conversión matemática de 20.0 C -&gt; 68.0 F
    dev_01_f = result_df.filter(pl.col("device_id") == "DEV_01")["temperature_fahrenheit"][0]
    assert dev_01_f == pytest.approx(68.0)

def test_clean_raw_telemetry_empty_input():
    # Arrange: Schema válido pero DataFrame vacío
    empty_schema = {
        "device_id": pl.String,
        "temperature_celsius": pl.Float64
    }
    empty_df = pl.DataFrame(schema=empty_schema)

    # Act
    result_df = clean_raw_telemetry(empty_df)

    # Assert
    assert len(result_df) == 0
    assert "temperature_fahrenheit" in result_df.columns

```

---

## 🧠 Checkpoint de Autoevaluación

1. ¿En qué se diferencia la filosofía **DataOps** del CI/CD de software tradicional respecto al plano de cómputo vs. plano de datos?
2. ¿Por qué se debe ejecutar `terraform plan` durante la etapa de Pull Request y `terraform apply` solo tras la fusión a la rama principal?
3. ¿Qué rol cumplen herramientas como **Ruff** y **SQLFluff** en la prevención de fallas antes del despliegue?
4. ¿Por qué los tests unitarios de transformaciones de datos deben diseñarse con DataFrames pequeños en memoria (*Fixtures*) en lugar de conectarse al Data Lake de producción?