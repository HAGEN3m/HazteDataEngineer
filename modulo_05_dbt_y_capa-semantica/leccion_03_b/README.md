# ⚡ Lección 03.B (Módulo 05): Formatos de Tabla Modernos y Lakehouse: ACID en Data Lakes con Delta Lake y Apache Iceberg

&gt; **Propósito**: Comprender la arquitectura interna y diferencias operativas de los formatos de tabla abiertos (*Open Table Formats*) como **Delta Lake** y **Apache Iceberg**, que transforman Data Lakes pasivos en **Data Lakehouses** con garantías transaccionales ACID, *Time Travel*, evolución de esquemas y compactación inteligente.

---

## 📌 1\. La Evolución: De archivos sueltos en S3 al Data Lakehouse

En la era tradicional de los Data Lakes (Hive Metastore sobre archivos Parquet/ORC sueltos en S3/HDFS), los Ingenieros de Datos enfrentaban severos problemas de consistencia e infraestructura:

```
❌ DATA LAKE TRADICIONAL (Hive Metastore + Parquet):
- Sin soporte de transacciones ACID: Si un job falla a mitad de camino, quedan archivos corruptos o parciales en S3.
- Operaciones LIST extremadamente costosas en S3/GCS para descubrir particiones.
- Imposible hacer UPDATE o DELETE eficientes (requería reescribir carpetas enteras).
- Lecturas concurrentes fallaban si otro job estaba escribiendo en la misma partición.

✅ DATA LAKEHOUSE (Delta Lake / Apache Iceberg):
- Transacciones ACID reales (Optimistic Concurrency Control).
- Metadatos desacoplados e indexados: Las consultas leen archivos manifest/json directamente sin hacer `s3:ListObjects`.
- Mutaciones eficientes (`UPDATE`, `DELETE`, `MERGE INTO` / Upsert) a nivel de archivo.
- Time Travel, Schema Enforcement y mantenimiento automático.

```

---

## 🔬 2\. Anatomía Interna: Delta Lake vs. Apache Iceberg

Aunque ambos formatos persiguen el mismo objetivo (abstraer carpetas de Parquet para que se comporten como tablas relacionales), sus arquitecturas de metadatos difieren:

### A. Delta Lake (Creado por Databricks)

Delta Lake utiliza un **Transaction Log (*\_delta\_log*)** basado en archivos JSON append-only y checkpoints en Parquet:

```
mi_tabla_delta/
├── _delta_log/
│   ├── 00000000000000000000.json      &lt;-- Modificación 0 (Create)
│   ├── 00000000000000000001.json      &lt;-- Modificación 1 (Append)
│   ├── 00000000000000000010.checkpoint.parquet  &lt;-- Estado consolidado cada 10 commits
├── part-00000-c000.snappy.parquet
└── part-00001-c000.snappy.parquet

```

* **Control de Concurrencia**: *Optimistic Concurrency Control (OCC)*. Asume que las escrituras no colisionarán. Si dos escrituras tocan los mismos archivos, el motor reintenta la transacción automáticamente.
* **Integración**: Nativa y perfecta dentro del ecosistema Apache Spark y Databricks.

---

### B. Apache Iceberg (Creado por Netflix / Apache Foundation)

Apache Iceberg utiliza una **estructura jerárquica en árbol de archivos de metadatos** que aísla por completo la definición de la tabla del sistema de archivos o catálogo subyacente:

```
                                [ Iceberg Catalog ]
                                         │
                                         ▼
                               [ v3.metadata.json ]  (Estado actual de la tabla)
                                         │
                                         ▼
                              [ Manifest List File ] (Lista de manifiestos del snapshot)
                                   ┌─────┴─────┐
                                   ▼           ▼
                         [ Manifest 1 ]    [ Manifest 2 ] (Tracking explícito de cada .parquet)
                                   │           │
                                   ▼           ▼
                            [ Data Files ]  [ Data Files ] (.parquet)

```

* **Independencia de Motor**: Diseñado desde cero para ser neutral frente al motor de cómputo (funciona igual de nativo en Spark, Trino, Flink, DuckDB, Snowflake y StarRocks).
* **Partition Evolution**: Permite cambiar el esquema de particionamiento de una tabla (ej. de diario a horario) sin reescribir los datos antiguos.

---

## 🛠️ 3\. Capacidades Clave del Lakehouse en Producción

### A. Time Travel (Auditoría e Historial de Estado)

Permite consultar el estado exacto que tenía la tabla en un momento específico del tiempo o en un número de versión anterior, ideal para auditar fallos o reproducir modelos de Machine Learning.

```
-- Consultar Delta Lake en una versión específica
SELECT * FROM delta_ventas VERSION AS OF 5;

-- Consultar Apache Iceberg en una estampa de tiempo pasada
SELECT * FROM iceberg_ventas FOR SYSTEM_TIME AS OF '2026-01-15 10:00:00';

```

### B. Mantenimiento y Solución al "Small File Problem"

Las ingestas por streaming o micro-batches generan miles de archivos `.parquet` de pocos kilobytes, degradando el I/O. Los formatos de tabla modernos ofrecen comandos de compactación física:

* **Compactación (`OPTIMIZE` / Bin-Packing)**: Fusiona miles de archivos pequeños en archivos grandes óptimos (ej. de 128 MB a 512 MB).
* **Multidimensional Clustering (Z-Ordering / Liquid Clustering)**: Reorganiza físicamente las filas dentro de los archivos Parquet ordenándolas por múltiples columnas para maximizar el *Data Skipping* durante las consultas.
* **Limpieza de Archivos Huérfanos (`VACUUM` / `EXPIRE SNAPSHOTS`)**: Elimina de S3 los archivos antiguos que ya no son referenciados por ninguna versión activa o dentro del período de retención.

---

## ⚡ 4\. Mutaciones ACID: `MERGE INTO` (Upserts) en Data Lakes

Antes del Lakehouse, aplicar cambios (updates o deletes) requería leer toda la tabla y reescribirla. Con Delta Lake e Iceberg, ejecutamos sentencias **`MERGE INTO`** atómicas de alto rendimiento:

```
MERGE INTO delta_gold_clientes AS target
USING staging_silver_clientes AS source
ON target.cliente_id = source.cliente_id
WHEN MATCHED AND source.fecha_actualizacion &gt; target.fecha_actualizacion THEN
  UPDATE SET
    target.email = source.email,
    target.estado = source.estado,
    target.fecha_actualizacion = source.fecha_actualizacion
WHEN NOT MATCHED THEN
  INSERT (cliente_id, nombre, email, estado, fecha_actualizacion)
  VALUES (source.cliente_id, source.nombre, source.email, source.estado, source.fecha_actualizacion);

```

---

## 🏋️‍♂️ Ejercicio Práctico Hands-On: Operaciones ACID y Time Travel con Delta Lake

Crea el archivo `demo_delta_lakehouse.py` para ejercitar la creación, actualización incremental y lectura de versiones históricas en PySpark:

```
from pyspark.sql import SparkSession
from pyspark.sql.functions import col

# 1. Crear sesión de PySpark configurada con paquetes de Delta Lake
spark = (
    SparkSession.builder.appName("DeltaLakehouseDemo")
    .config("spark.jars.packages", "io.delta:delta-spark_2.12:3.1.0")
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
    .config(
        "spark.sql.catalog.spark_catalog",
        "org.apache.spark.sql.delta.catalog.DeltaCatalog",
    )
    .getOrCreate()
)

delta_path = "/tmp/delta_lakehouse_ventas"

# 2. Ingesta Inicial (Versión 0)
df_v0 = spark.createDataFrame(
    [
        (1, "Cliente A", 100.0, "ACTIVO"),
        (2, "Cliente B", 250.0, "ACTIVO"),
    ],
    ["id", "cliente", "monto", "estado"],
)

df_v0.write.format("delta").mode("overwrite").save(delta_path)
print("✅ Tabla Delta creada en Versión 0")

# 3. Segunda Ingesta - Apéndice de Datos (Versión 1)
df_v1 = spark.createDataFrame(
    [
        (3, "Cliente C", 500.0, "ACTIVO"),
    ],
    ["id", "cliente", "monto", "estado"],
)

df_v1.write.format("delta").mode("append").save(delta_path)
print("✅ Datos añadidos. Versión 1 generada.")

# 4. Demostración de Time Travel (Consultar la Versión 0 original)
print("\n📜 Leyendo la Versión 0 original (Time Travel):")
df_historico_v0 = (
    spark.read.format("delta").option("versionAsOf", 0).load(delta_path)
)
df_historico_v0.show()

# 5. Consulta del Estado Actual (Versión 1)
print("\n📊 Leyendo el estado actual de la Tabla (Versión 1):")
df_actual = spark.read.format("delta").load(delta_path)
df_actual.show()

spark.stop()

```

---

## 🧠 Checkpoint de Autoevaluación

1. ¿Por qué el almacenamiento tradicional de archivos Parquet sueltos en S3 no ofrecía garantías de transacciones ACID y cómo lo resuelve el *Transaction Log* (`_delta_log`) en Delta Lake?
2. Explica la diferencia entre *Schema Enforcement* y *Schema Evolution* en un Data Lakehouse.
3. ¿Cómo ayuda el comando `OPTIMIZE` (compactación) a solucionar el problema del *Small File Problem* en sistemas de almacenamiento como S3?
4. ¿Qué ventaja ofrece el desacoplamiento de metadatos en **Apache Iceberg** cuando trabajamos en entornos multi-motor (Spark + Trino + DuckDB)?