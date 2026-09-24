# 🏅 Lección 04.B (Módulo 04): Arquitectura Medallion en Data Lakes &amp; Lakehouses: Bronze, Silver y Gold

&gt; **Propósito**: Dominar el patrón de diseño de datos más extendido en la industria moderna de Data Lakes y Lakehouses (Databricks, Delta Lake, Apache Iceberg), comprendiendo la responsabilidad, nivel de calidad, gobernanza y esquema de almacenamiento en las capas **Bronze (Raw)**, **Silver (Cleaned/Enriched)** y **Gold (Business Aggregates)**.

---

## 📌 1\. ¿Qué es la Arquitectura Medallion y por qué reemplazó a los ETLs tradicionales?

En los inicios del Big Data, los Data Lakes solían convertirse en "Data Swamps" (pantanos de datos) debido a la acumulación desordenada de archivos CSV y JSON sin esquema ni validación.

La **Arquitectura Medallion** (o arquitectura de tres capas) establece una estructura lógica de procesamiento de datos por etapas, garantizando la calidad y trazabilidad incremental:

```
[ Fuentes de Datos ] ──(Ingesta Raw)──&gt; [ BRONZE (Raw Lake) ] ──(Limpieza/Schema)──&gt; [ SILVER (Enriched) ] ──(Agregaciones/BI)──&gt; [ GOLD (Business Marts) ]
  • APIs REST                             • Append-only                          • Schema enforcement                   • Aggregated tables
  • Transaccionales DBs                  • Formato original (JSON/CSV)          • Deduplicación                        • Modelos estrella
  • Eventos Kafka                         • Metadatos de ingesta                 • Tipado estricto                      • Formato Parquet/Delta

```

---

## 🔬 2\. Anatomía Detallada de las Tres Capas

### A. Capa Bronze (Raw / Ingesta Cruda)

* **Objetivo**: Capturar y conservar los datos exactamente como vienen del sistema origen.
* **Patrón de Ingesta**: *Append-Only* (Solo inserción).
* **Características**:  
  * No se aplican transformaciones, filtrados ni correcciones de tipo de dato.
  * Preserva el historial completo e inmutable para auditorías o re-procesamientos (*Replayability*).
  * Incluye metadatos de ingesta: `_ingested_at` (timestamp), `_source_file` o `_topic_name`.
  * **Formato habitual**: JSON, CSV, Avro o tablas Delta/Iceberg con esquema permisivo.

### B. Capa Silver (Cleaned, Enriched &amp; Conformed)

* **Objetivo**: Convertir los datos crudos en una fuente única de verdad (*Single Source of Truth*) limpia y conformada.
* **Transformaciones**:  
  * **Schema Enforcement &amp; Casting**: Conversión explícita de tipos de datos (strings a timestamps/integers).
  * **Deduplicación &amp; Idempotencia**: Eliminación de registros duplicados usando claves primarias/de negocio (`MERGE INTO` / `UPSERT`).
  * **Data Quality Checks**: Aplicación de Contratos de Datos y validación de nulos o valores fuera de rango.
  * **Enriquecimiento**: Uniones simples (*Lookups*) con dimensiones maestras (ej. asociar ID de cliente con datos del perfil).
* **Formato habitual**: Parquet, Delta Lake o Apache Iceberg.

### C. Capa Gold (Business / Curated / Analytics)

* **Objetivo**: Exponer vistas y agregaciones altamente optimizadas para el consumo de usuarios de negocio, herramientas de BI (Power BI, Tableau) y modelos de Machine Learning.
* **Modelado**:  
  * Tablas de Hechos y Dimensiones (Esquema Estrella / Copo de Nieve Kimball).
  * Tablas agregadas por periodo (ej. `ventas_diarias_por_region`).
* **Rendimiento**:  
  * Datos pre-calculados para garantizar tiempos de respuesta en milisegundos.
  * Control de acceso estricto por roles (RLS / Column-level security).

---

## 🛠️ 3\. Reglas de Inmutabilidad, Idempotencia y Trazabilidad

| Criterio             | Capa Bronze                        | Capa Silver                             | Capa Gold                |
| -------------------- | ---------------------------------- | --------------------------------------- | ------------------------ |
| **Mutabilidad**      | Inmutable (Append-Only)            | Mutable (`MERGE` / `UPDATE` / `DELETE`) | Mutable / Re-calculable  |
| **Audiencia**        | Data Engineers                     | Data Engineers, Data Scientists         | Data Analysts, BI, Execs |
| **Latencia**         | Streaming / Near-Real-Time / Batch | Batch / Micro-batch                     | Batch diario / Horario   |
| **Nivel de Calidad** | Bajo (Datos crudos/sucios)         | Alto (Validado/Limpio)                  | Máximo (Consolidado)     |

---

## ⚡ 4\. Implementación en Python con Polars / PyArrow

Podemos simular la progresión de las 3 capas utilizando **Polars** y exportando a archivos **Parquet**:

```
import polars as pl
from datetime import datetime

# ====================================================
# 1. CAPA BRONZE: Ingesta Raw (JSON con metadatos)
# ====================================================
raw_json_data = [
    {"id": "TX_101", "user_id": "U1", "amount": "150.50", "timestamp": "2026-09-24T10:00:00Z"},
    {"id": "TX_102", "user_id": "U2", "amount": "INVALID", "timestamp": "2026-09-24T10:05:00Z"},
    {"id": "TX_101", "user_id": "U1", "amount": "150.50", "timestamp": "2026-09-24T10:00:00Z"}, # Duplicado
]

# Agregar metadatos de ingesta
bronze_df = pl.DataFrame(raw_json_data).with_columns(
    pl.lit(datetime.now()).alias("_ingested_at"),
    pl.lit("api_transacciones_v1").alias("_source_sys")
)
bronze_df.write_parquet("layer_bronze_transacciones.parquet")
print("✅ Capa Bronze escrita (3 registros crudos).")

# ====================================================
# 2. CAPA SILVER: Limpieza, Casting y Deduplicación
# ====================================================
silver_df = (
    pl.read_parquet("layer_bronze_transacciones.parquet")
    # Castings defensivos (reemplazar montos inválidos por null)
    .with_columns(
        pl.col("amount").cast(pl.Float64, strict=False).alias("amount"),
        pl.col("timestamp").str.to_datetime(strict=False).alias("transaction_at")
    )
    # Filtrar registros corruptos (Quality Gate)
    .filter(pl.col("amount").is_not_null())
    # Deduplicación por clave primaria
    .unique(subset=["id"], keep="first")
)
silver_df.write_parquet("layer_silver_transacciones.parquet")
print("✅ Capa Silver escrita (1 registro válido y deduplicado).")

# ====================================================
# 3. CAPA GOLD: Agregación de Negocio
# ====================================================
gold_df = (
    pl.read_parquet("layer_silver_transacciones.parquet")
    .group_by("user_id")
    .agg(
        pl.col("amount").sum().alias("total_monto_comprado"),
        pl.col("id").count().alias("cantidad_transacciones")
    )
)
gold_df.write_parquet("layer_gold_resumen_usuarios.parquet")
print("✅ Capa Gold escrita (Métricas para BI).")
print(gold_df)

```

---

## 🧠 Checkpoint de Autoevaluación

1. ¿Por qué es fundamental conservar la capa **Bronze** intacta en lugar de transformar los datos directamente en la ingesta?
2. ¿Qué transformaciones y controles de calidad caracterizan a la capa **Silver**?
3. Explica la diferencia entre el patrón *Append-Only* de la capa Bronze y el patrón de *Merge/Upsert* de la capa Silver.
4. ¿En qué se diferencia el modelado de la capa **Gold** (agregaciones/modelo estrella) frente al almacenamiento de la capa Silver?