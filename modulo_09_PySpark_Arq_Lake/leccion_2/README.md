# 🚀 Lección 02: PySpark Core: Transformaciones Lazy, Actions, Shuffling y Optimización con Catalyst Optimizer

En la Lección 01 comprendimos la arquitectura distribuida Driver-Executors de Apache Spark y cómo escala horizontalmente dividiendo datos en particiones a lo largo de un clúster.

Sin embargo, para escribir código PySpark de nivel Senior/Ssr que procese Terabytes en minutos sin agotar la memoria, es indispensable entender cómo piensa Spark por dentro: **¿Por qué definir transformaciones no ejecuta nada en el clúster? ¿Qué diferencia a una transformación de una Action? ¿Por qué el Shuffling es el enemigo número uno del rendimiento y cómo el Catalyst Optimizer reescribe nuestro código para hacerlo ultra-eficiente?**

---

## 1. El Paradigma de Evaluación Perezosa (Lazy Evaluation)

En librerías de un solo nodo como Pandas o Polars, cada línea de código se ejecuta de inmediato (*Eager Execution*). Si aplicamos 5 filtros consecutivos en Pandas, la computadora procesa y crea 5 DataFrames intermedios en RAM.

En PySpark, el modelo es **Lazy (Perezoso)**.

Cuando aplicás filtros, creás columnas o seleccionás campos, Spark no lee ni procesa un solo byte de datos. En su lugar, registra la instrucción dentro de un **Grafo Acíclico Dirigido (DAG)** que representa el plan lógico de ejecución.

```text
               EVALUACIÓN PEREZOSA (LAZY EVALUATION) EN SPARK
┌────────────────────────────────────────────────────────────────────────┐
│ 1. df = spark.read.parquet("s3://data-lake/bronze/")   ──► (NO EJECUTA NADA) │
│ 2. df_filtrado = df.filter(df.monto > 100)            ──► (ACUMULA EN DAG)  │
│ 3. df_final = df_filtrado.select("cliente_id", "monto")──► (ACUMULA EN DAG)  │
└────────────────────────────────────────────────────────────────────────┘
                                   │
                     SE LLAMA A UNA ACTION (ej. .count())
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│ EL CATALYST OPTIMIZER LEE TODO EL DAG, OPTIMIZA Y EJECUTA EN EL CLÚSTER│
└────────────────────────────────────────────────────────────────────────┘
```

### ¿Por qué Lazy Evaluation es una ventaja masiva?
Permite a Spark analizar el flujo de trabajo completo antes de tocar los datos. Si aplicaste un `.filter()` al final de tu script de 100 líneas, el optimizador de Spark lo moverá automáticamente al principio para leer únicamente las filas necesarias desde el disco (**Predicate Pushdown**).

---

## 2. Transformaciones vs. Acciones (Actions)

En PySpark, todas las operaciones sobre DataFrames se dividen estrictamente en dos categorías:

```text
                        OPERACIONES EN PYSPARK
                                   │
         ┌─────────────────────────┴─────────────────────────┐
         ▼                                                   ▼
  TRANSFORMACIONES (Lazy)                             ACCIONES (Eager)
  • Retornan un nuevo DataFrame                      • Retornan un resultado al Driver
  • NO ejecutan procesamiento computacional          • O escriben datos en almacenamiento
  • Ejemplos: select(), filter(),                    • ¡DESPACHAN LA EJECUCIÓN DEL DAG!
    withColumn(), groupBy(), join()                  • Ejemplos: show(), count(),
                                                       collect(), write.parquet()
```

> ### ⚠️ El Peligro de `.collect()` en Producción
>
> La acción `.collect()` toma todas las particiones dispersas en los Executors del clúster y las envía a la memoria RAM del Driver Node.  
> **Regla de Oro:** Si el DataFrame procesado pesa 200 GB y tu Driver tiene 8 GB de RAM, `.collect()` provocará un colapso catastrófico por falta de memoria (*Out-Of-Memory / OOM*). Utilizá `.show(10)`, `.take(10)` o guardá el resultado con `.write.parquet()`.

---

## 3. Tipos de Transformaciones: Narrow vs. Wide y el Costo del Shuffling

No todas las transformaciones se comportan igual en la red del clúster. Se clasifican en dos tipos según el movimiento de datos entre nodos:

```text
            NARROW TRANSFORMATION                        WIDE TRANSFORMATION
          (Sin movimiento de red)                      (Requiere SHUFFLING)

    Executor 1          Executor 2                 Executor 1          Executor 2
  ┌────────────┐      ┌────────────┐             ┌────────────┐      ┌────────────┐
  │ Partición 1│      │ Partición 2│             │ Partición 1│      │ Partición 2│
  └─────┬──────┘      └─────┬──────┘             └─────┬──────┘      └─────┬──────┘
        │ filter()          │ filter()                 └───────┐   ┌───────┘
        ▼                   ▼                                  ▼   ▼
  ┌────────────┐      ┌────────────┐                    [ RED DEL CLÚSTER ]
  │ Partición 1│      │ Partición 2│                     (Redistribución)
  └────────────┘      └────────────┘                           │   │
                                                               ▼   ▼
                                                        ┌────────────┐┌────────────┐
                                                        │Partición 1B││Partición 2B│
                                                        └────────────┘└────────────┘
```

### A. Transformaciones Estrechas (Narrow Transformations)
* **Definición:** Cada partición de entrada contribuye a lo sumo a una partición de salida. La operación se resuelve localmente en la memoria del Executor sin comunicarse con otros nodos.
* **Operaciones:** `select()`, `filter()`, `withColumn()`, `drop()`.
* **Impacto:** Ultra rápidas, escalan linealmente.

### B. Transformaciones Anchas (Wide Transformations)
* **Definición:** Múltiples particiones de entrada deben combinarse para calcular el resultado. Requiere reorganizar y mover los datos a través de la red del clúster entre diferentes Executors.
* **Proceso:** Este intercambio masivo de datos por red se denomina **Shuffling**.
* **Operaciones:** `groupBy()`, `join()`, `distinct()`, `repartition()`.
* **Impacto:** El Shuffling es la operación más costosa en procesamiento distribuido. Provoca saturación de red, lectura/escritura en disco y cuellos de botella de I/O.

---

## 4. El Motor de Optimización: Catalyst Optimizer y Tungsten

Cuando invocás una Action, el **Catalyst Optimizer** de Spark toma tu DAG y lo hace pasar por 4 fases secuenciales antes de ejecutar bytecode optimizado mediante el motor **Tungsten**:

```text
                       FASES DEL CATALYST OPTIMIZER
  1. Unresolved Logical Plan ──► Parsea la sintaxis del código.
  2. Resolved Logical Plan   ──► Valida tipos y columnas contra el Catálogo/Metastore.
  3. Optimized Logical Plan  ──► Aplica reescrituras (Predicate Pushdown, Column Pruning).
  4. Physical Plan           ──► Selecciona la mejor estrategia (ej. Broadcast Join vs. Hash Join).
```

### Optimizaciones Clave del Catalyst:
* **Column Pruning (Poda de Columnas):** Si la tabla tiene 100 columnas pero tu consulta solo usa 3, Spark descarta las 97 restantes antes de leer el archivo del disco.
* **Predicate Pushdown (Empuje de Filtros):** Si filtrás por `pais = 'ARG'`, el Catalyst envía ese filtro directamente al lector del archivo Parquet para no levantar filas innecesarias a la memoria RAM.

---

## 🛠️ Código PySpark: Inspeccionando el Plan con `.explain()`

Podemos inspeccionar las optimizaciones que aplicó el Catalyst Optimizer utilizando el método `.explain(True)` sobre cualquier DataFrame:

```python
from pyspark.sql import SparkSession
from pyspark.sql.functions import col

spark = SparkSession.builder.appName("CatalystDemo").master("local[*]").getOrCreate()

# 1. Cargar dataset
df = spark.read.parquet("s3://data-lake/bronze/ventas.parquet")

# 2. Definir transformaciones (Lazy - No ejecuta nada aún)
df_procesado = df \
    .filter(col("monto_usd") > 50.0) \
    .select("cliente_id", "monto_usd", "pais") \
    .groupBy("pais") \
    .sum("monto_usd")

# 3. Inspeccionar el Plan Físico de Ejecución del Catalyst
df_procesado.explain(True)