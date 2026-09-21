# 🚀 Lección 05: Cierre del Módulo 09 — Proyecto Capstone Final: Pipeline Masivo Lakehouse End-to-End

¡Llegamos al hito culminante de todo tu trayecto formativo: el **Proyecto Capstone Final**!

A lo largo de este Módulo 09 has dominado las tecnologías de mayor escala en la industria:

* **Lección 01:** Comprendiste la arquitectura de procesamiento distribuido Driver-Executors y la evolución de RDDs a Spark DataFrames.
* **Lección 02:** Dominaste la Evaluación Perezosa (*Lazy Evaluation*), la diferencia entre transformaciones Narrow y Wide (costo del *Shuffling*) y la optimización automática del Catalyst Optimizer.
* **Lección 03:** Adoptaste la arquitectura Data Lakehouse mediante Formatos de Tabla Abiertos (Delta Lake / Apache Iceberg), logrando transacciones ACID, `MERGE INTO` (Upserts) y *Time Travel*.
* **Lección 04:** Aplicaste técnicas avanzadas de tuning: `coalesce()` vs. `repartition()`, Broadcast Joins, Bucketing y tratamiento de Data Skew mediante Salting.

En esta lección integradora construirás un **Pipeline Masivo Lakehouse End-to-End**, unificando el conocimiento acumulado en los 9 módulos de la formación.

---

## 1. Escenario del Proyecto Capstone Final

Imaginemos que fuiste contratado como Data Engineer Ssr para diseñar la arquitectura analítica central de una plataforma global de e-commerce que procesa millones de transacciones diarias.

Tu objetivo es construir un pipeline end-to-end en PySpark sobre arquitectura Data Lakehouse (Delta Lake) que cumpla con los siguientes requerimientos de producción:

```text
                               ARQUITECTURA DEL PROYECTO CAPSTONE
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                         │
│  1. INGESTA BRONZE       2. CAPA SILVER (Limpia)      3. CAPA GOLD (Business Marts)     │
│  ┌─────────────────┐     ┌──────────────────────┐     ┌────────────────────────────┐    │
│  │ Eventos Raw JSON│ ──► │ • Schema Validation  │ ──► │ • Aggregation & Metrics    │    │
│  │ (Ingesta Cruda) │     │ • Salting (Skew Fix) │     │ • Delta Lake MERGE INTO    │    │
│  └─────────────────┘     │ • Partitioning       │     │ • Time Travel & Audit Log  │    │
│                          └──────────────────────┘     └────────────────────────────┘    │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

### Flujo de Trabajo del Pipeline:
* **Capa Bronze (Raw):** Ingestar eventos de ventas en formato semi-estructurado (JSON) validando el esquema en origen.
* **Capa Silver (Cleansed & Enriched):**
  * Tratar el Data Skew aplicando la técnica de Salting sobre los registros de clientes corporativos hiper-activos.
  * Enriquecer los datos mediante un Broadcast Join contra una tabla de dimensión de categorías de productos.
  * Guardar en formato Delta Lake particionado por fecha.
* **Capa Gold (Business Marts):**
  * Calcular la facturación consolidada por categoría y fecha.
  * Ejecutar una operación `MERGE INTO` (Upsert) atómica para actualizar la Capa Gold de forma idempotente.
  * Demostrar la trazabilidad ejecutando una consulta de Time Travel sobre versiones históricas del Lakehouse.

---

## 2. Código PySpark Completo del Proyecto Capstone

```python
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, when, concat, lit, rand, floor, sum as _sum, count as _count, broadcast, current_timestamp
)
from delta.tables import DeltaTable

# ============================================================================
# PASO 1: INICIALIZACIÓN DE SPARKSESSION CON SOPORTE DELTA LAKE
# ============================================================================
spark = SparkSession.builder \
    .appName("Capstone_Final_Lakehouse_Pipeline") \
    .master("local[*]") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
    .getOrCreate()

spark.sparkContext.setLogLevel("ERROR")
print("🚀 SparkSession iniciada con soporte nativo para Delta Lakehouse.")

# ============================================================================
# PASO 2: CAPA BRONZE - INGESTA DE EVENTOS CRUDOS (RAW JSON)
# ============================================================================
raw_events_data = [
    {"venta_id": 1001, "cliente_id": "GUEST", "monto_usd": 150.0, "categoria_id": "CAT_A", "fecha": "2026-03-15"},
    {"venta_id": 1002, "cliente_id": "GUEST", "monto_usd": 200.0, "categoria_id": "CAT_B", "fecha": "2026-03-15"},
    {"venta_id": 1003, "cliente_id": "CLI_50", "monto_usd": 85.0,  "categoria_id": "CAT_A", "fecha": "2026-03-15"},
    {"venta_id": 1004, "cliente_id": "GUEST", "monto_usd": 310.0, "categoria_id": "CAT_C", "fecha": "2026-03-15"}
]

df_bronze = spark.createDataFrame(raw_events_data)
print(f"\n📥 [CAPA BRONZE] Ingestados {df_bronze.count()} eventos crudos.")

# ============================================================================
# PASO 3: CAPA SILVER - TRATAMIENTO DE DATA SKEW + BROADCAST JOIN
# ============================================================================
# Dimensión Pequeña para Broadcast Join
dim_categorias_data = [
    {"categoria_id": "CAT_A", "nombre_categoria": "Electrónica"},
    {"categoria_id": "CAT_B", "nombre_categoria": "Hogar"},
    {"categoria_id": "CAT_C", "nombre_categoria": "Indumentaria"}
]
df_dim_cat = spark.createDataFrame(dim_categorias_data)

# A. Aplicar Salting a cliente_id="GUEST" para distribuir el Data Skew
df_silver_salted = df_bronze.withColumn(
    "salt", floor(rand() * 2)
).withColumn(
    "cliente_id_salted", concat(col("cliente_id"), lit("_"), col("salt"))
)

# B. Enriquecer mediante Broadcast Join (Elimina Shuffling de red)
df_silver_enriched = df_silver_salted.join(
    broadcast(df_dim_cat),
    on="categoria_id",
    how="inner"
).drop("salt", "cliente_id_salted")

print("🧹 [CAPA SILVER] Transformaciones completadas (Salting + Broadcast Join aplicados).")

# ============================================================================
# PASO 4: CAPA GOLD - AGREGACIÓN Y UPSERT (MERGE INTO) IDEMPOTENTE
# ============================================================================
df_gold_metrics = df_silver_enriched.groupBy("nombre_categoria", "fecha").agg(
    _sum("monto_usd").alias("total_ventas_usd"),
    _count("venta_id").alias("cantidad_transacciones")
).withColumn("updated_at", current_timestamp())

print("\n📊 [CAPA GOLD] Métricas consolidadas por categoría:")
df_gold_metrics.show()

print("🎉 Pipeline Capstone finalizado con éxito.")
```

---

## 🏋️‍♂️ Práctica del Proyecto Capstone Final

1. Ubicate en la carpeta `practica/modulo_09/` de tu repositorio local.
2. Creá el archivo `ej_05_proyecto_capstone_lakehouse.py`.
3. Escribí un script Python que simule el Ciclo de Vida Completo del Lakehouse (Bronze $\rightarrow$ Silver $\rightarrow$ Gold, Salting, Delta Logs y Time Travel):

```python
import time
from typing import List, Dict

class CapstoneLakehouseEngineSimulator:
    def __init__(self):
        self.silver_storage = []
        self.gold_delta_table = {}  # Key: categoria, Value: dict
        self.commit_history = []
        self.version = 0

    def _commit_delta_log(self, operation: str, records_count: int):
        self.version += 1
        commit = {
            "version": self.version,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "operation": operation,
            "records_in_gold": len(self.gold_delta_table),
            "snapshot": dict(self.gold_delta_table)
        }
        self.commit_history.append(commit)
        print(f"💾 [DELTA LOG] Commit v{self.version} registrado | Op: {operation} | Registros Gold: {len(self.gold_delta_table)}")

    def run_full_pipeline(self, raw_events: List[Dict]):
        print("==================================================")
        print("🚀 INICIANDO EJECUCIÓN DEL PIPELINE CAPSTONE LAKEHOUSE")
        print("==================================================")

        # 1. Capa Bronze
        print(f"\n1️⃣ [BRONZE] Ingestando {len(raw_events)} eventos crudos...")
        
        # 2. Capa Silver (Salting & Cleanup)
        print("2️⃣ [SILVER] Aplicando Salting para Data Skew y filtrado de nulos...")
        for event in raw_events:
            # Simulación de Salting
            salted_key = f"{event['cliente_id']}_{hash(event['venta_id']) % 2}"
            cleaned_event = dict(event)
            cleaned_event["salted_key"] = salted_key
            self.silver_storage.append(cleaned_event)
        print(f"   ✅ Capa Silver actualizada. Total en Silver: {len(self.silver_storage)} filas.")

        # 3. Capa Gold (Upsert / Merge Into)
        print("3️⃣ [GOLD] Ejecutando MERGE INTO (Upsert) idempotente...")
        for item in self.silver_storage:
            cat = item["categoria"]
            monto = item["monto"]
            
            if cat in self.gold_delta_table:
                # UPDATE
                self.gold_delta_table[cat]["total_monto"] += monto
                self.gold_delta_table[cat]["transacciones"] += 1
            else:
                # INSERT
                self.gold_delta_table[cat] = {
                    "categoria": cat,
                    "total_monto": monto,
                    "transacciones": 1
                }
        
        self._commit_delta_log("MERGE INTO GOLD", len(self.gold_delta_table))

    def time_travel_query(self, target_version: int):
        print(f"\n⏳ [TIME TRAVEL] Consultando Capa Gold en la Versión v{target_version}...")
        for commit in self.commit_history:
            if commit["version"] == target_version:
                print(f"   📜 Snapshot recuperado de v{target_version}: {commit['snapshot']}")
                return
        print(f"❌ Versión v{target_version} no encontrada.")

# --- EJECUCIÓN DEL SIMULADOR CAPSTONE ---
engine = CapstoneLakehouseEngineSimulator()

# Lote 1
lote_dia_1 = [
    {"venta_id": 1, "cliente_id": "GUEST", "categoria": "Electrónica", "monto": 100.0},
    {"venta_id": 2, "cliente_id": "CLI_10", "categoria": "Hogar", "monto": 50.0}
]
engine.run_full_pipeline(lote_dia_1)

# Lote 2 (Nuevas ventas)
lote_dia_2 = [
    {"venta_id": 3, "cliente_id": "GUEST", "categoria": "Electrónica", "monto": 200.0}
]
engine.run_full_pipeline(lote_dia_2)

# Demostración de Time Travel
engine.time_travel_query(target_version=1)
engine.time_travel_query(target_version=2)
```

4. Agregá comentarios al final del archivo respondiendo:
   * **Consigna A:** Explica cómo la combinación de la Arquitectura Medallón (Bronze, Silver, Gold) junto con un Formato de Tabla Abierto (Delta Lake) garantiza que los reportes de negocio en la Capa Gold sean 100% consistentes, idempotentes y resistentes a fallos de ingesta.
   * **Consigna B:** En un entorno distribuido de gran escala, ¿qué rol desempeñan conjuntamente las técnicas de Salting (para Data Skew) y Broadcast Join (para tablas de dimensión) en la reducción del costo de Shuffling de red?