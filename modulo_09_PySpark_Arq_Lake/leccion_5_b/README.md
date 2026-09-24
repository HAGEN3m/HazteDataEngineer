# 🎓 Lección 05.B (Módulo 09): Orquestación End-to-End, Observabilidad OpenLineage &amp; Cierre del Proyecto Capstone

&gt; **Propósito**: Finalizar el Proyecto Capstone Integrador unificando la orquestación declarativa (Dagster / Airflow TaskFlow), la trazabilidad automática del linaje de datos con **OpenLineage &amp; Marquez**, alertas defensivas de SLA y despliegue continuo (CI/CD) en la nube para consolidar la Arquitectura Lakehouse de producción.

---

## 📌 1\. Visión General de la Orquestación End-to-End en el Lakehouse

El objetivo final de la plataforma de datos es conectar cada componente desarrollado en las lecciones previas en un flujo cohesivo, observable y resiliente:

```
[ Fuente OLTP / Logs ] ──(CDC Debezium)──&gt; [ Apache Kafka + Schema Registry ]
                                                    │
                                                    ▼ (PySpark Streaming)
                                          [ Capa Bronze (S3 Raw Parquet) ]
                                                    │
                                                    ▼ (Dagster / Airflow Asset Exec)
                                          [ Capa Silver (Delta/Iceberg MERGE) ]
                                                    │
                                                    ▼ (Kimball Star Schema)
                                          [ Capa Gold (Fact &amp; Dim Tables) ]
                                                    │
                                                    ▼
                                     [ Servibilidad OLAP / OpenLineage ]

```

---

## 🪡 2\. Orquestación Centrada en Activos (Dagster Assets / Airflow TaskFlow)

Integración de las ejecuciones de la capa Bronze, Silver y Gold con verificación automática de dependencias y calidad de datos.

### Beneficios Clave:

1. **Disparo Basado en Eventos (*Sensor / Asset Reconciliation*)**: La capa Silver se ejecuta solo cuando nuevos micro-batches llegan a la capa Bronze.
2. **Aislamiento de Fallos**: Si un registro viola el Data Contract en la capa Silver, se desvía a la tabla de cuarentena (`quarantine_orders`) y la capa Gold continúa procesando registros válidos sin interrumpir el negocio.

---

## 🔍 3\. Observabilidad &amp; Linaje Abierto con OpenLineage y Marquez

Para garantizar la gobernanza total en clústeres distribuidos, instrumentamos las ejecuciones de Spark y Airflow/Dagster usando el estándar abierto **OpenLineage**.

```
[ Spark / Airflow / Dagster ] ──(EventEmitter)──&gt; [ OpenLineage API Backend ]
                                                           │
                                                           ▼
                                                [ Marquez UI / Catalog ]

```

### Eventos de Linaje (*RunEvent*):

* **Inputs**: Tablas/Datasets de origen con esquema y versión.
* **Outputs**: Tablas/Datasets generados con recuento de filas y columnas impactadas.
* **Job &amp; Run ID**: Trazabilidad completa para identificar qué ejecución exacta modificó una celda en la capa Gold.

---

## 🚀 4\. Despliegue Continuo (CI/CD) &amp; Hardening en Producción

El ciclo de vida del Proyecto Capstone concluye con la automatización en GitHub Actions:

```
name: Capstone Production Deployment

on:
  push:
    branches: [ main ]

jobs:
  validate-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python 3.12
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Run Linter &amp; Security Scan
        run: |
          pip install ruff bandit pytest
          ruff check .
          bandit -r src/

      - name: Execute Unit &amp; Data Contract Tests
        run: |
          pytest tests/unit/

      - name: Deploy Infrastructure (Terraform)
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        run: |
          cd terraform/
          terraform init
          terraform apply -auto-approve

```

---

## 🏋️‍♂️ Ejercicio Práctico Hands-On: Orquestador Integrador y Emisor OpenLineage

```
from dagster import asset, Definitions, Output, MetadataValue, AssetExecutionContext
import polars as pl
import requests
import json
import uuid
import datetime

# --------------------------------------------------------------------
# Cliente Emisor de Eventos OpenLineage
# --------------------------------------------------------------------
class OpenLineageLogger:
    def __init__(self, marquez_url="http://localhost:5000"):
        self.endpoint = f"{marquez_url}/api/v1/lineage"

    def emit_start_job(self, job_name: str, run_id: str, inputs: list):
        payload = {
            "eventType": "START",
            "eventTime": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "run": {"runId": run_id},
            "job": {"namespace": "capstone_lakehouse", "name": job_name},
            "inputs": [{"namespace": "s3_lakehouse", "name": inp} for inp in inputs],
            "outputs": [],
            "producer": "https://github.com/data-engineering-roadmap"
        }
        # En producción se envía un POST a Marquez/OpenLineage
        return payload

    def emit_complete_job(self, job_name: str, run_id: str, outputs: list, row_count: int):
        payload = {
            "eventType": "COMPLETE",
            "eventTime": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "run": {"runId": run_id},
            "job": {"namespace": "capstone_lakehouse", "name": job_name},
            "inputs": [],
            "outputs": [
                {
                    "namespace": "s3_lakehouse",
                    "name": out,
                    "facets": {
                        "stats": {"rowCount": row_count}
                    }
                } for out in outputs
            ],
            "producer": "https://github.com/data-engineering-roadmap"
        }
        return payload

lineage_logger = OpenLineageLogger()

# --------------------------------------------------------------------
# Activo Orquestado: Gold Business Aggregations con Linaje
# --------------------------------------------------------------------
@asset(group_name="capstone_gold")
def gold_executive_kpis(context: AssetExecutionContext) -&gt; Output[pl.DataFrame]:
    run_id = str(uuid.uuid4())
    job_name = "build_gold_executive_kpis"

    # 1. Registrar inicio en OpenLineage
    lineage_logger.emit_start_job(job_name, run_id, inputs=["silver_orders", "silver_customers"])

    # 2. Simulación de lectura de capa Silver
    silver_orders = pl.DataFrame({
        "order_id": [101, 102, 103, 104],
        "customer_id": [1, 2, 1, 3],
        "amount": [250.0, 120.0, 300.0, 450.0],
        "status": ["COMPLETED", "COMPLETED", "COMPLETED", "COMPLETED"]
    })

    # 3. Transformación Gold: Agregación de Métricas
    kpi_df = (
        silver_orders
        .group_by("customer_id")
        .agg(
            pl.sum("amount").alias("lifetime_value"),
            pl.len().alias("total_orders")
        )
        .sort("lifetime_value", descending=True)
    )

    # 4. Registrar finalización en OpenLineage
    lineage_logger.emit_complete_job(job_name, run_id, outputs=["gold_executive_kpis"], row_count=len(kpi_df))

    return Output(
        value=kpi_df,
        metadata={
            "row_count": len(kpi_df),
            "openlineage_run_id": run_id,
            "top_customer_ltv": float(kpi_df[0, "lifetime_value"])
        }
    )

defs = Definitions(assets=[gold_executive_kpis])

```

---

## 🏆 Cierre Oficial del Programa de Ingeniería de Datos 2026

¡Felicitaciones! Has completado el **Programa Integral de Formación en Ingeniería de Datos (Módulos 00 al 09)**.

### Resumen del Dominio Técnico Adquirido:

1. **Módulo 00**: Entorno Local, Bash Defensivo, Git &amp; CI/CD.
2. **Módulo 01**: Python para Data Engineering (CPython, I/O Streaming, Asyncio, Polars).
3. **Módulo 02**: SQL Avanzado &amp; Database Internals (Partitioning, DuckDB, ACID).
4. **Módulo 03**: Docker &amp; Orquestación Local (cgroups, Networking, Hardening).
5. **Módulo 04**: Modelado de Datos &amp; Medallion (Kimball, SCD 0-6, Data Vault 2.0).
6. **Módulo 05**: Apache Spark &amp; Lakehouse Internals (AQE, DPP, Delta Lake, Iceberg).
7. **Módulo 06**: Streaming &amp; Real-Time Data (Kafka, Debezium CDC, Schema Registry).
8. **Módulo 07**: Orquestación &amp; Data Quality (Airflow, Dagster, Soda, Circuit Breakers).
9. **Módulo 08**: Cloud Data Engineering, Terraform, CI/CD &amp; FinOps.
10. **Módulo 09**: Proyecto Capstone Integrador End-to-End &amp; Observabilidad.