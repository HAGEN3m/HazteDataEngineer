# 🚀 Lección 02: Workflows de GitHub Actions para Testing Automático (Linters, Pytest, SQLFluff)

En la Lección 01 aprendimos los fundamentos de la cultura DataOps, la diferencia crítica con DevOps (el estado persistente de los datos) y por qué los 4 pilares aseguran despliegues continuos sin errores en producción.

Ahora daremos el paso práctico de automatización: **¿Cómo implementamos un "guardián robotizado" en el repositorio de GitHub que audite automáticamente cada Pull Request antes de que toque producción?**

En esta lección aprenderemos a configurar pipelines de CI/CD con GitHub Actions, integrando las tres herramientas estándar de testing en Data Engineering:
* **Linters de Python (`ruff` / `flake8`):** Para garantizar calidad de código Python, formateo estandarizado y prevención de errores de sintaxis.
* **`pytest`:** Para ejecutar pruebas unitarias automatizadas sobre funciones de transformación de datos (Pandas, Polars, PySpark).
* **`SQLFluff`:** El linter de SQL líder de la industria para auditar dialéctica, formato y antipatrones en consultas y modelos de dbt.

---

## 1. ¿Qué es GitHub Actions y cómo funciona un Workflow?

GitHub Actions es la plataforma de Integración y Despliegue Continuo (CI/CD) nativa de GitHub. Permite automatizar flujos de trabajo (*Workflows*) directamente dentro del repositorio cuando ocurren eventos como un `push` o la apertura de un `pull_request`.

```text
               ANATOMÍA DE UN WORKFLOW EN GITHUB ACTIONS
┌─────────────────────────────────────────────────────────────────┐
│ EVENTO TRIGGER (ej. `on: pull_request` a la rama `main`)        │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│ JOB: `data-quality-ci` (Corre en máquina virtual `ubuntu-latest`)│
├─────────────────────────────────────────────────────────────────┤
│ Steps (Pasos secuenciales):                                     │
│  1. `actions/checkout@v4` (Clona el repositorio)                │
│  2. `actions/setup-python@v5` (Instala Python 3.11)             │
│  3. Instalar dependencias (`pip install -r requirements.txt`)   │
│  4. Ejecutar Linter Python (`ruff check .`)                     │
│  5. Ejecutar Unit Tests (`pytest tests/`)                       │
│  6. Ejecutar Linter SQL (`sqlfluff lint models/`)               │
└─────────────────────────────────────────────────────────────────┘
```

### Componentes Clave:
* **Workflow:** Archivo de configuración escrito en YAML ubicado obligatoriamente en la ruta `.github/workflows/`.
* **Events (`on`):** Detonantes del flujo (ej. `pull_request`, `push`, ejecuciones programadas tipo cron).
* **Jobs:** Conjunto de pasos que se ejecutan en un servidor aislado (*Runner*).
* **Steps:** Tareas individuales que ejecutan comandos de terminal o acciones predefinidas de la comunidad.

---

## 2. La Suite de Testing de un Data Engineer Ssr

Para evitar que código sucio o consultas SQL ineficientes lleguen al Data Warehouse, nuestro pipeline de CI evalúa tres áreas:

```text
                        SUITE DE CI EN DATA ENGINEERING
                                       │
       ┌───────────────────────────────┼───────────────────────────────┐
       ▼                               ▼                               ▼
 1. LINTING PYTHON (ruff)     2. UNIT TESTING (pytest)       3. LINTING SQL (sqlfluff)
 • Estilo PEP8                • Lógica de transformación     • Formato de palabras clave
 • Inmune a errores de sintaxis• Manejo de casos de borde      • Evita `SELECT *`
 • Detección de imports nulos • Aserciones en DataFrames     • Compatibilidad dbt/Dialectos
```

### A. Linters de Python (`ruff`)
`ruff` es el linter de Python de extrema velocidad que reemplaza a `flake8`, `black` e `isort`. Detecta variables no utilizadas, imports desordenados y violaciones al estándar de estilo PEP8.

```bash
# Ejecución local en terminal
ruff check .
```

### B. Pruebas Unitarias de Transformación (`pytest`)
Con `pytest` probamos que nuestras funciones puras de transformación (limpieza de cadenas, cálculos de impuestos, parseo de fechas) reaccionen correctamente ante escenarios normales y datos anómalos:

```python
# tests/test_transformaciones.py
import pytest
import pandas as pd

def limpiar_monto_moneda(cadena_monto: str) -> float:
    if not cadena_monto:
        return 0.0
    # Remueve símbolos de moneda y convierte a float
    monto_limpio = cadena_monto.replace("$", "").replace(",", "").strip()
    return float(monto_limpio)

# Prueba Unitaria con Pytest
def test_limpiar_monto_moneda_valido():
    assert limpiar_monto_moneda("$ 1,250.50") == 1250.50

def test_limpiar_monto_moneda_vacio():
    assert limpiar_monto_moneda(None) == 0.0
```

### C. Linter de SQL para Data Warehousing (`SQLFluff`)
SQL no suele tener un compilador previo. Un error de sintaxis o una consulta mal formateada solo falla cuando se ejecuta en el Data Warehouse. SQLFluff analiza las consultas SQL y modelos de dbt antes de ejecutarlos.

```ini
# Configuración en .sqlfluff (Dialecto Snowflake / Postgres)
[sqlfluff]
dialect = postgres
templater = dbt

[sqlfluff:rules:capitalisation.keywords]
capitalisation_policy = upper # Exige palabras clave en MAYÚSCULAS (SELECT, FROM, WHERE)
```

**Ejemplo de corrección automática con SQLFluff:**

```sql
-- ❌ SQL Sucio que SQLFluff rechazará:
select id, name, amount from raw.sales where amount > 0;

-- 🟢 SQL Limpio corregido por SQLFluff:
SELECT
    id,
    name,
    amount
FROM raw.sales
WHERE amount > 0;
```

---

## 3. Configuración del Workflow Real (`.github/workflows/data_ci.yml`)

A continuación se muestra el archivo YAML completo de GitHub Actions que audita cualquier Pull Request hacia la rama `main`:

```yaml
name: Data Engineering Quality CI

on:
  pull_request:
    branches: [ "main" ]
  push:
    branches: [ "main" ]

jobs:
  data-pipeline-testing:
    name: Code & SQL Quality Checks
    runs-on: ubuntu-latest

    steps:
      - name: 1. Checkout del código
        uses: actions/checkout@v4

      - name: 2. Configurar Entorno Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: 3. Instalar Herramientas de Testing
        run: |
          python -m pip install --upgrade pip
          pip install ruff pytest sqlfluff pandas

      - name: 4. Ejecutar Linter de Python (Ruff)
        run: |
          echo "🔍 Auditando estilo de código Python con Ruff..."
          ruff check .

      - name: 5. Ejecutar Pruebas Unitarias (Pytest)
        run: |
          echo "🧪 Ejecutando suite de Unit Tests de transformaciones..."
          pytest tests/ --verbose

      - name: 6. Audit de Consultas SQL (SQLFluff)
        run: |
          echo "📊 Auditando sintaxis y estilo de modelos SQL..."
          sqlfluff lint models/ --dialect postgres
```

---

## 🏋️‍♂️ Práctica de la Lección 02

1. Ubicate en la carpeta `practica/modulo_08/` de tu repositorio local.
2. Creá el archivo `ej_02_github_actions_testing.py`.
3. Escribí un script Python que simule el Ejecutor de GitHub Actions (*Runner Simulator*) corriendo los pasos de `ruff`, `pytest` y `sqlfluff` sobre un fragmento de código:

```python
import sys

# 1. Código Python a evaluar
python_code_sample = """
def calcular_impuesto_neto(monto: float) -> float:
    if monto < 0:
        raise ValueError("El monto no puede ser negativo")
    return round(monto * 0.21, 2)
"""

# 2. Consulta SQL a evaluar
sql_code_sample = """
SELECT
    cliente_id,
    SUM(monto) AS total
FROM analytics.ventas
WHERE estado = 'COMPLETADA'
GROUP BY cliente_id;
"""

class GitHubActionsRunnerSimulator:
    def __init__(self):
        self.passed_steps = 0
        self.total_steps = 3

    def step_1_ruff_linter(self, py_code: str) -> bool:
        print("▶️ Step 1: Running Ruff Python Linter...")
        # Simulación de regla: No usar print desprolijos
        if "print(" in py_code:
            print("❌ RUFF ERROR: Remueva sentencias 'print' de depuración.")
            return False
        print("✅ Ruff: 0 errors found.")
        return True

    def step_2_pytest_runner(self) -> bool:
        print("\n▶️ Step 2: Running Pytest Unit Suite...")
        # Simulando test unitario
        try:
            # Test 1: Monto positivo
            assert round(100.0 * 0.21, 2) == 21.0
            # Test 2: Invariante
            assert round(0.0 * 0.21, 2) == 0.0
            print("✅ Pytest: 2 passed in 0.05s.")
            return True
        except AssertionError:
            print("❌ Pytest: Assertion Failed.")
            return False

    def step_3_sqlfluff_linter(self, sql_query: str) -> bool:
        print("\n▶️ Step 3: Running SQLFluff SQL Linter...")
        # Regla: Palabras clave deben estar en mayúsculas
        keywords_lower = ["select", "from", "where", "group by"]
        for kw in keywords_lower:
            if kw in sql_query:
                print(f"❌ SQLFLUFF LINT ERROR: Palabra clave '{kw}' debe estar en MAYÚSCULAS.")
                return False
        print("✅ SQLFluff: Code matches 'postgres' dialect rules.")
        return True

    def run_job(self):
        print("==================================================")
        print("🤖 GITHUB ACTIONS RUNNER: Job 'data-quality-ci'")
        print("==================================================\n")

        s1 = self.step_1_ruff_linter(python_code_sample)
        s2 = self.step_2_pytest_runner()
        s3 = self.step_3_sqlfluff_linter(sql_code_sample)

        if s1 and s2 and s3:
            print("\n🎉 WORKFLOW SUCCESS: All CI checks passed! PR is green for Merge.")
        else:
            print("\n💥 WORKFLOW FAILED: Check logs and fix errors before merging.")

# Ejecución de la prueba
runner = GitHubActionsRunnerSimulator()
runner.run_job()
```

4. Agregá comentarios al final del archivo respondiendo:
   * **Consigna A:** ¿Por qué es fundamental ejecutar SQLFluff en el pipeline de CI antes de autorizar el merge de un modelo de dbt o consulta SQL a la rama principal?
   * **Consigna B:** En la configuración de un archivo de GitHub Actions (`.yml`), ¿qué indica la instrucción `on: pull_request` y qué beneficio aporta para la estabilidad de la rama `main`?