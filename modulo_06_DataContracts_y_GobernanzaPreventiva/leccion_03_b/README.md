# ⚡ Lección 03.B (Módulo 06): Stream Processing en Tiempo Real &amp; Change Data Capture (CDC) con Debezium y Spark/Flink

&gt; **Propósito**: Dominar las arquitecturas de procesamiento de eventos en tiempo real (*Stream Processing*) y la captura de cambios en bases de datos relacionales (*Change Data Capture - CDC*), comprendiendo el funcionamiento de Debezium sobre el WAL/Binlog, la diferencia entre procesadores micro-batch (Spark Structured Streaming) y evento por evento (Apache Flink), y la gestión de ventanas temporales con *Watermarking*.

---

## 📌 1\. Change Data Capture (CDC) vs. Polling Tradicional

En sistemas batch tradicionales, la ingesta incremental de bases de datos relacionales (PostgreSQL, MySQL, Oracle) suele realizarse ejecutando consultas recurrentes como:

```
-- ANTI-PATRÓN DE INGESTA INCREMENTAL (POLLING)
SELECT * FROM ordenes WHERE fecha_actualizacion &gt; '2026-09-24 00:00:00';

```

### Problemas Críticos del Polling Tradicional:

1. **Sobrecarga en la Base de Datos OLTP**: Ejecutar consultas de escaneo frecuentes degrada el rendimiento de la base de datos de producción.
2. **Incapacidad para Capturar Registros Eliminados (`DELETE`)**: Si una fila se borra físicamente (`DELETE FROM ordenes WHERE id = 10`), el polling nunca sabrá que ese registro dejó de existir.
3. **Pérdida de Estados Intermedios**: Si un registro cambia de estado tres veces entre cada corrida del job (`PENDIENTE` \-&gt; `PAGADO` \-&gt; `ENVIADO`), el polling solo capturará el último estado (`ENVIADO`), perdiendo la trazabilidad de los cambios intermedios.

### La Solución CDC (Change Data Capture)

El enfoque **CDC** no ejecuta consultas SQL sobre la base de datos. En su lugar, lee directamente el registro de transacciones a bajo nivel del motor de base de datos (**Write-Ahead Log / WAL** en PostgreSQL, **Binlog** en MySQL).

```
[ Base de Datos OLTP (PostgreSQL) ]
          │
          ▼ (Escribe transacciones físicas)
    [ WAL / Binlog ]
          │
          ▼ (Lee eventos de cambio sin impacto en CPU/RAM)
 [ Debezium / Kafka Connect ]
          │
          ▼ (Publica eventos de mutación JSON/Avro)
   [ Kafka Topic: db.public.ordenes ]

```

---

## 🔬 2\. Arquitectura de Debezium &amp; Kafka Connect

**Debezium** es un conector de código abierto construido sobre el framework **Kafka Connect** que convierte las modificaciones registradas en el log de la base de datos en streams de eventos estandarizados.

### Anatomía de un Evento CDC de Debezium (JSON)

Cuando se ejecuta un `UPDATE` en la tabla de ordenes, Debezium emite un mensaje en Kafka con la siguiente estructura:

```
{
  "schema": { ... },
  "payload": {
    "before": {
      "orden_id": 105,
      "monto": 150.00,
      "estado": "PENDIENTE"
    },
    "after": {
      "orden_id": 105,
      "monto": 150.00,
      "estado": "PAGADO"
    },
    "source": {
      "version": "2.5.0.Final",
      "connector": "postgresql",
      "name": "production_db",
      "ts_ms": 1774332000000,
      "table": "ordenes"
    },
    "op": "u",  // 'c' = Create/Insert, 'u' = Update, 'd' = Delete, 'r' = Read (Snapshot inicial)
    "ts_ms": 1774332001000
  }
}

```

---

## 🛠️ 3\. Motores de Stream Processing: Spark Structured Streaming vs. Apache Flink

Una vez que los eventos de cambio residen en topics de Kafka, requerimos motores de procesamiento continuo para realizar agregaciones, filtrados y transformaciones en tiempo real.

```
┌───────────────────────────────────┬───────────────────────────────────┐
│ Spark Structured Streaming        │ Apache Flink                      │
├───────────────────────────────────┼───────────────────────────────────┤
│ Modelo: Micro-batch (por defecto) │ Modelo: Native Event-Driven       │
│ Latencia: 100ms - 1 segundo       │ Latencia: Sub-segundo (&lt; 10ms)    │
│ Estado: InMemory / RocksDB        │ Estado: RocksDB State Backend     │
│ Ideal para: ETL continuo,         │ Ideal para: Complejidad temporal, │
│ unificación con Batch/Lakehouse.  │ detección de fraude, CEP.         │
└───────────────────────────────────┴───────────────────────────────────┘

```

---

## ⚡ 4\. Ventanas Temporales &amp; Manejo de Datos Tardíos (Late Data)

En sistemas distribuidos en tiempo real, existen dos conceptos de tiempo esenciales:

* **Event Time (Tiempo del Evento)**: Marca de tiempo ocurrida cuando se generó el evento en el sistema origen (`payload.source.ts_ms`).
* **Processing Time (Tiempo de Procesamiento)**: Marca de tiempo del servidor cuando el motor de procesamiento recibe y procesa el registro.

Debido a latencias de red o caídas de conexión, los eventos pueden llegar fuera de orden (*Late Data*). Para agrupar eventos en tiempo real sin perder consistencia, utilizamos **Ventanas Temporales** y **Watermarking**.

```
A. Tumbling Window (Sin superposición, intervalos fijos de 5 min)
|   00:00 - 00:05   |   00:05 - 00:10   |   00:10 - 00:15   |

B. Sliding Window (Con superposición, ventana de 10 min, desliza cada 2 min)
|====== 00:00 - 00:10 ======|
        |====== 00:02 - 00:12 ======|

```

### ¿Qué es el Watermarking?

El **Watermarking** es un umbral de tolerancia a la tardanza. Define cuánto tiempo esperará el motor a un evento demorado antes de cerrar la ventana y emitir los resultados finales.

```
# Ejemplo de Watermark de 10 minutos
df.withWatermark("event_time", "10 minutes") \
  .groupBy(window("event_time", "5 minutes"), "categoria") \
  .count()

```

*Si llega un evento con `event_time = 10:00`, pero el watermark del sistema ya avanzó a `10:15` (debido a eventos más recientes procesados), el evento tardío se descarta de forma segura para evitar modificar datos históricos.*

---

## 🏋️‍♂️ Ejercicio Práctico Hands-On: Stream Processing con PySpark Structured Streaming

Crea el archivo `streaming_cdc_processor.py` para consumir eventos CDC de Kafka, procesarlos con ventanas temporales y aplicar Watermarking:

```
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, expr, window
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, LongType

# 1. Inicializar sesión de PySpark con paquete de Kafka
spark = SparkSession.builder \
    .appName("CDC_Stream_Processing") \
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

# 2. Definir esquema del payload de Debezium
cdc_payload_schema = StructType([
    StructField("before", StructType([
        StructField("orden_id", LongType()),
        StructField("monto", DoubleType()),
        StructField("estado", StringType())
    ])),
    StructField("after", StructType([
        StructField("orden_id", LongType()),
        StructField("monto", DoubleType()),
        StructField("estado", StringType())
    ])),
    StructField("op", StringType()),
    StructField("ts_ms", LongType())
])

# 3. Leer Stream continuo desde Kafka
raw_kafka_stream = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:9092") \
    .option("subscribe", "db.public.ordenes") \
    .option("startingOffsets", "latest") \
    .load()

# 4. Deserializar el JSON y extraer campos con Event Time
parsed_stream = raw_kafka_stream \
    .select(from_json(col("value").cast("string"), cdc_payload_schema).alias("data")) \
    .select(
        col("data.after.orden_id").alias("orden_id"),
        col("data.after.monto").alias("monto"),
        col("data.after.estado").alias("estado"),
        col("data.op").alias("operacion"),
        (col("data.ts_ms") / 1000).cast("timestamp").alias("event_time")
    ) \
    .filter(col("operacion") != "d") # Filtrar eliminaciones

# 5. Agregación en ventana deslizante de 10 minutos con Watermark de 5 minutos
windowed_aggregations = parsed_stream \
    .withWatermark("event_time", "5 minutes") \
    .groupBy(
        window(col("event_time"), "10 minutes", "2 minutes"),
        col("estado")
    ) \
    .sum("monto")

# 6. Escribir resultados continuos en la consola (Modo Append/Update)
query = windowed_aggregations.writeStream \
    .outputMode("update") \
    .format("console") \
    .option("truncate", "false") \
    .start()

# query.awaitTermination()

```

---

## 🧠 Checkpoint de Autoevaluación

1. ¿Por qué la lectura directa del Write-Ahead Log (WAL / Binlog) mediante CDC es superior al polling de tablas relacionales con `WHERE updated_at &gt; last_sync`?
2. ¿Qué significan los valores `'c'`, `'u'` y `'d'` en el campo `op` de un evento generado por Debezium?
3. Explica la diferencia entre **Event Time** y **Processing Time** y por qué los cálculos en tiempo real deben basarse en el Event Time.
4. ¿Cómo ayuda el **Watermarking** a prevenir el agotamiento de memoria RAM en un clúster de Stream Processing cuando se procesan eventos fuera de orden (*Late Data*)?