# 🌪️ Lección 01.B (Módulo 07): Apache Airflow Avanzado: TaskFlow API, Dynamic Task Mapping & Deferrable Operators

> **Propósito**: Dominar patrones avanzados de orquestación en Apache Airflow, migrando del paradigma clásico de operadores a la **TaskFlow API**, implementando generación dinámica de tareas (*Dynamic Task Mapping*), optimizando el uso de RAM y workers mediante **Deferrable Operators & Triggers** (asincrónicos) y creando operadores personalizados (*Custom Operators*) de nivel producción.

---

## 📌 1. Evolución del Paradigma: Operadores Clásicos vs. TaskFlow API

En versiones anteriores de Airflow (v1.x / v2.0), el intercambio de datos entre tareas requería instanciar manualmente operadores (`PythonOperator`, `BashOperator`) y gestionar explícitamente **XComs** (`xcom_push` y `xcom_pull`), generando código redundante (*boilerplate*) y difícil de mantener.

```python
# ❌ PARADIGMA CLÁSICO (Verboso y propenso a errores)
def extract_data(**kwargs):
    data = {"total": 1500, "status": "ok"}
    kwargs['ti'].xcom_push(key='payload', value=data)

def process_data(**kwargs):
    ti = kwargs['ti']
    payload = ti.xcom_pull(key='payload', task_ids='extract')
    print(f"Processing {payload['total']}")

extract_task = PythonOperator(
    task_id='extract',
    python_callable=extract_data,
    dag=dag
)
process_task = PythonOperator(
    task_id='process',
    python_callable=process_data,
    dag=dag
)
extract_task >> process_task
```

### La Revolución de TaskFlow API (Airflow 2.0+)
Con la **TaskFlow API**, Airflow utiliza decoradores `@dag` y `@task` que convierten funciones nativas de Python en tareas orquestadas. La transferencia de datos vía XComs se gestiona de forma transparente retornando valores directamente.

```python
# ✅ TASKFLOW API (Limpio, fuertemente tipado y Pythonico)
from airflow.decorators import dag, task
from datetime import datetime

@dag(schedule="@daily", start_date=datetime(2026, 1, 1), catchup=False)
def pipeline_ingesta_mod26():

    @task
    def extract_data() -> dict:
        return {"total": 1500, "status": "ok"}

    @task
    def process_data(payload: dict):
        print(f"Processing {payload['total']}")

    # Invocación y pase implícito de XCom
    data = extract_data()
    process_data(data)

pipeline = pipeline_ingesta_mod26()
```

---

## 🔬 2. Mapeo Dinámico de Tareas (*Dynamic Task Mapping*)

En pipelines de datos reales, el número de archivos a procesar, tablas a migrar o particiones a ingerir **no se conoce de antemano**; depende de los datos que llegan en tiempo de ejecución.

El **Dynamic Task Mapping** (`.expand()`) permite a Airflow instanciar N tareas en paralelo basándose en el resultado de una tarea previa.

```
                  ┌───> [ Task Process: Partner A ] ───┐
                  │                                    │
[ Task Fetch List ] ───> [ Task Process: Partner B ] ───┼───> [ Task Aggregate ]
                  │                                    │
                  └───> [ Task Process: Partner C ] ───┘
```

### Ejemplo de Mapeo Dinámico:
```python
from airflow.decorators import dag, task
from datetime import datetime

@dag(schedule=None, start_date=datetime(2026, 1, 1), catchup=False)
def dynamic_etl_pipeline():

    @task
    def get_active_partners() -> list[str]:
        # Consulta dinámica a la base de datos o S3
        return ["partner_alpha", "partner_beta", "partner_gamma"]

    @task
    def process_partner(partner_id: str) -> dict:
        # Tarea ejecutada en PARALELO para cada partner
        print(f"Procesando datos para {partner_id}")
        return {"partner": partner_id, "status": "PROCESSED"}

    @task
    def aggregate_results(results: list[dict]):
        print(f"Total partners procesados exitosamente: {len(results)}")

    partners = get_active_partners()
    # .expand() genera dinámicamente 3 instancias independientes de la tarea process_partner
    processed_data = process_partner.expand(partner_id=partners)
    aggregate_results(processed_data)

dag_instance = dynamic_etl_pipeline()
```

---

## 🛠️ 3. Deferrable Operators & Triggers (Liberación Asincrónica de RAM)

Cuando Airflow ejecuta un operador que espera por un recurso externo (ej. esperar 45 minutos a que un job de **AWS Glue**, **EMR** o **Databricks** termine, o un `Sensors` esperando un archivo en S3), el worker mantiene ocupado un slot de ejecución y consume memoria RAM de forma ociosa.

```
❌ OPERADOR TRADICIONAL (Síncrono/Blocking):
[ Worker Slot Ocupado (RAM/CPU) ] ─── (Polling cada 30s) ───> Espera 1 Hora ───> OOM / Bloqueo de Cola

✅ DEFERRABLE OPERATOR (Asincrónico/Triggerer):
[ Worker Executing ] ─── Suscala estado a Triggerer ───> [ Worker Slot LIBERADO ]
                                                                   │
                                                                   ▼ (Triggerer asincrónico asyncio)
[ Worker Re-asignado solo al finalizar ] <─── Notificación Event ──┘
```

### ¿Cómo funciona el Triggerer?
1. El **Deferrable Operator** inicia la petición al servicio externo (ej. lanza el Job de Spark en EMR).
2. Libera inmediatamente el *Worker Slot* suspendiendo la tarea y cediendo el control al demonio **Airflow Triggerer**.
3. El **Triggerer** corre un bucle de eventos asincrónico (`asyncio`) que monitorea cientos de tareas diferidas simultáneamente usando un solo proceso.
4. Cuando el evento concluye, el Triggerer despierta a un Worker para ejecutar los pasos finales de la tarea.

> 💡 **Impacto en Infraestructura**: Reduce el costo de clústeres de Airflow (MWAA / Astronomer) hasta en un **60%** al eliminar Workers ociosos esperando jobs externos.

---

## ⚡ 4. Custom Operators & Decoradores Virtualizados

Para extender la funcionalidad de Airflow manteniendo estándares de ingeniería corporativos, podemos crear **Custom Operators** o aislar dependencias de Python mediante `@task.virtualenv` o `@task.docker`.

### A. Tareas Aisladas con Entornos Virtuales (`@task.virtualenv`)
Evita conflictos de dependencias de Python (*Dependency Hell*) creando un `venv` efímero para la tarea:

```python
@task.virtualenv(
    requirements=["polars==0.20.0", "pyarrow==15.0.0"],
    system_site_packages=False
)
def transform_heavy_data():
    import polars as pl
    df = pl.DataFrame({"a": [1, 2, 3]})
    return df.sum().to_dict()
```

### B. Custom Operator de Producción
```python
from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults

class PostgresToMinioOperator(BaseOperator):
    """
    Operador personalizado para extraer datos de Postgres y cargarlos en MinIO/S3.
    """
    @apply_defaults
    def __init__(self, postgres_conn_id: str, minio_conn_id: str, sql_query: str, target_bucket: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.postgres_conn_id = postgres_conn_id
        self.minio_conn_id = minio_conn_id
        self.sql_query = sql_query
        self.target_bucket = target_bucket

    def execute(self, context):
        self.log.info(f"Ejecutando consulta SQL: {self.sql_query}")
        # Lógica de extracción y carga
        return "SUCCESS"
```

---

## 🏋️‍♂️ Ejercicio Práctico Hands-On: DAG Defensivo en TaskFlow API con Dynamic Mapping y Error Handling

Crea el archivo `dag_avanzado_taskflow.py` para demostrar orquestación resiliente en producción:

```python
from datetime import datetime, timedelta
from airflow.decorators import dag, task
from airflow.operators.python import get_current_context

default_args = {
    'owner': 'data_engineering_team',
    'retries': 3,
    'retry_delay': timedelta(minutes=2),
    'email_on_failure': False,
}

@dag(
    dag_id="modulo_07_taskflow_advanced_v1",
    default_args=default_args,
    schedule_interval="@daily",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["production", "taskflow", "dynamic_mapping"]
)
def pipeline_orquestacion_avanzada():

    @task
    def discover_source_files() -> list[str]:
        """Descubre dinámicamente los archivos presentes en el Data Lake."""
        # En un escenario real, esto consulta S3/MinIO
        files = ["transactions_2026_01.csv", "transactions_2026_02.csv", "transactions_2026_03.csv"]
        if not files:
            raise ValueError("No se encontraron archivos fuente para procesar.")
        return files

    @task(retries=2, retry_delay=timedelta(seconds=30))
    def validate_and_transform(file_name: str) -> dict:
        """Procesa y valida un archivo individual de forma paralela."""
        context = get_current_context()
        execution_date = context['ds']
        print(f"Procesando {file_name} para la fecha de ejecución {execution_date}")
        
        # Simulación de transformación
        return {"file": file_name, "records_processed": 5000, "status": "SUCCESS"}

    @task
    def consolidate_metrics(results: list[dict]):
        """Consolida las métricas de todas las tareas dinámicas mapeadas."""
        total_records = sum(r['records_processed'] for r in results)
        print(f"📊 Reporte Final: {len(results)} archivos procesados. Total registros: {total_records}")

    # Flujo de ejecución
    files_to_process = discover_source_files()
    processed_results = validate_and_transform.expand(file_name=files_to_process)
    consolidate_metrics(processed_results)

# Instanciación del DAG
dag_pipeline = pipeline_orquestacion_avanzada()
```

---

## 🧠 Checkpoint de Autoevaluación

1. ¿Qué ventajas estructurales ofrece la **TaskFlow API** frente a la declaración tradicional de DAGs usando `PythonOperator` y `xcom_push` / `xcom_pull`?
2. ¿Cómo funciona el método `.expand()` en **Dynamic Task Mapping** y en qué se diferencia de iterar un bucle `for` convencional en Python durante la definición del DAG?
3. ¿Por me el uso de **Deferrable Operators & Triggers** reduce drásticamente los costos de infraestructura en servicios administrados de Airflow como AWS MWAA o Astronomer?
4. ¿Cuándo deberías usar un decorador `@task.virtualenv` o `@task.docker` en lugar de una tarea de Python estándar dentro del worker de Airflow?

---

🚀 ¿Avanzamos con la **`modulo_07_leccion_02_B`** (*Asset-Based Orchestration con Dagster: Software-Defined Assets, Linaje Automático e I/O Managers*)?
