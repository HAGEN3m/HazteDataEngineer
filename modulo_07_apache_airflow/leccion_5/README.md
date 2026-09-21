# 🚀 Lección 05: Cierre del Módulo 07 — Proyecto Integrador: Orquestación End-to-End con Airflow + Docker

¡Llegamos al hito final del **Módulo 07: Orquestación con Apache Airflow e Idempotencia**!

A lo largo de este módulo hemos dominado la dirección y supervisión de pipelines de datos en producción:

* **Lección 01:** Entendimos los 5 componentes centrales de Apache Airflow (`Scheduler`, `Webserver`, `Metadatabase`, `Executor` y `Workers`) y la superioridad de los DAGs sobre `cron`.
* **Lección 02:** Diseñamos DAGs defensivos combinando la TaskFlow API y Operadores Clásicos (`BashOperator`), implementando reintentos con *exponential backoff*, *timeouts* y omisiones elegantes con `AirflowSkipException`.
* **Lección 03:** Garantizamos la Idempotencia (patrones Delete-Insert y Upsert), el control temporal con `logical_date` (evitando `datetime.now()`) y la ejecución de *Backfilling*.
* **Lección 04:** Administramos la comunicación inter-tarea mediante XComs (pasaje por referencia) y configuramos Callbacks de Alerta (`on_failure_callback`) para notificar incidentes en canales de producción.

En esta lección integramos todos estos conceptos en un **Proyecto Integrador Capstone**, construyendo la orquestación de un pipeline por capas Medallón (Bronze $\rightarrow$ Silver $\rightarrow$ Gold) listo para ejecutarse sobre Airflow en Docker.

---

## 1. Escenario del Proyecto Integrador

Imaginemos que nos asignan orquestar el pipeline principal de analítica para una plataforma e-commerce.

El pipeline debe ejecutarse todos los días a las 02:00 AM de forma idempotente y seguir el siguiente flujo:

1. **Paso 1 (Bronze):** Extraer transacciones diarias de la API de ventas parametrizadas por `ds` (`logical_date`) y guardar una referencia ligera en XCom.
2. **Paso 2 (Silver - Quality Check):** Validar la integridad de los datos. Si el lote tiene 0 registros, aplicar `AirflowSkipException`.
3. **Paso 3 (Gold - Transformation):** Ejecutar el modelo de dbt o script de carga idempotente mediante `BashOperator` aplicando *Partition Overwrite*.
4. **Paso 4 (Auditoría & Alertas):** Si alguna tarea colapsa tras agotar sus reintentos, disparar un Callback de Notificación de Emergencia.

---

## 2. Arquitectura del Despliegue en Docker

En entornos profesionales, Airflow se despliega utilizando Docker Compose para aislar sus componentes en contenedores interconectados:

```text
                               CONTENEDORES DOCKER COMPOSE
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                        │
│  [ postgres-metadata ] ◄────► [ airflow-webserver ] ◄────► [ airflow-scheduler ]       │
│  (Base de datos SQL)          (Puerto 8080 UI)             (Monitorea /dags)           │
│                                                                 │                      │
│                                                                 ▼                      │
│                                                      [ airflow-worker ]                │
│                                                      (Ejecuta las Tasks)               │
│                                                                                        │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Código Completo del DAG (`dag_proyecto_integrador_airflow.py`)

```python
from datetime import datetime, timedelta
from airflow.decorators import dag, task
from airflow.operators.bash import BashOperator
from airflow.exceptions import AirflowSkipException

# ============================================================================
# PASO 1: CALLBACK DE ALERTA ANTE FALLOS (Notificación)
# ============================================================================
def notificar_incidente_produccion(context):
    ti = context.get('task_instance')
    dag_id = ti.dag_id
    task_id = ti.task_id
    logical_date = context.get('ds')
    error = context.get('exception')

    alert_payload = f"""
    🚨 *ALERTA DE PRODUCCIÓN - AIRFLOW PIPELINE FAILED*
    • *DAG*: `{dag_id}` | *Task*: `{task_id}`
    • *Fecha Analítica (logical_date)*: `{logical_date}`
    • *Excepción*: `{error}`
    • *Acción*: Revisar logs en UI ({ti.log_url})
    """
    print(f"[EMERGENCY ALERT BROADCAST]:\n{alert_payload}")

# ============================================================================
# PASO 2: CONFIGURACIÓN DE PARÁMETROS DEFENSIVOS GLOBALES
# ============================================================================
default_args = {
    'owner': 'data_engineering_team',
    'depends_on_past': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=1),
    'retry_exponential_backoff': True,
    'execution_timeout': timedelta(minutes=15),
    'on_failure_callback': notificar_incidente_produccion,
}

# ============================================================================
# PASO 3: DEFINICIÓN DEL DAG
# ============================================================================
@dag(
    dag_id='dag_proyecto_integrador_medallion_v1',
    default_args=default_args,
    start_date=datetime(2026, 1, 1),
    schedule='0 2 * * *',  # Todos los días a las 02:00 AM
    catchup=False,
    tags=['project', 'medallion', 'idempotent', 'airflow_docker']
)
def pipeline_capstone_orquestado():

    # Task 1: Ingesta Bronze Parametrizada por logical_date (ds)
    @task(task_id='extraer_bronze_api')
    def extraer_bronze(ds: str = None) -> dict:
        print(f"📥 Extrayendo datos de la API para la fecha lógica: {ds}")
        
        # Simulación de extracción (Si fuera 0 registros, lanzamos Skip)
        registros_simulados = 1200
        if registros_simulados == 0:
            raise AirflowSkipException(f"No hay registros en origen para la fecha {ds}.")

        s3_reference = f"s3://lakehouse/bronze/ventas_{ds}.json"
        
        # Retorno de XCom ligero (Pasaje por referencia)
        return {
            "s3_path": s3_reference,
            "record_count": registros_simulados,
            "logical_date": ds
        }

    # Task 2: Validación de Calidad Silver
    @task(task_id='validar_calidad_silver')
    def validar_silver(meta_bronze: dict) -> dict:
        print(f"🧹 Validando calidad sobre {meta_bronze['s3_path']}...")
        print(f"✅ Registros confirmados: {meta_bronze['record_count']}")
        
        fecha_key = int(meta_bronze['logical_date'].replace("-", ""))
        
        return {
            "s3_clean_path": meta_bronze['s3_path'].replace("bronze", "silver"),
            "fecha_key": fecha_key,
            "logical_date": meta_bronze['logical_date']
        }

    # Task 3: Carga Idempotente Gold mediante BashOperator (Ejecución dbt / SQL)
    ejecutar_carga_gold = BashOperator(
        task_id='cargar_gold_idempotente_dbt',
        bash_command=(
            'echo "Ejecutando dbt run --select fct_ventas '
            '--vars \'{"partition_date": "{{ ds }}"}\'..."'
        ),
        execution_timeout=timedelta(minutes=10)
    )

    # Task 4: Auditoría de Cierre
    @task(task_id='auditar_pipeline_final')
    def auditar_cierre(meta_silver: dict):
        print(f"🎉 Pipeline completado con éxito para la fecha {meta_silver['logical_date']}.")
        print(f"   Partición cargada idempotentemente: fecha_key = {meta_silver['fecha_key']}")

    # Flujo de Dependencias (TaskFlow API + Operador Clásico)
    raw_info = extraer_bronze()
    silver_info = validar_silver(raw_info)
    
    # Orquestación en cadena
    silver_info >> ejecutar_carga_gold >> auditar_cierre(silver_info)

# Instanciación
dag_capstone = pipeline_capstone_orquestado()
```

---

## 🏋️‍♂️ Práctica del Proyecto Integrador (Lección 05)

1. Ubicate en la carpeta `practica/modulo_07/` de tu repositorio local.
2. Creá el archivo `ej_05_proyecto_integrador_airflow.py`.
3. Escribí un script Python que simule la ejecución completa del Scheduler de Airflow ejecutando el DAG Capstone (Ciclo de Vida, XComs, Idempotencia y Notificación):

```python
import time

class AirflowEngineCapstoneSimulator:
    def __init__(self, dag_name: str):
        self.dag_name = dag_name
        self.xcom_store = {}

    def run_capstone_pipeline(self, logical_date: str):
        print("==================================================")
        print(f"🚀 [AIRFLOW SCHEDULER] Iniciando DAG Run: '{self.dag_name}'")
        print(f"📅 Logical Date (data_interval_start): {logical_date}")
        print("==================================================\n")

        try:
            # Task 1: Bronze
            print("1️⃣ [Task: extraer_bronze_api] RUNNING...")
            s3_path = f"s3://lakehouse/bronze/ventas_{logical_date}.json"
            xcom_bronze = {"s3_path": s3_path, "count": 1500, "ds": logical_date}
            self.xcom_store["extraer_bronze_api"] = xcom_bronze
            print(f"   ✅ SUCCESS | XCom Pushed: {xcom_bronze}\n")

            # Task 2: Silver
            print("2️⃣ [Task: validar_calidad_silver] RUNNING...")
            bronze_data = self.xcom_store["extraer_bronze_api"]
            fecha_key = int(logical_date.replace("-", ""))
            xcom_silver = {"fecha_key": fecha_key, "ds": logical_date}
            self.xcom_store["validar_calidad_silver"] = xcom_silver
            print(f"   ✅ SUCCESS | Validados {bronze_data['count']} registros.\n")

            # Task 3: Gold (Bash / Delete-Insert Idempotente)
            print("3️⃣ [Task: cargar_gold_idempotente_dbt] RUNNING (BashOperator)...")
            print(f"   [EXEC BASH]: DELETE FROM fact_ventas WHERE fecha_key = {fecha_key};")
            print(f"   [EXEC BASH]: INSERT INTO fact_ventas SELECT * FROM silver WHERE ds = '{logical_date}';")
            print("   ✅ SUCCESS | Partición sobreescrita de forma IDEMPOTENTE.\n")

            # Task 4: Audit
            print("4️⃣ [Task: auditar_pipeline_final] RUNNING...")
            print(f"   ✅ SUCCESS | Auditoría finalizada. DAG Run '{logical_date}' COMPLETADO.\n")

        except Exception as e:
            print("\n🚨 [CALLBACK TRIGGERED] Ejecutando notificar_incidente_produccion()")
            print(f"   • Error detectado en el pipeline: {e}")

# Ejecución de la prueba
simulator = AirflowEngineCapstoneSimulator("dag_proyecto_integrador_medallion_v1")
simulator.run_capstone_pipeline(logical_date="2026-03-15")
```

4. Agregá comentarios al final del archivo respondiendo:
   * **Consigna A:** Explica por qué el patrón Delete-Insert ejecutado en el Paso 3 garantiza que si re-ejecutamos manualmente este DAG para la fecha `'2026-03-15'`, los datos no se duplicarán en el Data Warehouse.
   * **Consigna B:** En un despliegue de producción con Docker Compose, ¿cuál es la función del volumen compartido `/opt/airflow/dags` entre el contenedor `airflow-webserver` y el contenedor `airflow-scheduler`?