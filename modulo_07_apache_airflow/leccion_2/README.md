# 🚀 Lección 02: Definición de DAGs Defensivos con TaskFlow API y Operadores (PythonOperator, BashOperator)

En la Lección 01 comprendimos la arquitectura interna de Apache Airflow (Scheduler, Webserver, Metadatabase, Executor y Workers) y la diferencia abismal entre programar tareas estáticas con cron vs. orquestar flujos distribuidos mediante DAGs.

Sin embargo, en entornos de producción reales a nivel Ssr/Senior, no basta con escribir un DAG que funcione en condiciones ideales (*Happy Path*). Los servidores sufren micro-cortes de red, las APIs de terceros devuelven códigos `503 Service Unavailable` y las bases de datos pueden colgarse por cerrojos (*locks*).

En esta lección aprenderemos a diseñar DAGs defensivos y resilientes, dominando tanto la **TaskFlow API** moderna como los **Operadores Clásicos** (`PythonOperator`, `BashOperator`), configurando políticas de reintentos, tiempos máximos de ejecución (*Timeouts*) y manejo de excepciones.

---

## 1. Paradigmas de Código: Operadores Clásicos vs. TaskFlow API

En Airflow existen dos formas coexistentes de definir tareas y sus dependencias:

```text
               PARADIGMAS DE DEFINICIÓN DE TAREAS EN AIRFLOW
                                     │
           ┌─────────────────────────┴─────────────────────────┐
           ▼                                                   ▼
   OPERADORES CLÁSICOS (Instanciación)                TASKFLOW API (Decoradores)
   • `BashOperator(task_id='...', ...)`               • `@task` / `@dag` (Airflow 2.0+)
   • `SQLExecuteQueryOperator(...)`                  • Sintaxis Python pura y limpia
   • Ideal para infraestructura y Bash                • Ideal para transformaciones Python
   • Conexión mediante operadores `>>`                • Conexión mediante retorno de variables
```

### A. Operadores Clásicos
Se instancian como clases de Python. Siguen siendo indispensables cuando ejecutamos comandos de terminal, scripts de shell externos, contenedores Docker aislados (`DockerOperator`) o consultas SQL directas *in-warehouse*.

```python
from datetime import timedelta
from airflow.operators.bash import BashOperator

# Instanciación de Operador Clásico
ejecutar_dbt = BashOperator(
    task_id='ejecutar_transformacion_dbt',
    bash_command='dbt run --profiles-dir /opt/airflow/dbt --select +fct_ventas+',
    execution_timeout=timedelta(minutes=30)
)
```

### B. TaskFlow API (Decoradores `@task`)
Introducida en Airflow 2.0, convierte funciones de Python nativas en tareas de Airflow mediante el decorador `@task`. Simplifica enormemente el pasaje de datos entre tareas y elimina el código repetitivo (*boilerplate*).

```python
from airflow.decorators import task

@task(task_id='validar_calidad_payload')
def validar_payload(data: dict) -> bool:
    if not data.get("registros"):
        raise ValueError("Payload vacío.")
    return True
```

---

## 2. Configuración de Parámetros Defensivos (`default_args`)

Para evitar que una tarea colgada consuma indefinidamente los recursos del cluster o que un fallo temporal detenga todo el pipeline de negocio, definimos políticas de resiliencia centralizadas dentro del diccionario `default_args`:

```python
from datetime import datetime, timedelta

default_args = {
    'owner': 'data_engineering_team',
    'depends_on_past': False,              # No bloquea la ejecución si la fecha anterior falló
    'email_on_failure': True,              # Notifica por correo ante fallos en producción
    'email': ['alertas-de@empresa.com'],
    'retries': 3,                          # Reintentos automáticos (3 intentos en total)
    'retry_delay': timedelta(minutes=5),   # Esperar 5 minutos entre cada reintento
    'retry_exponential_backoff': True,    # Incrementa el tiempo entre reintentos (5m, 10m, 20m)
    'max_retry_delay': timedelta(hours=1), # Límite máximo de espera
    'execution_timeout': timedelta(minutes=15), # MÁXIMO tiempo permitido antes de abortar la tarea
}
```

### Atributos Defensivos Clave:
* **`execution_timeout`:** Si una consulta SQL o extracción de API queda colgada, Airflow cancela la tarea automáticamente al cumplir este tiempo, evitando tareas "zombie".
* **`retry_exponential_backoff`:** Evita saturar un servidor de origen que está caído. En lugar de reintentar cada minuto en ráfaga, duplica el tiempo de espera gradualmente.

---

## 3. Control Elegante de Excepciones: `AirflowSkipException`

En ciertos escenarios de producción, que una tarea no encuentre datos nuevos no constituye un error.

Por ejemplo, si un scraper o una API no devuelve datos para un día festivo, no queremos que la tarea falle y envíe alertas de emergencia. En su lugar, utilizamos `AirflowSkipException` para marcar la tarea como **SKIPPED (Omitida)** y permitir que el DAG continúe limpiamente sin fallar:

```python
from airflow.exceptions import AirflowSkipException
from airflow.decorators import task

@task()
def extraer_datos_incremental(fecha_proceso: str):
    datos = consultar_api_remota(fecha_proceso)

    if len(datos) == 0:
        # Marca la tarea como SKIPPED en lugar de FAILED
        raise AirflowSkipException(f"No hay datos nuevos para procesar en la fecha {fecha_proceso}.")

    return datos
```

---

## 4. Código Completo de un DAG Defensivo de Producción

A continuación se muestra un DAG completo que combina la TaskFlow API, el `BashOperator`, reintentos exponenciales y control de saltos:

```python
from datetime import datetime, timedelta
from airflow.decorators import dag, task
from airflow.operators.bash import BashOperator
from airflow.exceptions import AirflowSkipException

# 1. Configuración de Parámetros Defensivos Globales
default_args = {
    'owner': 'data_engineer_ssr',
    'retries': 2,
    'retry_delay': timedelta(minutes=2),
    'retry_exponential_backoff': True,
    'execution_timeout': timedelta(minutes=10),
}

# 2. Definición del DAG
@dag(
    dag_id='dag_defensivo_ingesta_medallion_v2',
    default_args=default_args,
    start_date=datetime(2026, 1, 1),
    schedule='0 3 * * *',  # Ejecutar todos los días a las 03:00 AM
    catchup=False,
    tags=['production', 'medallion', 'defensive']
)
def pipeline_ingesta_defensivo():

    # Tarea 1 (TaskFlow API): Ingesta Bronze desde API con validación
    @task(task_id='extraer_api_bronze')
    def extraer_api_bronze() -> dict:
        # Simulación de respuesta de API
        registros_obtenidos = 150  # Si fuera 0, podríamos lanzar AirflowSkipException

        if registros_obtenidos == 0:
            raise AirflowSkipException("Cero registros encontrados. Omitiendo downstream.")

        return {"status": "SUCCESS", "records_count": registros_obtenidos}

    # Tarea 2 (BashOperator Clásico): Ejecución de dbt en Capa Silver/Gold
    ejecutar_dbt_silver = BashOperator(
        task_id='ejecutar_transformacion_dbt_silver',
        bash_command='echo "Ejecutando dbt run --select stg_ventas+ en container de dbt..."',
        execution_timeout=timedelta(minutes=20)
    )

    # Tarea 3 (TaskFlow API): Notificación o Auditoría Final
    @task(task_id='auditar_resultado_final')
    def auditar_resultado(resultado_bronze: dict):
        print(f"Auditoría completada exitosamente. Registros procesados: {resultado_bronze['records_count']}")

    # Definición de Flujo de Dependencias Mixtas (TaskFlow + Operador Clásico)
    datos_bronze = extraer_api_bronze()

    # Conexión entre TaskFlow API y Operador Clásico
    datos_bronze >> ejecutar_dbt_silver >> auditar_resultado(datos_bronze)

# Instanciación
dag_instance = pipeline_ingesta_defensivo()
```

---

## 🏋️‍♂️ Práctica de la Lección 02

1. Ubicate en la carpeta `practica/modulo_07/` de tu repositorio local.
2. Creá el archivo `ej_02_dags_defensivos.py`.
3. Escribí un script Python que simule el motor de reintentos exponenciales y manejo de excepciones `AirflowSkipException` de Airflow:

```python
import time
from datetime import timedelta

class AirflowTaskRunnerSimulator:
    def __init__(self, retries: int = 2, delay_seconds: int = 1):
        self.retries = retries
        self.delay_seconds = delay_seconds

    def run_task(self, task_name: str, task_func, *args, **kwargs):
        attempt = 0
        current_delay = self.delay_seconds

        while attempt <= self.retries:
            attempt += 1
            print(f"🚀 [Runner] Ejecutando Task '{task_name}' (Intento {attempt}/{self.retries + 1})...")
            try:
                result = task_func(*args, **kwargs)
                print(f"✅ [Runner] Task '{task_name}' FINALIZADA CON ÉXITO.")
                return result
            except Exception as e:
                if "SKIP" in str(e):
                    print(f"🟡 [Runner] Task '{task_name}' OMITIDA (SKIPPED): {e}")
                    return "SKIPPED"

                print(f"❌ [Runner] Error en Task '{task_name}': {e}")
                if attempt <= self.retries:
                    print(f"⏳ [Backoff] Esperando {current_delay}s antes del reintento...")
                    time.sleep(current_delay)
                    current_delay *= 2  # Exponential Backoff
                else:
                    print(f"💥 [Runner] Task '{task_name}' COLLAPSED. Reintentos agotados.")
                    raise e

# Funciones de prueba
def funcion_inestable():
    import random
    if random.random() < 0.7:  # 70% de probabilidad de fallar
        raise ConnectionError("Timeout al conectar con la API remota.")
    return "Datos recibidos correctamente"

def funcion_vacia():
    raise Exception("SKIP: No se encontraron registros nuevos en la fuente.")

# Pruebas
runner = AirflowTaskRunnerSimulator(retries=2, delay_seconds=1)

print("=== PRUEBA 1: TAREA INESTABLE CON REINTENTOS ===")
try:
    runner.run_task("extraer_api_inestable", funcion_inestable)
except Exception:
    print("Manejando fallo definitivo en DAG...")

print("\n=== PRUEBA 2: TAREA CON SALTO ELEGANTE (SKIPPED) ===")
runner.run_task("extraer_api_vacia", funcion_vacia)
```

4. Agregá comentarios al final del archivo respondiendo:
   * **Consigna A:** ¿Qué diferencia existe en el flujo de ejecución de un DAG cuando una tarea lanza una excepción genérica (`Exception`) versus cuando lanza una `AirflowSkipException`?
   * **Consigna B:** ¿Por qué es una mala práctica dejar tareas sin configurar el parámetro `execution_timeout` en un entorno de producción?