# 🚀 Lección 04: Optimización de Jobs en PySpark: Partitioning, Bucketing, Broadcast Joins y Manejo de Data Skew

En la Lección 03 comprendimos la revolución del Data Lakehouse y los Formatos de Tabla Abiertos (Delta Lake / Apache Iceberg), permitiendo transacciones ACID, operaciones `MERGE INTO` (Upserts) y consulta histórica mediante Time Travel.

Sin embargo, cuando procesamos Terabytes o Petabytes de datos en producción, incluso la mejor arquitectura colapsará si cometemos errores clásicos de distribución física: jobs que tardan horas en finalizar, tareas colgadas al 99% por sesgo de datos (**Data Skew**) o cuellos de botella por intercambio masivo de datos por red (**Shuffling**).

En esta lección aprenderemos las técnicas avanzadas de optimización y tuning que diferencian a un Data Engineer Junior de un Data Engineer Ssr/Senior:
* Gestión de particiones con `repartition()` vs. `coalesce()`.
* Eliminación de Shuffles mediante Bucketing.
* Optimización de uniones con Broadcast Joins.
* Resolución del temido problema de Data Skew (Sesgo de Datos) mediante la técnica de Salting.

---

## 1. Gestión de Particiones: `repartition()` vs. `coalesce()`

Un DataFrame de PySpark se divide físicamente en particiones. Cada partición se procesa en un hilo de ejecución dentro de un Executor.

```text
                  PARTICIONADO DE UN DATAFRAME EN MEMORIA
  ┌────────────────────────────────────────────────────────────────────────┐
  │ DATAFRAME (10,000,000 de filas)                                        │
  ├───────────────┬───────────────┬───────────────┬────────────────────────┤
  │ Partición 1   │ Partición 2   │ Partición 3   │ Partición 4            │
  │ (2.5M filas)  │ (2.5M filas)  │ (2.5M filas)  │ (2.5M filas)           │
  └───────────────┴───────────────┴───────────────┴────────────────────────┘
```

### ¿Cuál es el tamaño ideal de una partición?
* **Regla de Oro:** Cada partición en memoria debe pesar entre **128 MB y 1 GB**.
* **Problema de Particiones Gigantes:** Provoca errores de falta de memoria (*Out-Of-Memory / OOM*).
* **Problema de Particiones Diminutas (*Small File Problem*):** Crear miles de particiones de 1 KB genera un enorme overhead de gestión en el Driver Node.

### La Diferencia Crucial: `repartition()` vs. `coalesce()`

```text
  `repartition(N)` (Aumenta o reduce particiones)
  • Realiza un FULL SHUFFLE a través de la red.
  • Redistribuye los datos de forma equitativa.
  • Usar cuando queramos AUMENTAR el número de particiones.

  `coalesce(N)` (Solo REDUCE particiones)
  • NO realiza un Full Shuffle por red.
  • Combina particiones adyacentes en el mismo nodo.
  • Usar cuando queramos REDUCIR particiones antes de guardar en disco (`.write`).
```

```python
# ❌ INCORRECTO: Genera Shuffling innecesario para reducir particiones
df_reducido = df.repartition(2)

# 🟢 CORRECTO: Reduce de 100 a 2 particiones en memoria sin Shuffling de red
df_reducido = df.coalesce(2)
```

---

## 2. Broadcast Joins: Optimización de Joins (Grandes vs. Pequeñas)

Cuando unimos dos tablas masivas en Spark (`df_ventas.join(df_clientes)`), el motor realiza un Sort-Merge Join, lo que exige mover filas de ambas tablas por la red para reunir las mismas claves en el mismo nodo (Full Shuffle).

Sin embargo, en esquemas analíticos es habitual unir una tabla de hechos masiva (ej. 500 millones de ventas) contra una tabla de dimensión pequeña (ej. 50 países o 1,000 categorías de productos).

### El Patrón Broadcast Join (`broadcast()`)
En lugar de mover la tabla gigante por la red, Spark hace una copia ligera de la tabla pequeña y la envía por difusión (*Broadcast*) a la memoria RAM de todos los Executor Nodes.

```text
                           BROADCAST MAP-JOIN
  [ TABLA PEQUEÑA ] ──► Se envía una copia a la RAM de cada Executor
  (ej. 5 MB)

      Executor 1                          Executor 2
  ┌────────────────────────┐          ┌────────────────────────┐
  │ Partición 1 Ventas     │          │ Partición 2 Ventas     │
  │ + [Copia Tabla Pequeña]│          │ + [Copia Tabla Pequeña]│
  └────────────────────────┘          └────────────────────────┘
  ★ EL JOIN SE RESUELVE 100% EN MEMORIA LOCAL (CERO SHUFFLING DE RED)
```

```python
from pyspark.sql.functions import broadcast

# Forzar a Spark a realizar un Broadcast Join
df_resultado = df_fact_ventas.join(
    broadcast(df_dim_paises),  # Envía la dimensión a todos los nodos
    on="pais_id",
    how="inner"
)
```

> ### 💡 Umbral por Defecto
> Por defecto, Spark aplica automáticamente Broadcast Join si la tabla pequeña pesa menos de 10 MB (`spark.sql.autoBroadcastJoinThreshold`).

---

## 3. Bucketing: Pre-Agrupamiento para Eliminar Shuffles Futuros

Si dos tablas masivas deben unirse con frecuencia sobre la misma columna (ej. `cliente_id`), hacer Shuffling en cada pipeline es un desperdicio de recursos.

**Bucketing** divide y guarda físicamente los datos en el disco en un número fijo de "baldes" (*Buckets*) aplicando una función de Hash sobre la columna clave:

```sql
-- Guardar tabla con Bucketing en 16 baldes por 'cliente_id'
CREATE TABLE gold.fact_ventas
USING parquet
CLUSTERED BY (cliente_id) INTO 16 BUCKETS;
```

Cuando unimos dos tablas que están pre-agrupadas por el mismo número de Buckets y la misma clave, Spark elimina completamente la fase de Shuffle, leyendo directamente los bloques alineados.

---

## 4. El Problema de Data Skew (Sesgo de Datos) y la Técnica de Salting

### ¿Qué es el Data Skew?
Ocurre cuando la distribución de los datos sobre la clave de particionado es extremadamente desproporcionada.

Un ejemplo típico en e-commerce: el 90% de las ventas pertenecen al cliente "Consumidor Final" (`cliente_id = 'GUEST'`), mientras que el 10% restante se reparte entre miles de clientes individuales.

```text
                  EFECTO DE DATA SKEW EN EL CLÚSTER
  Executor 1: Recibe cliente 'GUEST' ──► 9,000,000 filas (Tarda 2 horas) ──► 💥 Satura RAM
  Executor 2: Recibe cliente 'C-101' ──►     5,000 filas (Tarda 1 segundo)
  Executor 3: Recibe cliente 'C-102' ──►     3,000 filas (Tarda 1 segundo)

  ★ RESULTADO: El job completo queda "clavado" al 99% esperando que termine el Executor 1.
```

### La Solución Senior: Salting (Añadir Sal Aleatoria)
El **Salting** destruye la concentración de la clave sesgada agregando un número aleatorio ("sal") a la clave de uniones o agregaciones, dividiendo la clave gigante en sub-claves balanceadas.

```text
                           TÉCNICA DE SALTING
  [ Clave Sesgada: 'GUEST' ] ──► Salting (1 a 4) ──► 'GUEST_1' (2.25M filas)
                                                  ──► 'GUEST_2' (2.25M filas)
                                                  ──► 'GUEST_3' (2.25M filas)
                                                  ──► 'GUEST_4' (2.25M filas)
  ★ RESULTADO: Las 4 sub-claves se procesan en paralelo en 4 Executors sin saturación.
```

```python
from pyspark.sql.functions import concat, lit, rand, floor, col

# 1. Agregar "Sal" (número aleatorio entre 0 y 3) a la tabla sesgada
df_ventas_salted = df_ventas.withColumn(
    "salt", floor(rand() * 4)
).withColumn(
    "cliente_id_salted", concat(col("cliente_id"), lit("_"), col("salt"))
)

# 2. Replicar la sal en la tabla de dimensión para que haga match
# Ahora el join se distribuye de forma uniforme entre 4 sub-particiones
```

---

## 5. Código PySpark Completo: Demostración de Optimizaciones

```python
from pyspark.sql import SparkSession
from pyspark.sql.functions import broadcast, col, concat, lit, rand, floor

spark = SparkSession.builder \
    .appName("Optimizacion_PySpark_Leccion04") \
    .master("local[*]") \
    .getOrCreate()

# 1. Dataset Masivo de Ventas (Simulado)
df_ventas = spark.createDataFrame([
    (1, "GUEST", 100.0), (2, "GUEST", 200.0), (3, "GUEST", 150.0),
    (4, "CLI_101", 500.0), (5, "CLI_102", 300.0)
], ["venta_id", "cliente_id", "monto"])

# 2. Dataset Pequeño de Países (Dimensión para Broadcast)
df_paises = spark.createDataFrame([
    ("GUEST", "Global"), ("CLI_101", "Argentina"), ("CLI_102", "Chile")
], ["cliente_id", "pais_nombre"])

# --- OPTIMIZACIÓN 1: BROADCAST JOIN ---
print("--- 1. BROADCAST JOIN (Sin Shuffle de Red) ---")
df_broadcast = df_ventas.join(
    broadcast(df_paises),
    on="cliente_id",
    how="inner"
)
df_broadcast.show()

# --- OPTIMIZACIÓN 2: SALTING PARA DATA SKEW ---
print("--- 2. TÉCNICA DE SALTING PARA TRATAR DATA SKEW ---")
df_ventas_salted = df_ventas.withColumn("salt", floor(rand() * 2)) \
    .withColumn("salted_key", concat(col("cliente_id"), lit("_"), col("salt")))

df_ventas_salted.select("venta_id", "cliente_id", "salted_key").show()

# --- OPTIMIZACIÓN 3: COALESCE PARA REDUCIR ARCHIVOS ---
print("--- 3. REDUCCIÓN LIMPIA DE PARTICIONES CON COALESCE ---")
print(f"Particiones originales: {df_ventas.rdd.getNumPartitions()}")
df_coalesced = df_ventas.coalesce(1)
print(f"Particiones luego de coalesce(1): {df_coalesced.rdd.getNumPartitions()}")
```

---

## 🏋️‍♂️ Práctica de la Lección 04

1. Ubicate en la carpeta `practica/modulo_09/` de tu repositorio local.
2. Creá el archivo `ej_04_pyspark_optimization.py`.
3. Escribí un script Python que simule el impacto de Broadcast Join, Coalesce y la técnica de Salting:

```python
import pandas as pd
import random

# Simulador de Optimización de Jobs en PySpark
class SparkJobOptimizerSimulator:
    def __init__(self, fact_rows: int = 10000):
        self.fact_rows = fact_rows

    def simulate_broadcast_join(self, dim_size: int):
        print(f"🚀 [OPTIMIZER] Evaluando Join entre Fact ({self.fact_rows} filas) y Dim ({dim_size} filas)...")
        if dim_size <= 1000:
            print("  ✅ ESTRATEGIA SELECCIONADA: Broadcast Hash Join.")
            print("     La tabla dimensión se copia a todos los Executors. Shuffling = 0 MB.")
        else:
            print("  ⚠️ ESTRATEGIA SELECCIONADA: Sort-Merge Join.")
            print("     Requiere Full Network Shuffle entre todos los nodos.")

    def simulate_salting(self, skewed_key: str, skew_percentage: float):
        print(f"\n📊 [DATA SKEW DETECTOR] Clave '{skewed_key}' representa el {skew_percentage*100}% de los datos.")
        print("  ⚠️ RIESGO: El Executor asignado a esta clave colapsará por Out-Of-Memory (OOM).")

        print("  🧂 APLICANDO TÉCNICA DE SALTING (N=4 buckets)...")
        for i in range(4):
            sub_key_count = int((self.fact_rows * skew_percentage) / 4)
            print(f"     • Sub-clave '{skewed_key}_{i}': {sub_key_count} filas (Balanceado).")
        print("  ✅ Data Skew resuelto con éxito.")

# Ejecución de Pruebas
optimizer = SparkJobOptimizerSimulator(fact_rows=100000)

# Prueba 1: Broadcast Join
optimizer.simulate_broadcast_join(dim_size=50)

# Prueba 2: Salting para Data Skew
optimizer.simulate_salting(skewed_key="CONSUMIDOR_FINAL", skew_percentage=0.85)
```

4. Agregá comentarios al final del archivo respondiendo:
   * **Consigna A:** Explica por qué utilizar `coalesce()` es preferible a `repartition()` cuando deseamos reducir el número de particiones antes de guardar un dataset en almacenamiento en la nube (AWS S3 / Azure ADLS).
   * **Consigna B:** ¿En qué consiste el fenómeno de Data Skew (Sesgo de Datos) en un clúster distribuido y cómo la técnica de Salting evita que una tarea quede colgada al 99% de su ejecución?