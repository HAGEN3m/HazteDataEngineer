# 🔭 Lección 04.B (Módulo 07): Observabilidad &amp; Linaje de Datos: OpenLineage, Marquez, Alertas de SLA y Trazabilidad

&gt; **Propósito**: Implementar observabilidad de datos de extremo a extremo (*End-to-End Data Observability*) mediante estándares abiertos (**OpenLineage** y **Marquez**), definiendo métricas de calidad operativas, trazabilidad de esquemas y transformaciones, monitoreo de SLAs e integración de alertas automáticas para prevenir fallos silenciosos en producción.

---

## 📌 1\. Los 5 Pilares de la Observabilidad de Datos

A diferencia del monitoreo de software tradicional (CPU, RAM, latencia HTTP), la **Observabilidad de Datos** se centra en la salud e integridad de la información que fluye a través de los sistemas.

```
       ┌─────────────────────────────────────────────────────────┐
       │             5 PILARES DE OBSERVABILIDAD                │
       └─────────────────────────────────────────────────────────┘
        ├── 1. Frescura (Freshness / Timeliness &amp; SLAs)
        ├── 2. Calidad &amp; Distribución (Data Quality &amp; Volume)
        ├── 3. Esquema &amp; Deriva (Schema Drift)
        ├── 4. Linaje (End-to-End Lineage)
        └── 5. Estado de Ejecución (Pipeline Performance &amp; Health)

```

1. **Frescura (*Freshness*)**: ¿Cuándo fue la última vez que se actualizó la tabla? ¿Estamos cumpliendo con los SLAs del negocio?
2. **Volumen &amp; Distribución**: ¿Llegaron los 100,000 registros esperados o cayeron a 50 debido a un fallo en el upstream?
3. **Esquema (*Schema Drift*)**: ¿Cambió el tipo de dato de una columna o desapareció un campo crítico en la fuente?
4. **Linaje (*Lineage*)**: Si una tabla de la capa Gold tiene errores, ¿cuál fue el pipeline u origen exacto en la capa Bronze que causó la falla?
5. **Rendimiento (*Execution Performance*)**: ¿Por qué un DAG de Airflow/Spark pasó de tardar 5 minutos a 3 horas?

---

## 🌐 2\. Estándares Abiertos: OpenLineage &amp; Marquez

Para evitar el acoplamiento a herramientas propietarias de observabilidad, la Linux Foundation gestiona **OpenLineage**, un estándar abierto especificado en JSON que define cómo los motores de cómputo (Airflow, Spark, dbt, Flink) emiten eventos de linaje en tiempo de ejecución.

### Especificación de OpenLineage:

Cada evento de OpenLineage captura:

* **Job**: Identificador del proceso o tarea (ej. `dbt.run.gold_revenue`).
* **Run**: ID único de la ejecución (`Run ID`) con timestamp de inicio y fin.
* **Inputs &amp; Outputs**: Datasets leídos y producidos (con su esquema exacto y localización URI).
* **Facets**: Metadatos adicionales (métricas de calidad, consultas SQL ejecutadas, versión de código).

```
{
  "eventType": "COMPLETE",
  "eventTime": "2026-09-24T12:00:00Z",
  "producer": "https://github.com/OpenLineage/OpenLineage/tree/1.0.0/integration/spark",
  "job": {
    "namespace": "production_cluster",
    "name": "spark_gold_aggregation_job"
  },
  "inputs": [
    {
      "namespace": "s3://my-data-lake",
      "name": "silver/transactions"
    }
  ],
  "outputs": [
    {
      "namespace": "postgres://warehouse-prod:5432/analytics",
      "name": "gold_daily_revenue"
    }
  ]
}

```

### Marquez: El Servidor de Metadatos y Grafo de Linaje

**Marquez** es el servidor de referencia (*Reference Implementation*) para colectar, almacenar y visualizar eventos de OpenLineage. Permite navegar visualmente el grafo de dependencias de activos y consultar el historial de versiones de esquemas y ejecuciones.

---

## 🚨 3\. Monitoreo de SLAs y Alertas de Producción

Un **SLA (*Service Level Agreement*) de Datos** define la garantía máxima de retraso tolerable para un activo de datos crítico (ej. *"La tabla `gold_revenue` debe estar actualizada antes de las 06:00 AM con datos no más antiguos a 2 horas"*).

### Patrón de Alerta con Slack / PagerDuty:

```
def send_slack_alert(context):
    """Callback de falla en Airflow/Dagster para notificaciones en tiempo real."""
    dag_id = context.get('task_instance').dag_id
    task_id = context.get('task_instance').task_id
    execution_date = context.get('execution_date')
    exception = context.get('exception')

    payload = {
        "text": f"🚨 *CRITICAL DATA PIPELINE FAILURE*\n"
                f"*DAG*: `{dag_id}` | *Task*: `{task_id}`\n"
                f"*Execution Time*: `{execution_date}`\n"
                f"*Error*: ```{exception}```"
    }
    # Enviar payload vía Webhook

```

---

## 🏋️‍♂️ Ejercicio Práctico Hands-On: Colector de Linaje y Telemetría en Python

Implementaremos un decorador ejecutor que genera telemetría de observabilidad y eventos estructurados compatibles con **OpenLineage**:

```
import time
import datetime
import json
import uuid
import typing as t

class LineageCollector:
    """Colector ligero de eventos de observabilidad alineado con OpenLineage."""

    @staticmethod
    def emit_event(
        job_name: str,
        event_type: str,
        inputs: t.List[str],
        outputs: t.List[str],
        metadata: dict
    ) -&gt; dict:
        event = {
            "eventId": str(uuid.uuid4()),
            "eventType": event_type,  # START, COMPLETE, FAIL
            "eventTime": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "job": {
                "namespace": "data-engineering-pipeline",
                "name": job_name
            },
            "inputs": [{"namespace": "lakehouse", "name": inp} for inp in inputs],
            "outputs": [{"namespace": "lakehouse", "name": out} for out in outputs],
            "facets": {
                "metrics": metadata
            }
        }
        return event

def observable_pipeline(job_name: str, inputs: t.List[str], outputs: t.List[str]):
    """Decorador de observabilidad para medir tiempo, captura de errores y linaje."""
    def decorator(func: t.Callable):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            start_event = LineageCollector.emit_event(
                job_name, "START", inputs, outputs, {}
            )
            print(f"[OBSERVABILITY] 🚀 EVENT START: {json.dumps(start_event, indent=2)}")

            try:
                result, record_count = func(*args, **kwargs)
                execution_time = round(time.time() - start_time, 4)

                complete_event = LineageCollector.emit_event(
                    job_name, "COMPLETE", inputs, outputs, {
                        "execution_time_seconds": execution_time,
                        "records_processed": record_count,
                        "status": "SUCCESS"
                    }
                )
                print(f"[OBSERVABILITY] ✅ EVENT COMPLETE: {json.dumps(complete_event, indent=2)}")
                return result

            except Exception as e:
                execution_time = round(time.time() - start_time, 4)
                fail_event = LineageCollector.emit_event(
                    job_name, "FAIL", inputs, outputs, {
                        "execution_time_seconds": execution_time,
                        "error_message": str(e),
                        "status": "FAILED"
                    }
                )
                print(f"[OBSERVABILITY] ❌ EVENT FAIL: {json.dumps(fail_event, indent=2)}")
                raise e

        return wrapper
    return decorator

# --------------------------------------------------------------------
# Uso en un Pipeline de Producción
# --------------------------------------------------------------------
@observable_pipeline(
    job_name="transform_silver_to_gold_revenue",
    inputs=["silver_transactions"],
    outputs=["gold_daily_revenue"]
)
def run_aggregation():
    # Simulación de cómputo analítico
    time.sleep(0.5)
    processed_records = 15000
    return "SUCCESS", processed_records

if __name__ == "__main__":
    run_aggregation()

```

---

## 🧠 Checkpoint de Autoevaluación

1. ¿Cuáles son los 5 pilares de la observabilidad de datos y en qué se diferencia de la observabilidad APM de software tradicional?
2. ¿Qué es OpenLineage y qué ventajas ofrece estructurar los eventos de linaje bajo un estándar abierto?
3. ¿Cómo ayuda Marquez a realizar análisis de impacto cuando cambia el esquema de una fuente aguas arriba (*Upstream*)?
4. ¿Qué diferencia existe entre un error por fallo de sintaxis/infraestructura y una falla de SLA/Frescura en un pipeline?