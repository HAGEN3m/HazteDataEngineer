# ⚡ Lección 02.B (Módulo 05): Spark Shuffles, Particionamiento y Optimización Avanzada (AQE, DPP, Broadcast Joins)

&gt; **Propósito**: Dominar el comportamiento físico de los reordenamientos de datos (*Shuffles*) en Apache Spark, diferenciar las transformaciones estrechas de las anchas (*Narrow vs. Wide Transformations*), y aplicar técnicas avanzadas de optimización en tiempo de ejecución (**Adaptive Query Execution - AQE**, **Dynamic Partition Pruning - DPP** y **Broadcast Hash Joins**) para eliminar cuellos de botella en procesamiento masivo.

---

## 📌 1\. Transformaciones Estrechas vs. Anchas (Narrow vs. Wide Transformations)

En Apache Spark, las operaciones sobre DataFrames y RDDs se clasifican según el movimiento de datos a través de la red de los *Executors*:

```
Transformación Estrecha (Narrow):             Transformación Ancha (Wide / Shuffle):
Executor 1: [Fila 1, 2] -&gt; [Fila 1, 2]          Executor 1: [Clave A, Clave B] \   / Executor 1: [Clave A, Clave A]
Executor 2: [Fila 3, 4] -&gt; [Fila 3, 4]          Executor 2: [Clave A, Clave B]  X  
                                                Executor 3: [Clave B, Clave A] /   \ Executor 2: [Clave B, Clave B]
(Cada partición se procesa de forma aislada)      (Intercambio de datos a través de la red)

```

### A. Transformaciones Estrechas (*Narrow Transformations*)

* **Mecanismo**: Cada partición de entrada contribuye a **exactamente una** partición de salida. No hay intercambio de datos por la red entre distintas máquinas.
* **Operaciones**: `select()`, `filter()`, `withColumn()`, `drop()`, `union()`, `flatMap()`.
* **Impacto**: Se ejecutan dentro de un mismo **Stage** en paralelo sin bloqueo de I/O.

### B. Transformaciones Anchas (*Wide Transformations*)

* **Mecanismo**: Múltiples particiones de entrada necesitan redistribuir sus datos entre todas las máquinas del clúster basándose en una clave de agrupación o unión.
* **Operaciones**: `groupBy()`, `join()`, `distinct()`, `repartition()`, `reduceByKey()`.
* **Impacto**: Desencadenan un **Shuffle**, dividiendo la ejecución en un nuevo **Stage**.

---

## 🔬 2\. Anatomía de un Spark Shuffle: El Talón de Aquiles del Rendimiento

El **Shuffle** es la operación más costosa en sistemas distribuidos porque involucra tres cuellos de botella simultáneos:

```
[ Executor Origen ] ──&gt; 1. Serialización (Kryo/Java) ──&gt; 2. Escritura a Disco Local (Shuffle Write)
                                                                     │
                                                                 Red (TCP)
                                                                     │
[ Executor Destino ] &lt;── 4. Deserialización &lt;── 3. Lectura por Red (Shuffle Read)

```

### ¿Por qué los Shuffles degradan los pipelines?

1. **I/O de Disco**: Las particiones intermedias del Shuffle se escriben temporalmente en el disco rígido local de los workers (*Shuffle Write*).
2. **Saturación de Red**: Gigabytes de datos viajan por la red TCP entre los nodos (*Shuffle Read*).
3. **Pausas de Garbage Collection**: La deserialización de millones de objetos `PyObject` / Java sobrecarga la memoria heap.

### Parámetro Crítico: `spark.sql.shuffle.partitions`

Por defecto, Spark asigna **200 particiones** para cualquier operación que requiera Shuffle.

* **En datasets pequeños (&lt; 1 GB)**: 200 particiones es un exceso (*Overhead* por creación de miles de tareas vacías).
* **En datasets gigantes (&gt; 500 GB)**: 200 particiones genera particiones de más de 2.5 GB cada una, causando errores de *Spill to Disk* u **OOM (Out Of Memory)**.

---

## 🛠️ 3\. Optimización Dinámica con Adaptive Query Execution (AQE)

Introducido en Spark 3.0 (y activado por defecto desde Spark 3.2+ via `spark.sql.adaptive.enabled=true`), **AQE** re-optimiza el plan físico de ejecución en tiempo real utilizando las estadísticas recolectadas *durante* las fases intermadias del Shuffle.

```
[ Plan de Ejecución Inicial ] ──&gt; [ Ejecuta Stage 1 ] ──&gt; [ Re-evalúa Estadísticas Reales de Red/Disco ]
                                                                        │
                                                                        ▼
                                                   [ Ajusta Plan Físico para Stage 2 ]

```

### Las 3 Funcionalidades Clave de AQE:

1. **Coalescing Post-Shuffle Partitions (Fusiones Dinámicas)**:  
  * Combina automáticamente particiones de Shuffle pequeñas contiguas para evitar lanzar cientos de tareas de pocos kilobytes.
2. **Dynamic Join Conversion (Conversión Dinámica a Broadcast Join)**:  
  * Si después de aplicar un filtro (`WHERE fecha = '2026-01-01'`), una tabla gigantesca se reduce a menos de 10 MB, AQE cambia el algoritmo de `SortMergeJoin` a `BroadcastHashJoin` al vuelo, eliminando el Shuffle posterior.
3. **Dynamic Skew Join Optimization (Mitigación de Data Skew)**:  
  * Detecta automáticamente particiones sesgadas (muy grandes comparadas con el promedio) y las divide en sub-particiones más pequeñas, distribuyendo la carga de trabajo entre múltiples executors.

---

## ⚡ 4\. Broadcast Joins &amp; Dynamic Partition Pruning (DPP)

### A. Broadcast Hash Join (BHJ)

Si una de las dos tablas en un `JOIN` es lo suficientemente pequeña (por defecto &lt; 10 MB, configurable con `spark.sql.autoBroadcastJoinThreshold`), Spark copia la tabla completa en la memoria de todos los *Executors*.

```
[ Tabla Gigante (1 TB) ] (Distribuida en N nodos)
                                 │
                                 ├─&gt; JOIN Local en RAM con [ Tabla Pequeña (5 MB) ] (Copiada a todos los nodos)
                                 │
                   ❌ Cero Movimiento de Red para la Tabla Gigante (Cero Shuffle)

```

* **Uso Manual**: `from pyspark.sql.functions import broadcast` \-&gt; `df_large.join(broadcast(df_small), "id")`.

### B. Dynamic Partition Pruning (DPP)

En modelos en estrella (*Kimball*), las tablas de hechos están particionadas por fecha (ej. `año/mes/dia`). Cuando haces un `JOIN` entre la tabla de hechos y una dimensión filtrada (ej. `dim_region WHERE pais = 'CHILE'`), **DPP** identifica dinámicamente las particiones de la tabla de hechos que corresponden a Chile y **evita leer las particiones de los demás países de disco/S3**.

---

## 🏋️‍♂️ Ejercicio Práctico Hands-On: Comparativa de Join con Shuffle vs. Broadcast Join

Crea el archivo `demo_shuffle_vs_broadcast.py` para medir la diferencia de planes físicos:

```
import time
from pyspark.sql import SparkSession
from pyspark.sql.functions import broadcast, col, rand

# 1. Crear sesión de Spark con AQE habilitado
spark = (
    SparkSession.builder.appName("Optimization_Demo")
    .config("spark.sql.adaptive.enabled", "true")
    .config("spark.sql.shuffle.partitions", "8")
    .getOrCreate()
)

# 2. Generar dataset grande (1 millón de filas) y dataset pequeño (100 filas)
print("Generando datasets de prueba...")
df_grande = (
    spark.range(0, 1_000_000)
    .withColumn("categoria_id", (rand() * 10).cast("int"))
    .withColumn("val", rand())
)
df_pequeno = spark.range(0, 10).withColumnRenamed("id", "categoria_id")

# ----------------------------------------------------
# A. JOIN Convencional (Puede requerir Shuffle)
# ----------------------------------------------------
print("\n--- A. Ejecutando Join Normal (Sort-Merge / Shuffle) ---")
inicio = time.perf_counter()
res_normal = df_grande.join(df_pequeno, "categoria_id").groupBy("categoria_id").count()
res_normal.collect()
fin = time.perf_counter()
print(f"Tiempo Join Normal: {fin - inicio:.4f} segundos")

# ----------------------------------------------------
# B. JOIN Optimizado con Broadcast (Zero Shuffle en la tabla grande)
# ----------------------------------------------------
print("\n--- B. Ejecutando Broadcast Hash Join ---")
inicio = time.perf_counter()
res_broadcast = df_grande.join(broadcast(df_pequeno), "categoria_id").groupBy("categoria_id").count()
res_broadcast.collect()
fin = time.perf_counter()
print(f"Tiempo Broadcast Join: {fin - inicio:.4f} segundos")

# 3. Mostrar Plan Físico de Ejecución
print("\n--- Plan Físico del Broadcast Join ---")
res_broadcast.explain()

spark.stop()

```

---

## 🧠 Checkpoint de Autoevaluación

1. ¿Cuál es la diferencia técnica entre una transformación *Narrow* y una transformación *Wide* en Apache Spark?
2. ¿Por qué el *Shuffle* es considerado la operación más costosa en un pipeline distribuido?
3. Explica los tres mecanismos de optimización que realiza **Adaptive Query Execution (AQE)** en tiempo de ejecución.
4. ¿En qué escenario es seguro utilizar la función `broadcast()` en un `JOIN` y cuál es el riesgo de usarla con tablas grandes?