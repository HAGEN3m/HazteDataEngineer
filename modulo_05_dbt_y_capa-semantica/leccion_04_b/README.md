# ⚡ Lección 04.B (Módulo 05): PySpark en Producción: Vectorized UDFs, Prevención de OOM y Caching

&gt; **Propósito**: Dominar el escalado y optimización de pipelines de PySpark en entornos productivos, comprendiendo el overhead de la JVM inter-process (Python &lt;-&gt; Java), el uso de **Pandas UDFs (PyArrow)**, las estrategias de gestión de memoria para prevenir el **OOM Killer (Exit Code 137)**, el uso correcto de `cache()` vs `persist()` y las mejores prácticas anti-patrones.

---

## 📌 1\. El Dilema del Intérprete: Python UDF vs. JVM Engine

Apache Spark está escrito en Scala/Java y se ejecuta dentro de la **JVM**. Cuando usas PySpark, el código de la API estándar de DataFrames (`pyspark.sql.functions`) no corre en Python: se traduce directamente a un plan de ejecución de Java/Scala administrado por **Catalyst** y **Project Tungsten**.

Sin embargo, cuando escribes una **UDF de Python nativa** (`@udf`), se destruye la optimización:

```
[ JVM Executor (Java) ] ──(Serializar / Py4J Socket)──&gt; [ Python Worker Process ]
                                                                 │ (Ejecuta fila x fila)
[ JVM Executor (Java) ] &lt;──(Deserializar / Socket)─────── [ Devuelve Resultado ]

```

### Problemas de las Python UDFs Tradicionales:

1. **Serialización Fila por Fila**: PySpark debe mover cada fila de la memoria JVM a un proceso Python externo mediante IPC (Inter-Process Communication).
2. **Cero Optimización de Catalyst**: Catalyst trata a la UDF como una caja negra; no puede aplicar *Predicate Pushdown* ni compilación *Whole-Stage Codegen*.
3. **Alto Uso de CPU y RAM**: La constante conversión de tipos JVM &lt;-&gt; Python satura la CPU.

---

## 🔬 2\. UDFs Vectorizadas con Apache Arrow (Pandas UDFs)

Para resolver este problema sin reescribir el código en Scala/Java, Spark integra **Apache Arrow** para transferir bloques de datos continuos en memoria columnar entre la JVM y Python sin costo de serialización.

```
[ JVM Memory (Arrow Columnar) ] ──Zero-Copy / Memory Mapping──&gt; [ Python Pandas/PyArrow ]
                                                                       │ (Ejecuta en Bloque SIMD)
[ JVM Memory (Arrow Columnar) ] &lt;──Zero-Copy / Memory Mapping──────────┘

```

### Tipos de Pandas UDFs (`pyspark.sql.functions.pandas_udf`):

1. **Series to Series**: Recibe una o más `pandas.Series` y retorna una `pandas.Series` de igual longitud.
2. **Iterator of Series to Iterator of Series**: Ideal para inicializaciones costosas (ej. cargar un modelo ML una sola vez por partición).
3. **Grouped Map (`applyInPandas`)**: Permite aplicar transformaciones arbitrarias de Pandas sobre cada grupo de un `groupBy()`.

### Comparación de Rendimiento:

| Método                                           | Mecanismo                | Velocidad Relativa                |
| ------------------------------------------------ | ------------------------ | --------------------------------- |
| **Funciones Nativas PySpark** (`pl.col`, `when`) | Ejecución directa en JVM | ⚡⚡⚡ (1x - Referencia)             |
| **Pandas UDF (`@pandas_udf`)**                   | Vectorizado vía PyArrow  | ⚡⚡ (2x - 5x más lento que nativo) |
| **Python UDF Tradicional (`@udf`)**              | Fila x fila con IPC      | 🐢 (20x - 100x más lento)         |

---

## 🛠️ 3\. Prevención de OOM (Out of Memory) Killer en Executors

El error `Exit Code 137` o `java.lang.OutOfMemoryError: Java heap space` ocurre por tres causas principales:

### A. Data Skew (Sesgo de Datos)

Una o dos particiones contienen el 80% de los datos. El executor asignado a esa partición agota su memoria RAM durante un `groupBy` o `join`.

* **Solución**: Activar AQE (`spark.sql.adaptive.skewJoin.enabled=true`) o aplicar *Salting*.

### B. Uso de `.collect()` o `.toPandas()` en Datasets Masivos

Traer todo el contenido de un DataFrame distribuido al *Driver Node* colapsa la RAM del Driver.

* **Solución**: Usar `.take(N)`, `.limit(N)` o escribir la salida en disco/Data Lake.

### C. Ajuste Fino de Memoria del Executor

Si tus Pandas UDFs o librerías de C (NumPy/PyArrow) consumen memoria fuera del Heap de Java (*Off-Heap Memory*), debes incrementar la memoria de overhead del executor:

```
spark.executor.memoryOverhead = max(384MB, 0.10 * executorMemory)

```

---

## ⚡ 4\. Caching y Persistence (`cache()` vs. `persist()`)

Cuando un DataFrame se utiliza múltiples veces en distintas acciones (ej. entrenamiento de modelo + reporte analítico), recalcular su linaje (*DAG*) desde cero en cada acción es ineficiente.

```
# cache() es un alias de persist(StorageLevel.MEMORY_AND_DISK)
df.cache()

# persist() permite elegir el nivel de almacenamiento exacto
from pyspark import StorageLevel

# Guardar en RAM des-serializado (Rápido, usa más memoria)
df.persist(StorageLevel.MEMORY_ONLY)

# Guardar en RAM serializado (Ahorra memoria, usa un poco más de CPU)
df.persist(StorageLevel.MEMORY_ONLY_SER)

# Guardar en RAM y desbordar a disco local si no cabe (Recomendado para Datasets Grandes)
df.persist(StorageLevel.MEMORY_AND_DISK)

# ¡IMPORTANTE! Liberar memoria cuando finalice el cálculo
df.unpersist()

```

&gt; ⚠️ **REGLA DE ORO**: Nunca dejes DataFrames cacheados sin hacer `.unpersist()`. Acumular datasets en memoria degrada el *Storage Memory* y provoca *Garbage Collection Pauses* largas.

---

## 🏋️‍♂️ Ejercicio Práctico Hands-On: Benchmark de UDFs Vectorizadas vs. Tradicionales

Crea el archivo `udf_benchmark.py` para medir la diferencia de rendimiento entre una Python UDF y una Pandas UDF sobre un dataset masivo:

```
import time
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, udf, pandas_udf
import pandas as pd

# Inicializar sesión de Spark
spark = SparkSession.builder \
    .appName("UDF_Benchmark") \
    .config("spark.sql.execution.arrow.pyspark.enabled", "true") \
    .getOrCreate()

# 1. Crear dataset sintético de 5 millones de filas
df = spark.range(1, 5_000_001).withColumn("monto", col("id") * 1.5)

# 2. Definir UDF Tradicional (Fila a Fila)
@udf("double")
def calcular_impuesto_tradicional(val):
    return val * 0.21 if val is not None else 0.0

# 3. Definir Pandas UDF Vectorizada (Apache Arrow)
@pandas_udf("double")
def calcular_impuesto_vectorizado(val: pd.Series) -&gt; pd.Series:
    return val * 0.21

# ----------------------------------------------------
# A. Benchmark Python UDF Tradicional
# ----------------------------------------------------
inicio = time.time()
res_trad = df.withColumn("impuesto", calcular_impuesto_tradicional(col("monto"))).count()
fin = time.time()
print(f"🐢 UDF Tradicional (Fila x Fila): {fin - inicio:.2f} segundos")

# ----------------------------------------------------
# B. Benchmark Pandas UDF (Vectorizada Arrow)
# ----------------------------------------------------
inicio = time.time()
res_vec = df.withColumn("impuesto", calcular_impuesto_vectorizado(col("monto"))).count()
fin = time.time()
print(f"⚡ Pandas UDF (Vectorizada Arrow): {fin - inicio:.2f} segundos")

# ----------------------------------------------------
# C. Benchmark Función Nativa de Spark
# ----------------------------------------------------
inicio = time.time()
res_nat = df.withColumn("impuesto", col("monto") * 0.21).count()
fin = time.time()
print(f"🚀 Función Nativa Spark (Tungsten): {fin - inicio:.2f} segundos")

spark.stop()

```

---

## 🧠 Checkpoint de Autoevaluación

1. ¿Por qué una UDF tradicional de Python es significativamente más lenta que las funciones nativas de PySpark?
2. ¿Cómo logra Apache Arrow acelerar el procesamiento de las Pandas UDFs (`@pandas_udf`)?
3. ¿Cuál es el código de salida (*Exit Code*) del Linux OOM Killer cuando un Executor agota la memoria RAM del sistema y cómo se previene?
4. ¿Cuál es la diferencia entre `StorageLevel.MEMORY_ONLY` y `StorageLevel.MEMORY_AND_DISK` al usar `.persist()`, y por qué es obligatorio ejecutar `.unpersist()` al terminar?