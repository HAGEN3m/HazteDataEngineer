# 🚀 Lección 05: Cierre del Módulo 08 — Proyecto Integrador: Pipeline CI/CD Defensivo y Observabilidad End-to-End

¡Llegamos al hito final del **Módulo 08: DataOps, CI/CD y Observabilidad**!

A lo largo de este módulo hemos profesionalizado la cultura de desarrollo e ingeniería de datos:

* **Lección 01:** Adoptamos los fundamentos de DataOps, la diferencia crítica con DevOps (el estado persistente de los datos) y el aislamiento de entornos (`Dev`, `Staging`, `Prod`).
* **Lección 02:** Automatizamos el testing de código en GitHub Actions configurando linters de Python (`ruff`), pruebas unitarias (`pytest`) y linters de SQL (`SQLFluff`).
* **Lección 03:** Implementamos Data Quality Gates in-pipeline y monitoreamos el Data Drift (deriva estadística) mediante *Z-Score* para bloquear lotes anómalos.
* **Lección 04:** Establecimos los 5 Pilares de la Observabilidad de Datos (Frescura, Volumen, Esquema, Calidad y Linaje) y la gestión de SLOs/SLAs de negocio.

En esta lección integradora combinaremos todas estas herramientas construyendo un **Pipeline CI/CD Defensivo y Motor de Observabilidad End-to-End** listo para producción.

---

## 1. Escenario del Proyecto Integrador

Imaginemos que nos asignan liderar la infraestructura DataOps para la plataforma analítica de una empresa e-commerce.

Nuestra misión es implementar un sistema integral de dos etapas:

* **Etapa 1 (CI/CD en GitHub Actions):** Cada vez que un desarrollador abre un Pull Request hacia la rama `main`, un workflow automatizado ejecuta `ruff`, `pytest` y `SQLFluff`. Si alguna prueba o regla de formato falla, el *Merge* a producción queda bloqueado automáticamente.
* **Etapa 2 (Observabilidad In-Pipeline):** Al ejecutarse la ingesta diaria de la Capa Bronze a Silver/Gold, un Motor de Observabilidad en Python evalúa los 5 pilares: frescura de datos, anomalías de volumen, cambios no documentados en el esquema y deriva estadística (*Data Drift*).

---

## 2. Diagrama de la Arquitectura DataOps Integrada

```text
  [ CÓDIGO & PR ]                                      [ EJECUCIÓN IN-PIPELINE ]
┌──────────────────────────┐                         ┌──────────────────────────┐
│  Pull Request en GitHub  │                         │ Ingesta Diaria de Datos  │
└────────────┬─────────────┘                         └────────────┬─────────────┘
             │                                                    │
             ▼ (GitHub Actions CI)                                ▼ (DataOps Quality Gate)
┌──────────────────────────┐                         ┌──────────────────────────┐
│ • Ruff (Linter Python)   │                         │ • Schema Check           │
│ • Pytest (Unit Tests)    │                         │ • Freshness & Volume SLA │
│ • SQLFluff (Linter SQL)  │                         │ • Z-Score Drift Monitor  │
└────────────┬─────────────┘                         └────────────┬─────────────┘
             │                                                    │
     ┌───────┴───────┐                                    ┌───────┴───────┐
     ▼               ▼                                    ▼               ▼
 ❌ Block PR     ✅ Merge                         ✅ Aprobado      🚨 Rejección/DLQ
   Build          a Main                           Capa Gold        Alerta Slack
```

---

## 3. Código y Configuración Completa del Proyecto Capstone

### Archivo 1: `.github/workflows/dataops_capstone_ci.yml` (Workflow de GitHub Actions)

```yaml
name: DataOps Capstone CI Pipeline

on:
  pull_request:
    branches: [ "main" ]
  push:
    branches: [ "main" ]

jobs:
  dataops-quality-gate:
    name: Code, SQL & Contract Quality Guard
    runs-on: ubuntu-latest

    steps:
      - name: 1. Checkout Repositorio
        uses: actions/checkout@v4

      - name: 2. Configurar Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: 3. Instalar Dependencias de CI
        run: |
          python -m pip install --upgrade pip
          pip install ruff pytest sqlfluff pandas numpy

      - name: 4. Audit Linter Python (Ruff)
        run: |
          echo "🔍 [STEP 1] Running Ruff Linter..."
          ruff check .

      - name: 5. Unit Tests de Transformación (Pytest)
        run: |
          echo "🧪 [STEP 2] Running Pytest Suite..."
          pytest tests/ --verbose

      - name: 6. Audit Linter SQL (SQLFluff)
        run: |
          echo "📊 [STEP 3] Running SQLFluff Linter..."
          sqlfluff lint models/ --dialect postgres
```

### Archivo 2: `dataops_observability_engine.py` (Motor In-Pipeline)

```python
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

class DataOpsObservabilityEngine:
    def __init__(self, expected_schema: dict, baseline_mean: float, baseline_std: float, expected_volume: int):
        self.expected_schema = expected_schema
        self.baseline_mean = baseline_mean
        self.baseline_std = baseline_std
        self.expected_volume = expected_volume

    def evaluate_pipeline_run(self, df: pd.DataFrame, date_col: str, metric_col: str) -> dict:
        report = {
            "timestamp": datetime.now().isoformat(),
            "status": "HEALTHY",
            "violations": []
        }

        # 1. Chequeo de Esquema
        current_cols = set(df.columns)
        expected_cols = set(self.expected_schema.keys())
        missing_cols = expected_cols - current_cols

        if missing_cols:
            report["status"] = "BLOCKED"
            report["violations"].append(f"💥 ESQUEMA INCOMPATIBLE: Faltan columnas {missing_cols}")

        # 2. Chequeo de Frescura (Max Date < 24h)
        if date_col in df.columns and not df.empty:
            max_date = pd.to_datetime(df[date_col]).max()
            lag_hours = (datetime.now() - max_date).total_seconds() / 3600.0
            if lag_hours > 24.0:
                report["status"] = "DEGRADED"
                report["violations"].append(f"⏰ FRESCURA VIOLADA: Latencia de {lag_hours:.1f}h supera el SLA de 24h.")

        # 3. Chequeo de Volumen (Anomalía)
        vol_ratio = len(df) / float(self.expected_volume) if self.expected_volume > 0 else 1.0
        if vol_ratio < 0.5 or vol_ratio > 2.0:
            report["status"] = "DEGRADED"
            report["violations"].append(f"📊 VOLUMEN ANÓMALO: {len(df)} filas recibidas (Ratio {vol_ratio:.2f} vs esperado).")

        # 4. Chequeo de Data Drift (Z-Score)
        if metric_col in df.columns and not df.empty and self.baseline_std > 0:
            current_mean = df[metric_col].mean()
            z_score = abs(current_mean - self.baseline_mean) / self.baseline_std
            if z_score > 3.0:
                report["status"] = "DEGRADED"
                report["violations"].append(
                    f"🚨 DATA DRIFT DETECTADO: Media actual ${current_mean:.2f} con Z-Score = {z_score:.2f} > 3.0."
                )

        return report
```

---

## 🏋️‍♂️ Práctica del Proyecto Integrador (Lección 05)

1. Ubicate en la carpeta `practica/modulo_08/` de tu repositorio local.
2. Creá el archivo `ej_05_proyecto_integrador_dataops.py`.
3. Escribí un script Python que simule la ejecución completa del ecosistema DataOps (Simulador de CI/CD + Motor de Observabilidad In-Pipeline):

```python
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# 1. Parámetros de Referencia Histórica (Baseline)
EXPECTED_SCHEMA = {"transaccion_id": "int", "monto_usd": "float", "fecha": "datetime"}
BASELINE_MEAN_AMOUNT = 150.0  # $150 USD promedio
BASELINE_STD_AMOUNT = 20.0    # $20 USD desviación estándar
EXPECTED_DAILY_VOLUME = 1000  # 1,000 transacciones diarias

# Motor de Observabilidad (Embebido para la práctica)
class DataOpsObservabilityEngine:
    def __init__(self, expected_schema: dict, baseline_mean: float, baseline_std: float, expected_volume: int):
        self.expected_schema = expected_schema
        self.baseline_mean = baseline_mean
        self.baseline_std = baseline_std
        self.expected_volume = expected_volume

    def evaluate_pipeline_run(self, df: pd.DataFrame, date_col: str, metric_col: str) -> dict:
        report = {
            "timestamp": datetime.now().isoformat(),
            "status": "HEALTHY",
            "violations": []
        }

        # 1. Esquema
        missing_cols = set(self.expected_schema.keys()) - set(df.columns)
        if missing_cols:
            report["status"] = "BLOCKED"
            report["violations"].append(f"💥 ESQUEMA INCOMPATIBLE: Faltan columnas {missing_cols}")

        # 2. Frescura
        if date_col in df.columns and not df.empty:
            max_date = pd.to_datetime(df[date_col]).max()
            lag_hours = (datetime.now() - max_date).total_seconds() / 3600.0
            if lag_hours > 24.0:
                report["status"] = "DEGRADED"
                report["violations"].append(f"⏰ FRESCURA VIOLADA: Latencia de {lag_hours:.1f}h supera el SLA de 24h.")

        # 3. Volumen
        vol_ratio = len(df) / float(self.expected_volume) if self.expected_volume > 0 else 1.0
        if vol_ratio < 0.5 or vol_ratio > 2.0:
            report["status"] = "DEGRADED"
            report["violations"].append(f"📊 VOLUMEN ANÓMALO: {len(df)} filas recibidas (Ratio {vol_ratio:.2f} vs esperado).")

        # 4. Data Drift (Z-Score)
        if metric_col in df.columns and not df.empty and self.baseline_std > 0:
            current_mean = df[metric_col].mean()
            z_score = abs(current_mean - self.baseline_mean) / self.baseline_std
            if z_score > 3.0:
                report["status"] = "DEGRADED"
                report["violations"].append(
                    f"🚨 DATA DRIFT DETECTADO: Media actual ${current_mean:.2f} con Z-Score = {z_score:.2f} > 3.0."
                )

        return report

# 2. Simulador del Sistema DataOps Capstone
class DataOpsCapstoneSystemSimulator:
    def __init__(self):
        self.observability_engine = DataOpsObservabilityEngine(
            expected_schema=EXPECTED_SCHEMA,
            baseline_mean=BASELINE_MEAN_AMOUNT,
            baseline_std=BASELINE_STD_AMOUNT,
            expected_volume=EXPECTED_DAILY_VOLUME
        )

    def run_ci_cd_stage(self, pr_has_syntax_error: bool) -> bool:
        print("=== ETAPA 1: WORKFLOW DE GITHUB ACTIONS (CI/CD) ===")
        if pr_has_syntax_error:
            print("❌ [GitHub Actions] RUFF / SQLFLUFF ERROR: Sintaxis o formato inválido.")
            print("   Merge a 'main' BLOQUEADO.\n")
            return False

        print("✅ [GitHub Actions] Ruff, Pytest y SQLFluff PASSED.")
        print("   Pull Request Aprobado y Fused en 'main'.\n")
        return True

    def run_pipeline_observability_stage(self, df_batch: pd.DataFrame, batch_name: str):
        print(f"=== ETAPA 2: MOTOR DE OBSERVABILIDAD IN-PIPELINE ({batch_name}) ===")
        report = self.observability_engine.evaluate_pipeline_run(
            df=df_batch,
            date_col="fecha",
            metric_col="monto_usd"
        )

        print(f"  • Estado Global de Salud: {report['status']}")
        if report["violations"]:
            print("  • Incidentes Detectados:")
            for viol in report["violations"]:
                print(f"    - {viol}")
        else:
            print("  • ✅ Todos los SLOs/SLAs de Datos en estado ÓPTIMO.")
        print()

# Ejecución de Pruebas Integradas
system = DataOpsCapstoneSystemSimulator()

# Test 1: CI/CD rechaza PR con error
system.run_ci_cd_stage(pr_has_syntax_error=True)

# Test 2: CI/CD aprueba PR limpio
system.run_ci_cd_stage(pr_has_syntax_error=False)

# Test 3: Evaluando Lote Normal
df_lote_sano = pd.DataFrame({
    "transaccion_id": range(1, 1001),
    "monto_usd": np.random.normal(loc=152.0, scale=18.0, size=1000),
    "fecha": [datetime.now()] * 1000
})
system.run_pipeline_observability_stage(df_lote_sano, "Lote_Lunes_Limpio")

# Test 4: Evaluando Lote con Data Drift y Caída de Volumen
df_lote_drift = pd.DataFrame({
    "transaccion_id": range(1, 100),  # Solo 99 filas (Caída > 90%)
    "monto_usd": np.random.normal(loc=280.0, scale=25.0, size=99),  # Media $280 (Drift Z > 6.0)
    "fecha": [datetime.now() - timedelta(days=2)] * 99  # Desactualizado 48h
})
system.run_pipeline_observability_stage(df_lote_drift, "Lote_Martes_Anomalo")
```

4. Agregá comentarios al final del archivo respondiendo:
   * **Consigna A:** ¿Qué diferencia estratégica existe entre las validaciones que realiza el workflow de GitHub Actions (Etapa 1) vs. las validaciones que ejecuta el Motor de Observabilidad In-Pipeline (Etapa 2)?
   * **Consigna B:** Explica cómo la combinación de linters, testing unitario, Data Quality Gates y alertas de observabilidad permite reducir a casi cero el Tiempo Medio de Reparación (MTTR - *Mean Time to Repair*) ante incidentes de datos en producción.