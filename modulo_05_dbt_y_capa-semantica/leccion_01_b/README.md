# ⚡ Lección 01.B (Módulo 05): Arquitectura Interna de Apache Spark: Driver, Executors, DAG y Tungsten

&gt; **Propósito**: Comprender a profundidad la arquitectura distribuida de Apache Spark, el ciclo de vida de ejecución de trabajos (Jobs, Stages, Tasks), las optimizaciones del Catalyst Optimizer y Project Tungsten, y la gestión unificada de memoria en los Executors.

---

## 📌 1\. Arquitectura de Clúster en Apache Spark

Apache Spark sigue una arquitectura **Master-Worker** distribuida para procesar datos a gran escala:

```
                          [ DRIVER NODE ]
             ┌───────────────────────────────────────┐
             │ SparkSession / SparkContext           │
             │ DAGScheduler &amp; TaskScheduler          │
             └──────────────────┬────────────────────┘
                                │
                     [ CLUSTER MANAGER ]
             (YARN / Kubernetes / Standalone / Mesos)
                                │
            ┌───────────────────┴───────────────────┐
            ▼                                       ▼
  [ WORKER NODE 1 ]                       [ WORKER NODE 2 ]
┌──────────────────────┐                ┌──────────────────────┐
│ Executor 1 (JVM)     │                │ Executor 2 (JVM)     │
│ ├── Task 1  Task 2   │                │ ├── Task 3  Task 4   │
│ └── BlockManager     │                │ └── BlockManager     │
└──────────────────────┘                └──────────────────────┘

```

### Componentes Clave:

1. **Driver Node**: El nodo maestro que ejecuta la función `main()`, crea la `SparkSession`, convierte el código en un **DAG (Directed Acyclic Graph)** y distribuye las tareas a los workers.
2. **Cluster Manager**: El orquestador de recursos (Kubernetes, YARN o Standalone) encargado de reservar memoria y CPUs en los nodos físicos.
3. **Executors**: Procesos JVM que corren en los Worker Nodes. Ejecutan las **Tasks** en paralelo, almacenan datos en caché (*Storage*) y realizan cómputos en memoria (*Execution*).

---

## 🔬 2\. El Ciclo de Ejecución: Transformaciones Lazy, Jobs, Stages y Tasks

En Spark, nada se ejecuta en el clúster hasta que se invoca una **Acción**.

```
[ Código PySpark ] ─── Transformaciones (Lazy) ───&gt; [ DAG Plan ] ─── Acción (count, collect) ───&gt; [ Job ]
                                                                                                      │
                                                                                                      ▼
                                                                                                 [ Stages ]
                                                                                                (Shuffle Boundaries)
                                                                                                      │
                                                                                                      ▼
                                                                                                 [ Tasks ]
                                                                                                (Paralelo por Partición)

```

### Conceptos Clave del Runtime:

* **Transformaciones (Lazy Evaluation)**: Operaciones como `.filter()`, `.select()` o `.map()`. No leen ni procesan datos inmediatamente; solo construyen el plan de ejecución lógico.
* **Acciones**: Operaciones como `.collect()`, `.count()`, `.write()` o `.show()`. Desencadenan la ejecución real en el clúster.
* **Job**: La unidad de trabajo creada cuando se ejecuta una Acción.
* **Stage**: Un conjunto de tareas que se pueden ejecutar en paralelo sin reordenar datos entre nodos. Un nuevo *Stage* se crea cada vez que ocurre un **Shuffle** (reorganización de datos en la red, ej. `.groupBy()`, `.join()`).
* **Task**: La unidad mínima de ejecución enviada a un solo hilo de un Executor para procesar **una sola partición de datos**.

---

## 🛠️ 3\. El Motor de Optimización: Catalyst Optimizer y Project Tungsten

Spark DataFrame y Spark SQL no ejecutan el código de Python directamente. Pasan por dos motores de optimización masivos en Scala/Java:

### A. Catalyst Optimizer (Optimizador de Consultas)

Pasa por 4 fases secuenciales:

1. **Unresolved Logical Plan**: Verifica la sintaxis.
2. **Logical Plan**: Valida nombres de columnas y tipos de datos mediante el *Catalog*.
3. **Optimized Logical Plan**: Aplica reglas de optimización como *Constant Folding*, *Predicate Pushdown* (filtrar antes de leer) y *Projection Pruning* (seleccionar solo columnas necesarias).
4. **Physical Plan**: Genera múltiples planes físicos de ejecución (ej. elegir entre *Broadcast Hash Join* o *Sort Merge Join*) y selecciona el de menor costo estimado.

### B. Project Tungsten (Eficiencia de Memoria y CPU)

* **Off-Heap Memory Management**: Almacena datos como arreglos de bytes binarios fuera del Heap de la JVM, eliminando el overhead de GC (Garbage Collection) y reduciendo el consumo de RAM.
* **Whole-Stage Code Generation**: Fusiona múltiples operaciones de un Stage en un solo bloque de código máquina en Bytecode de Java, eliminando llamadas a funciones virtuales y aprovechando los registros de la CPU.

---

## ⚡ 4\. Unified Memory Manager en los Executors

La memoria asignada a cada Executor (JVM) se divide dinámicamente mediante el **Unified Memory Manager**:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ EXECUTOR MEMORY (JVM HEAP)                                                  │
│                                                                             │
│ ┌──────────────────────────────────────┬──────────────────────────────────┐ │
│ │ Unified Memory Pool (80% default)    │ User Memory (20%)                │ │
│ │ ┌──────────────────┬───────────────┐ │ (Estructuras de datos custom,    │ │
│ │ │ Storage Memory   │ Execution Mem │ │  Ratios de métricas de usuario)  │ │
│ │ │ (Caché/Broadcast)│ (Shuffles/Join)│ │                                  │ │
│ │ └──────────────────┴───────────────┘ │ Reserved Memory (300 MB)         │ │
│ └──────────────────────────────────────┴──────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘

```

* **Execution Memory**: Usada para transformaciones en vuelo, shuffles, joins y agrupaciones.
* **Storage Memory**: Usada para guardar DataFrames cacheados (`.cache()`, `.persist()`) y variables broadcast.
* Ten en cuenta el límite dinámico: si no hay datos cacheados en *Storage*, *Execution* puede tomar hasta el 100% de la memoria unificada.

---

## 🏋️‍♂️ Ejercicio Práctico Hands-On: Inspección del Plan Físico con `.explain()`

Crea el archivo `inspeccion_spark.py` para visualizar cómo el Catalyst Optimizer transforma tu código en un plan físico:

```
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

# 1. Crear SparkSession Local
spark = (
    SparkSession.builder.appName("CatalystInspection")
    .master("local[*]")
    .getOrCreate()
)

# 2. Generar DataFrame de prueba
df_ventas = spark.range(1, 1_000_001).select(
    F.col("id").alias("venta_id"),
    (F.col("id") % 10).alias("categoria_id"),
    (F.col("id") * 15.5).alias("monto"),
)

# 3. Aplicar transformaciones
df_filtrado = (
    df_ventas.filter(F.col("monto") &gt; 500.0)
    .filter(F.col("categoria_id") == 5)
    .groupBy("categoria_id")
    .agg(F.sum("monto").alias("monto_total"))
)

# 4. Imprimir el plan físico optimizado
print("=== PLAN FÍSICO DE EJECUCIÓN (CATALYST OPTIMIZER) ===")
df_filtrado.explain(extended=True)

spark.stop()

```

---

## 🧠 Checkpoint de Autoevaluación

1. ¿Cuál es la responsabilidad del *Driver Node* frente a la responsabilidad de los *Worker/Executors* en un clúster de Spark?
2. ¿Por qué las **Transformaciones** en Spark son *Lazy* y qué evento desencadena la creación de un **Job**?
3. Explica qué es un **Stage** y qué tipo de operaciones marcan el límite entre un Stage y el siguiente.
4. ¿Qué problema de la JVM resuelve el módulo **Project Tungsten** mediante el manejo de memoria *Off-Heap*?