# 🚀 Lección 01: Arquitectura de Apache Airflow (Scheduler, Webserver, Workers, Executor, DAGs)

En los módulos anteriores aprendiste a procesar datos con Python y Polars (Módulo 01), optimizar bases de datos (Módulo 02), contenedorizar entornos con Docker (Módulo 03), diseñar Data Warehouses en capas Medallón (Módulo 04), transformar datos con dbt (Módulo 05) y gobernar la calidad con Data Contracts (Módulo 06).

Ahora surge una pregunta crítica de producción: **¿Quién ejecuta todos estos componentes en el orden correcto, a la hora adecuada y reintenta automáticamente si una API o base de datos falla?**

En este Módulo 07 aprenderemos a dominar la herramienta estándar mundial de orquestación de flujos de datos: **Apache Airflow**.

---

## 1. El Problema de Cron y la Necesidad de un Orquestador

En los inicios de la ingeniería de datos, las empresas programaban sus scripts con la utilidad de sistema `cron` (Crontab):

```bash
# Ejemplo de Crontab tradicional:
0 2 * * * python /scripts/extraer_api.py
0 3 * * * python /scripts/transformar_dbt.py
```

### ¿Por qué cron falla en producción?
* **Sin Gestión de Dependencias Reales:** Si `extraer_api.py` tarda más de 1 hora por un volumen imprevisto, `transformar_dbt.py` arrancará a las 3:00 AM sobre datos incompletos o corruptos.
* **Sin Visibilidad ni Interfaz Gráfica:** No hay un panel centralizado para ver qué scripts fallaron, cuáles están corriendo o cuánto tardaron.
* **Sin Reintentos Inteligentes (*Retries*):** Si la conexión a la API cae por 30 segundos, el script falla y no se recupera hasta el día siguiente.
* **Sin Manejo de Estado ni Historial:** No existe una base de datos de auditoría que registre el estado de cada ejecución del pasado.

### La Solución: Un Orquestador de Flujos de Trabajo
Un Orquestador no ejecuta el procesamiento pesado en sí mismo, sino que actúa como el **"director de orquesta"**: coordina la secuencia de ejecución, gestiona dependencias entre tareas, maneja reintentos ante fallos y proporciona alertas y observabilidad en tiempo real.

---

## 2. Los 5 Componentes de la Arquitectura de Apache Airflow

Airflow es una plataforma distribuida compuesta por 5 componentes fundamentales que trabajan en equipo:

```text
                               ARQUITECTURA DE APACHE AIRFLOW
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                         │
│     ┌──────────────────┐           ┌──────────────────┐           ┌──────────────────┐  │
│     │    WEBSERVER     │           │    SCHEDULER     │           │   METADATABASE   │  │
│     │ (Interfaz UI)    │           │ (Cerebro/Clock)  │           │(PostgreSQL/MySQL)│  │
│     └────────┬─────────┘           └────────┬─────────┘           └────────┬─────────┘  │
│              │                              │                              │            │
│              └──────────────────────────────┼──────────────────────────────┘            │
│                                             │                                           │
│                                             ▼                                           │
│                                    ┌──────────────────┐                                 │
│                                    │     EXECUTOR     │                                 │
│                                    │(Celery/K8s/Local)│                                 │
│                                    └────────┬─────────┘                                 │
│                                             │                                           │
│                                             ▼                                           │
│                                    ┌──────────────────┐                                 │
│                                    │     WORKERS      │                                 │
│                                    │(Ejecutan tareas) │                                 │
│                                    └──────────────────┘                                 │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

### 1. Webserver (Interfaz Gráfica - UI)
Es una aplicación web en Flask que expone un panel interactivo. Permite a los ingenieros y analistas inspeccionar la ejecución de los DAGs, revisar logs de errores en tiempo real, pausar/activar flujos y reejecutar tareas manualmente.

### 2. Scheduler (El Cerebro del Sistema)
Es un proceso daemon que monitorea constantemente todos los DAGs definidos en el código. Evalúa los intervalos de tiempo y las dependencias entre tareas. Cuando una tarea está lista para ejecutarse, la envía a la cola del Executor.

### 3. Metadatabase (Base de Datos de Estado)
Base de datos relacional (habitualmente PostgreSQL o MySQL) donde Airflow almacena el estado completo del sistema: credenciales (*Connections*), variables, usuarios, historial de ejecuciones y estados de las tareas (`queued`, `running`, `success`, `failed`).

### 4. Executor (El Mecanismo de Distribución)
Define cómo y dónde se asignan las tareas para su procesamiento:
* **SequentialExecutor:** Ejecuta una sola tarea a la vez en un solo hilo (solo para pruebas locales).
* **LocalExecutor:** Corre múltiples tareas en paralelo utilizando la capacidad multihilo del mismo servidor.
* **CeleryExecutor / KubernetesExecutor:** Nivel Enterprise. Distribuye la carga de tareas dinámicamente en clusters de múltiples servidores o pods de Kubernetes.

### 5. Workers (Los Nodos de Ejecución)
Son los procesos o contenedores físicos que levantan las tareas de la cola y ejecutan el código real en Python, Bash, SQL o llamadas a Docker/dbt.

---

## 3. Conceptos Clave: DAG, Operator, Task y Task Instance

```text
                  CONCEPTOS FUNDAMENTALES DE AIRFLOW
┌────────────────────────────────────────────────────────────────────┐
│ DAG (Grafo Acíclico Dirigido)                                      │
│                                                                    │
│  [ Task A: Extraer API ] ──► [ Task B: Transformar ] ──► [ Task C ]│
│   (PythonOperator)            (BashOperator/dbt)        (EmailOp)  │
└────────────────────────────────────────────────────────────────────┘
```

* **DAG (*Directed Acyclic Graph*):** Es el flujo completo representado como un Grafo Acíclico Dirigido. Es "dirigido" porque sigue un sentido claro de ejecución (de A a B) y "acíclico" porque no permite bucles infinitos (una tarea no puede volver a ejecutarse a sí misma en el mismo ciclo).
* **Operator (Operador):** Es la plantilla reutilizable que define qué tipo de trabajo realiza una tarea (ej. `PythonOperator` para código Python, `BashOperator` para comandos de terminal, `SQLExecuteQueryOperator` para consultas en base de datos).
* **Task (Tarea):** Es un nodo dentro del DAG que instancia a un Operador.
* **Task Instance (Instancia de Tarea):** Es la combinación de una Tarea individual ejecutándose en un punto específico en el tiempo (`logical_date`). Posee un estado propio (`running`, `success`, `failed`, `up_for_retry`).

---

## 4. Anatomía de un DAG Moderno con TaskFlow API

A partir de Airflow 2.0, la forma estándar recomendada para definir pipelines en Python es la **TaskFlow API**, que utiliza decoradores (`@dag`, `@task`) para escribir código limpio y legible:

```python
from datetime import datetime, timedelta
from airflow.decorators import dag, task

# Configuración por defecto para todas las tareas del DAG
default_args = {
    'owner': 'data_engineering_team',
    'retries': 2,                          # Reintentar 2 veces si falla
    'retry_delay': timedelta(minutes=5),  # Esperar 5 minutos entre reintentos
}

@dag(
    dag_id='pipeline_ingesta_ecommerce_v1',
    default_args=default_args,
    start_date=datetime(2026, 1, 1),
    schedule='@daily',                     # Ejecución diaria a la medianoche
    catchup=False,                         # No ejecutar fechas pasadas al activar
    tags=['medallion', 'ecommerce']
)
def pipeline_ecommerce():

    @task()
    def extraer_datos_api() -> dict:
        # Simulación de extracción de datos de la fuente
        return {"ventas": [100, 250, 80], "total": 430}

    @task()
    def transformar_datos(payload: dict) -> float:
        # Transformación en la capa Silver
        total_usd = float(payload["total"]) * 1.05  # Aplicando impuesto
        return total_usd

    @task()
    def cargar_data_warehouse(monto_final: float):
        # Carga en la capa Gold
        print(f"Cargando ${monto_final} USD en la Fact Table de PostgreSQL.")

    # Definición explícita del flujo de dependencias
    datos_raw = extraer_datos_api()
    monto_procesado = transformar_datos(datos_raw)
    cargar_data_warehouse(monto_procesado)

# Instanciación del DAG
pipeline_dag = pipeline_ecommerce()
```

---

## 🏋️‍♂️ Práctica de la Lección 01

1. Ubicate en la carpeta `practica/modulo_07/` de tu repositorio local.
2. Creá el archivo `ej_01_arquitectura_airflow.py`.
3. Escribí un script Python que simule el mecanismo interno del Scheduler y la Metadatabase de Airflow, cambiando los estados de un DAG simulado:

```python
import time
from enum import Enum

# Estados oficiales de una Task Instance en Airflow
class TaskState(Enum):
    NONE = "none"
    SCHEDULED = "scheduled"
    QUEUED = "queued"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"

class AirflowSchedulerSimulator:
    def __init__(self, dag_id: str):
        self.dag_id = dag_id
        self.tasks = {}
        self.state_history = []

    def add_task(self, task_id: str, dependencies: list = None):
        self.tasks[task_id] = {
            "state": TaskState.NONE,
            "dependencies": dependencies or []
        }

    def _update_state(self, task_id: str, new_state: TaskState):
        self.tasks[task_id]["state"] = new_state
        self.state_history.append((task_id, new_state.value))
        print(f"🔄 [Metadatabase] Task '{task_id}' cambio estado a ➔ {new_state.value.upper()}")

    def run_dag(self):
        print(f"🚀 [Scheduler] Iniciando DAG Run para: '{self.dag_id}'")

        for task_id, task_info in self.tasks.items():
            # 1. Verificar dependencias
            deps = task_info["dependencies"]
            for dep in deps:
                if self.tasks[dep]["state"] != TaskState.SUCCESS:
                    print(f"⏳ [Scheduler] Task '{task_id}' bloqueada esperando a '{dep}'")
                    return

            # 2. Transiciones de Estado (Scheduler -> Executor -> Worker)
            self._update_state(task_id, TaskState.SCHEDULED)
            self._update_state(task_id, TaskState.QUEUED)
            self._update_state(task_id, TaskState.RUNNING)

            # Simulación de ejecución exitosa
            time.sleep(0.5)
            self._update_state(task_id, TaskState.SUCCESS)

        print(f"✅ [Scheduler] DAG Run '{self.dag_id}' FINALIZADO CON ÉXITO.")

# Ejecución de la prueba
scheduler = AirflowSchedulerSimulator("dag_etl_medallion")

# Registrar tareas con dependencias (Extraer -> Transformar -> Cargar)
scheduler.add_task("extraer_bronze")
scheduler.add_task("limpiar_silver", dependencies=["extraer_bronze"])
scheduler.add_task("cargar_gold", dependencies=["limpiar_silver"])

scheduler.run_dag()
```

4. Agregá comentarios al final del archivo respondiendo:
   * **Consigna A:** ¿Qué componente de Airflow es el responsable de guardar la contraseña cifrada de la base de datos de destino y el historial de ejecuciones de un DAG?
   * **Consigna B:** Explica por qué en una arquitectura distribuida de producción se utiliza `CeleryExecutor` o `KubernetesExecutor` en lugar de `SequentialExecutor`.