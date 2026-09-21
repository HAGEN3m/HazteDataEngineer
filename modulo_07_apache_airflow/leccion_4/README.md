# 🚀 Lección 04: Manejo de Estado, XComs, Retries y Alertas en Canales (Slack/Email/Discord)

En la Lección 03 dominamos el principio de Idempotencia, la gestión de intervalos temporales con `logical_date` y la ejecución de re-procesamientos históricos (*Backfilling*).

En esta lección abordaremos la comunicación entre tareas y el monitoreo operativo: **¿Cómo se comparten metadatos entre tareas aisladas dentro de un DAG y cómo se notifica automáticamente a los ingenieros cuando ocurre un fallo en producción?**

Aprenderemos a utilizar **XComs (*Cross-Communications*)** de forma eficiente (evitando antipatrones como saturar la base de datos de Airflow con DataFrames masivos) y a configurar *Callbacks* de Alerta en canales como Slack, Discord o correo electrónico.

---

## 1. Comunicación Inter-Tarea: ¿Qué son los XComs?

Por diseño, cada tarea en Airflow se ejecuta de forma aislada en un proceso o contenedor independiente. Las tareas no comparten memoria RAM ni variables globales.

Sin embargo, en muchos flujos necesitamos pasar información ligera de una tarea a otra (por ejemplo, el número de filas procesadas, el ID de un lote generado o la ruta de un archivo guardado en el Data Lake S3/GCS).

Para esto existen los **XComs (*Cross-Communications*)**: un mecanismo de mensajería clave-valor almacenado directamente en la Metadatabase de Airflow.

```text
               FLUJO DE INTERCAMBIO CON XCOMS (Metadatabase)
┌──────────────────────────┐                      ┌──────────────────────────┐
│ Task A: Extraer API      │                      │ Task B: Cargar DW        │
├──────────────────────────┤                      ├──────────────────────────┤
│ Genera 's3_file_path'    │                      │ Lee 's3_file_path'       │
└────────────┬─────────────┘                      └────────────▲─────────────┘
             │ xcom_push(key, value)                           │ xcom_pull(task_ids)
             ▼                                                 │
┌──────────────────────────────────────────────────────────────┴───────────┐
│                    AIRFLOW METADATABASE (Tabla `xcom`)                   │
│  dag_id  | task_id | run_id | key            | value                     │
│  dag_v1  | task_a  | run_01 | 's3_file_path' | 's3://bucket/20260315.parquet'│
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Reglas de Oro y Antipatrones de XComs

### ❌ El Antipatrón Peligroso:
Nunca uses XComs para pasar DataFrames de Pandas/Polars o datasets pesados de megabytes o gigabytes. Dado que los XComs se serializan y se guardan como registros en la base de datos relacional de Airflow (PostgreSQL/MySQL), pasar datasets pesados colapsará la memoria de la Metadatabase y ralentizará todo el servidor.

### 🟢 El Patrón Ssr Correcto:
Usa el patrón **Pass-by-Reference (Pasaje por Referencia)**:
1. **Task A** guarda el dataset pesado directamente en el Data Lake o Data Warehouse (ej. `s3://bucket/layer_silver/20260315.parquet`).
2. **Task A** retorna únicamente la cadena de texto con la ruta del archivo (XCom ligero).
3. **Task B** lee la ruta del XCom y descarga/procesa el archivo directamente desde el almacenamiento.

---

## 3. Uso de XComs en la TaskFlow API vs. Operadores Clásicos

### A. En TaskFlow API (Automático y Transparente)
En Airflow 2.0+, cualquier valor retornado por una función decorada con `@task` se convierte automáticamente en un XCom.

```python
@task()
def generar_ruta_archivo(ds: str = None) -> str:
    # El return genera automáticamente un XCom con la clave 'return_value'
    return f"s3://my-lakehouse/bronze/ventas_{ds}.parquet"

@task()
def procesar_archivo(path_s3: str):
    # Airflow resuelve la dependencia y extrae el XCom de forma transparente
    print(f"Leyendo dataset masivo desde: {path_s3}")

# Conexión limpia
path = generar_ruta_archivo()
procesar_archivo(path)
```

### B. En Operadores Clásicos (`ti.xcom_push` / `ti.xcom_pull`)
Si usás la API clásica, interactuás con el contexto del objeto `TaskInstance` (`ti`):

```python
# Tarea Emisora
def enviar_metadato_func(**context):
    ti = context['ti']
    ti.xcom_push(key='total_registros', value=1500)

# Tarea Receptora
def recibir_metadato_func(**context):
    ti = context['ti']
    total = ti.xcom_pull(task_ids='tarea_emisora', key='total_registros')
    print(f"Registros a validar: {total}")
```

---

## 4. Alertas Automáticas y Callbacks en Canales (Slack / Discord / Email)

Cuando un pipeline falla en producción a las 4:00 AM, el equipo de datos debe ser notificado de inmediato con el contexto exacto del error sin tener que revisar manualmente el dashboard.

Airflow ofrece **Callbacks de Ciclo de Vida**:
* **`on_failure_callback`:** Se ejecuta automáticamente cuando una tarea falla definitivamente.
* **`on_retry_callback`:** Se ejecuta cada vez que una tarea falla e inicia un reintento.
* **`on_success_callback`:** Se ejecuta al finalizar con éxito (útil para auditoría).

### Ejemplo de Función de Alerta para Slack / Discord:
```python
def notificar_error_slack(context):
    """
    Función Callback que captura el contexto del fallo en Airflow
    y envía un mensaje estructurado vía Webhook.
    """
    dag_id = context.get('task_instance').dag_id
    task_id = context.get('task_instance').task_id
    logical_date = context.get('ds')
    exception = context.get('exception')
    log_url = context.get('task_instance').log_url

    mensaje = f"""
    🚨 *ALERTA DE PRODUCCIÓN - TAREA FALLIDA* 🚨
    • *DAG*: `{dag_id}`
    • *Task*: `{task_id}`
    • *Fecha Analítica*: `{logical_date}`
    • *Error*: `{exception}`
    • *Logs*: <{log_url}|Ver Logs en Airflow UI>
    """

    # Enviar payload vía requests POST al Webhook de Slack/Discord
    print(f"[SLACK BOT WEBHOOK]:\n{mensaje}")
```

---

## 5. Código Completo de un DAG con XComs y Callbacks de Alerta

```python
from datetime import datetime, timedelta
from airflow.decorators import dag, task

# 1. Definición del Callback de Alerta ante Fallos
def notificar_fallo_canal(context):
    ti = context.get('task_instance')
    print(f"🚨 [ALERT SYSTEM] La tarea '{ti.task_id}' del DAG '{ti.dag_id}' falló. "
          f"Revisar logs en: {ti.log_url}")

# 2. Argumentos Defensivos con Callback
default_args = {
    'owner': 'data_engineer_ssr',
    'retries': 1,
    'retry_delay': timedelta(minutes=2),
    'on_failure_callback': notificar_fallo_canal,  # Callback global
}

@dag(
    dag_id='dag_xcoms_y_alertas_v1',
    default_args=default_args,
    start_date=datetime(2026, 1, 1),
    schedule='@daily',
    catchup=False,
    tags=['xcom', 'alerting', 'production']
)
def pipeline_con_alertas():

    # Task 1: Genera y publica una referencia de archivo (XCom)
    @task(task_id='extraer_y_guardar_s3')
    def extraer_datos(ds: str = None) -> dict:
        path_s3 = f"s3://data-lake-prod/silver/ventas_{ds}.parquet"
        registros = 4500

        # Retornamos un diccionario con metadatos ligeros
        return {
            "s3_path": path_s3,
            "row_count": registros
        }

    # Task 2: Recibe el XCom de Task 1 y procesa
    @task(task_id='validar_y_cargar_gold')
    def cargar_gold(metadatos_bronze: dict):
        path = metadatos_bronze["s3_path"]
        rows = metadatos_bronze["row_count"]

        print(f"📥 Leyendo {rows} registros desde {path}...")

        if rows <= 0:
            raise ValueError("El archivo en S3 está vacío. Abortando pipeline.")

        print("✅ Procesamiento Gold completado con éxito.")

    # Flujo de ejecución pasando el retorno como argumento
    meta = extraer_datos()
    cargar_gold(meta)

dag_instance = pipeline_con_alertas()
```

---

## 🏋️‍♂️ Práctica de la Lección 04

1. Ubicate en la carpeta `practica/modulo_07/` de tu repositorio local.
2. Creá el archivo `ej_04_xcoms_alertas.py`.
3. Escribí un script Python que simule la tabla de XComs de la Metadatabase y un gestor de callbacks de alerta para fallos:

```python
import pandas as pd

# Simulación de la Metadatabase de Airflow (Tabla `xcom`)
class AirflowMetadatabaseSimulator:
    def __init__(self):
        self.xcom_table = []

    def xcom_push(self, dag_id: str, task_id: str, key: str, value):
        # Valida tamaño simulado (Antipatrón: No guardar objetos gigantes)
        if isinstance(value, pd.DataFrame):
            print(f"⚠️ [WARNING XCOM] ¡ALERTA! Se intentó guardar un DataFrame de {len(value)} filas en XCom.")
            print("   Antipatrón detectado: Guardá el archivo en S3/Parquet y pasá solo la ruta string.")

        self.xcom_table.append({
            "dag_id": dag_id,
            "task_id": task_id,
            "key": key,
            "value": value
        })
        print(f"💾 [XCom Pushed] Task '{task_id}' guardó '{key}' ➔ {value}")

    def xcom_pull(self, dag_id: str, task_id: str, key: str):
        for entry in reversed(self.xcom_table):
            if entry["dag_id"] == dag_id and entry["task_id"] == task_id and entry["key"] == key:
                return entry["value"]
        return None

# Simulador de Callbacks ante Errores
def callback_slack_alert(task_id: str, error: Exception):
    print(f"\n🚨 [SLACK BOT NOTIFICATION]")
    print(f"   • Alerta: La tarea '{task_id}' ha colapsado.")
    print(f"   • Causa: {error}")
    print(f"   • Estado: Notificado al canal #alertas-data-eng\n")

# Ejecución de Prueba
meta_db = AirflowMetadatabaseSimulator()

print("=== PRUEBA 1: USO CORRECTO DE XCOMS (Pasaje por Referencia) ===")
meta_db.xcom_push("dag_ventas", "task_extraer", "s3_reference", "s3://bucket/silver_2026.parquet")
ref = meta_db.xcom_pull("dag_ventas", "task_extraer", "s3_reference")
print(f"Task Cargar leyó la referencia: {ref}\n")

print("=== PRUEBA 2: ADVERTENCIA DE ANTIPATRÓN (DataFrame en XCom) ===")
df_gigante = pd.DataFrame({"id": range(10000), "monto": [99.9]*10000})
meta_db.xcom_push("dag_ventas", "task_extraer", "df_data", df_gigante)

print("\n=== PRUEBA 3: EJECUCIÓN DE CALLBACK DE ALERTA ===")
try:
    raise ConnectionResetError("Error de conexión con el servidor PostgreSQL remoto.")
except Exception as e:
    callback_slack_alert("task_cargar_gold", e)
```

4. Agregá comentarios al final del archivo respondiendo:
   * **Consigna A:** ¿Por qué guardar un DataFrame de 1,000,000 de filas dentro de un XCom se considera un antipatrón grave de arquitectura en Apache Airflow?
   * **Consigna B:** ¿Qué información clave debe incluir la función callback `on_failure_callback` al enviar un mensaje a Slack o Teams para que el ingeniero de guardia pueda diagnosticar el error rápidamente?