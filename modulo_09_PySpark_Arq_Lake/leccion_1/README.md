# 🚀 Lección 01: Arquitectura de Procesamiento Distribuido en Apache Spark (Driver, Executors, RDDs, DataFrames)

En los módulos anteriores aprendiste a procesar datos en una sola computadora con Python y Polars (Módulo 01), optimizar bases de datos relacionales (Módulo 02), empaquetar entornos con Docker (Módulo 03), diseñar Data Warehouses Medallón (Módulo 04), transformar modelos con dbt (Módulo 05), implementar Data Contracts (Módulo 06), orquestar con Airflow (Módulo 07) y garantizar la calidad con DataOps y Observabilidad (Módulo 08).

Llegamos al módulo culminante de la formación de Data Engineer Ssr: **PySpark y Arquitectura Lakehouse**.

A partir de este punto, dejamos atrás los entornos donde los datos entran en la memoria RAM de un único servidor y aprendemos a procesar Terabytes o Petabytes de datos distribuidos en un clúster de decenas o cientos de computadoras.

---

## 1. Escalado Vertical vs. Escalado Horizontal (Procesamiento Distribuido)

Cuando trabajamos con herramientas monolíticas como Pandas o motores relacionales tradicionales, el procesamiento depende de una única máquina:

```text
ESCALADO VERTICAL (Single-Node - Pandas / PostgreSQL):
[ Servidor Único ] ──► Para procesar más datos, se compra una máquina más grande.
                       • Límite físico de RAM y CPU.
                       • Si el archivo pesa 500 GB y la máquina tiene 64 GB de RAM: Out-Of-Memory (OOM).

ESCALADO HORIZONTAL (Distributed - Apache Spark Clúster):
[ Driver Node ] ──► Coordina a N Workers
                       ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
                       │  Worker 01   │  │  Worker 02   │  │  Worker 03   │
                       │ (RAM + CPU)  │  │ (RAM + CPU)  │  │ (RAM + CPU)  │
                       └──────────────┘  └──────────────┘  └──────────────┘
                       • Escalabilidad casi infinita agregando nodos económicos al clúster.
```

### ¿Por qué nació Apache Spark?
Apache Spark es el motor de procesamiento distribuido en memoria más rápido y utilizado del mundo. Reemplazó al antiguo modelo Hadoop MapReduce porque realiza las transformaciones directamente en la memoria RAM (hasta 100 veces más rápido que escribir en disco entre cada etapa).

---

## 2. La Arquitectura Clúster de Apache Spark

Spark opera bajo una arquitectura Master-Worker (Driver / Executors):

```text
                           ARQUITECTURA DE APACHE SPARK
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                         │
│   ┌────────────────────────────────┐                 ┌──────────────────────────────┐   │
│   │          DRIVER NODE           │                 │       CLUSTER MANAGER        │   │
│   │  • SparkSession                │ ──────────────► │ (YARN / Kubernetes / Stand)  │   │
│   │  • Convierte código en DAG     │                 │ Asigna recursos al clúster   │   │
│   │  • Scheduler & Catalyst        │                 └──────────────┬───────────────┘   │
│   └──────────────┬─────────────────┘                                │                   │
│                  │                                                  │                   │
│                  └──────────────────────────┬───────────────────────┘                   │
│                                             │                                           │
│                                             ▼                                           │
│                 ┌──────────────────────────────────────────────────────┐                │
│                 │                   WORKER NODES                       │                │
│                 │  ┌────────────────────┐    ┌────────────────────┐    │                │
│                 │  │    EXECUTOR 1      │    │    EXECUTOR 2      │    │                │
│                 │  │ (Core / Task Threads)│  │ (Core / Task Threads)│  │                │
│                 │  └────────────────────┘    └────────────────────┘    │                │
│                 └──────────────────────────────────────────────────────┘                │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

### Componentes Clave:
* **Driver Node (El Cerebro):**
  * Ejecuta el proceso principal (`SparkSession` y el código Python del usuario).
  * Convierte las transformaciones del usuario en un DAG (*Directed Acyclic Graph*) de ejecución.
  * Planifica las tareas (*Tasks*) y las distribuye a los Executors.
* **Cluster Manager (El Asignador de Recursos):**
  * Administra la infraestructura del clúster (Apache YARN, Kubernetes o Spark Standalone).
  * Asigna la memoria RAM y los núcleos de CPU (vCPUs) que utilizará la aplicación.
* **Executor Nodes (Los Trabajadores):**
  * Procesos que corren en los nodos Workers.
  * Ejecutan las tareas asignadas por el Driver en hilos paralelos (*Tasks*).
  * Almacenan en memoria RAM (*In-Memory Caching*) las particiones de datos asignadas.

---

## 3. La Evolución de las Abstracciones en Spark: De RDDs a DataFrames

A lo largo de su historia, Spark ha evolucionado la forma en que los ingenieros manipulan datos distribuidos:

```text
                  EVOLUCIÓN DE ABSTRACCIONES EN SPARK
                                   │
         ┌─────────────────────────┴─────────────────────────┐
         ▼                                                   ▼
   RDD (Resilient Distributed Dataset)                SPARK DATAFRAME / SQL
   • Bajo nivel (Spark 1.0 - Años 2014)               • Alto nivel (Spark 2.0 / 3.0+)
   • Colección de objetos Python/Java                 • Estructura tabular (filas y columnas)
   • Sin esquema estricto ni optimizador              • Altamente optimizado por Catalyst
   • Lento de optimizar manualmente                   • Sintaxis equivalente a Pandas y SQL
```

### A. RDD (Resilient Distributed Dataset)
Es la unidad fundamental de datos en Spark. Representa una colección de objetos dividida en particiones distribuidas a través de los nodos del clúster. Es resiliente porque si un nodo Worker falla, Spark reconstruye la partición perdida automáticamente utilizando el historial del DAG.

### B. Spark DataFrames
Un DataFrame es una capa de abstracción construida sobre los RDDs, pero organizada en columnas con tipos de datos definidos (esquema). Al tener estructura, el motor de Spark puede aplicar el **Catalyst Optimizer** para reescribir y optimizar la consulta automáticamente antes de ejecutarla.

---

## 4. Inicialización de PySpark (SparkSession)

El punto de entrada para trabajar con PySpark en cualquier aplicación es la `SparkSession`:

```python
from pyspark.sql import SparkSession

# Creación de la SparkSession
spark = SparkSession.builder \
    .appName("Modulo09_Leccion01_IntroduccionSpark") \
    .master("local[*]") \
    .config("spark.driver.memory", "4g") \
    .getOrCreate()

print(f"Spark Version: {spark.version}")
```

---

## 🏋️‍♂️ Práctica de la Lección 01

1. Ubicate en la carpeta `practica/modulo_09/` de tu repositorio local.
2. Creá el archivo `ej_01_arquitectura_pyspark.py`.
3. Escribí un script Python que simule el reparto de tareas de un Driver Node entre $N$ Executors sobre un RDD/DataFrame particionado:

```python
import time
from typing import List, Dict

# Simulación de Particiones distribuidas en N Executors
class SparkClusterSimulator:
    def __init__(self, num_executors: int):
        self.num_executors = num_executors
        self.executors = {f"Executor_{i+1}": [] for i in range(num_executors)}

    def distribute_dataset(self, data: List[Dict]):
        print(f"🚀 [DRIVER NODE] Particionando {len(data)} registros entre {self.num_executors} Executors...")

        # Round-Robin para simular la partición de un RDD/DataFrame
        for idx, record in enumerate(data):
            executor_key = f"Executor_{(idx % self.num_executors) + 1}"
            self.executors[executor_key].append(record)

        for exec_id, partition in self.executors.items():
            print(f"  • {exec_id} recibió Partición con {len(partition)} registros.")

    def run_parallel_task(self, transformation_func):
        print("\n⚡ [DRIVER NODE] Enviando Tareas (Tasks) a los Executors en paralelo...")
        results = []

        for exec_id, partition in self.executors.items():
            print(f"  ▶️ {exec_id} ejecutando transformación sobre su partición en RAM...")
            # Cada Executor procesa su partición de forma aislada
            exec_result = [transformation_func(row) for row in partition]
            results.extend(exec_result)

        print("✅ [DRIVER NODE] Resultados recolectados (Action collect() completada).")
        return results

# Datos de Prueba (Simulación de Ingesta)
lote_datos = [
    {"transaccion_id": i, "monto_usd": i * 10.5, "estado": "COMPLETADA"}
    for i in range(1, 13)
]

# Transformación de prueba
def calcular_impuesto(row: dict) -> dict:
    row["impuesto_usd"] = round(row["monto_usd"] * 0.21, 2)
    return row

# Ejecución del Simulador
spark_sim = SparkClusterSimulator(num_executors=3)
spark_sim.distribute_dataset(lote_datos)
datos_procesados = spark_sim.run_parallel_task(calcular_impuesto)

print(f"\nMuestra de Resultado Final (Driver): {datos_procesados[:2]}")
```

4. Agregá comentarios al final del archivo respondiendo:
   * **Consigna A:** ¿Cuál es la función del Driver Node en la arquitectura de Apache Spark y por qué no debe usarse para almacenar datasets masivos en su memoria interna?
   * **Consigna B:** Explica la diferencia entre un RDD y un DataFrame en Spark y por qué los DataFrames ofrecen un rendimiento superior gracias al Catalyst Optimizer.