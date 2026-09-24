## 📌 1\. Paradigm Shift: Workflow-Centric (Airflow) vs. Asset-Centric (Dagster)

Durante años, la orquestación de datos estuvo dominada por el paradigma **Workflow-Centric** (centrado en flujos de trabajo). En herramientas como Apache Airflow, la unidad fundamental de cómputo es la **Tarea** (*Task*), organizada en un Grafo Acíclico Dirigido (**DAG**).

### El Dilema del Workflow-Centric:

* **Airflow responde**: *"Ejecuta la Tarea A, luego la Tarea B y finalmente la Tarea C a las 02:00 AM"*.
* **El negocio pregunta**: *"¿Está actualizada la tabla* *gold\_daily\_revenue* *en Snowflake y cuál es su linaje?"*.

En Airflow, las tablas, archivos Parquet o modelos de ML son "efectos secundarios" no rastreados explícitamente por el orquestador.

```
❌ WORKFLOW-CENTRIC (Airflow):
[ Task: extract_data ] ──&gt; [ Task: transform_data ] ──&gt; [ Task: load_data ]
  (El orquestador solo ve tareas pasando estado SUCCESS/FAILED, ignora qué datos se produjeron)

✅ ASSET-CENTRIC (Dagster):
[ Asset: raw_sales_csv ] ──&gt; [ Asset: silver_sales_table ] ──&gt; [ Asset: gold_revenue_metrics ]
  (El orquestador rastrea directamente el estado, esquema, volumen y linaje del activo producido)

```

### La Filosofía Asset-Centric (Dagster):

Dagster introduce los **Software-Defined Assets (SDAs)**. Un activo es un objeto del mundo real (una tabla en PostgreSQL, un bucket en S3, un modelo de Scikit-Learn o un reporte en Tableau). En Dagster, defines **qué activo debe existir** y **el código necesario para calcularlo**.

---

## 🔬 2\. Anatomía de un Software-Defined Asset (SDA)

Un *Software-Defined Asset* une tres elementos indispensables:

1. **Un Nombre de Activo**: Identificador único en el catálogo de datos (ej. `silver_users`).
2. **Un Conjunto de Upstream Assets**: Las dependencias requeridas para calcularlo.
3. **Una Función de Cómputo**: El código Python/SQL que transforma las entradas en la salida.

```
from dagster import asset, AssetIn
import polars as pl

@asset(group_name="bronze")
def raw_orders() -&gt; pl.DataFrame:
    """Ingesta desde API o S3 hacia la capa Bronze."""
    return pl.read_csv("https://api.internal/orders.csv")

@asset(group_name="silver")
def clean_orders(raw_orders: pl.DataFrame) -&gt; pl.DataFrame:
    """Limpia y valida los pedidos de la capa Bronze.
    
    Dagster infiere automáticamente que 'clean_orders' depende de 'raw_orders'
    simplemente leyendo el argumento de la función.
    """
    return raw_orders.filter(pl.col("status") != "CANCELLED").with_columns(
        pl.col("amount").cast(pl.Float64)
    )

```

### Linaje Automático (*Data Lineage*):

Al declarar que la función `clean_orders` recibe como parámetro `raw_orders`, Dagster construye automáticamente la gráfica de linaje sin necesidad de declarar dependencias explícitas con operadores como `&gt;&gt;`.

---

## 🛠️ 3\. I/O Managers: Abstracción de Almacenamiento

Uno de los mayores antipatrones en scripts de ingeniería de datos es mezclar la **lógica de transformación** con la **lógica de persistencia/lectura**:

```
# ❌ CÓDIGO ACOPLADO Y DIFÍCIL DE TESTEAR:
def process_data():
    df = pd.read_parquet("s3://my-bucket/raw.parquet") # Lectura acoplada
    df_clean = df.dropna()
    df_clean.to_sql("clean_table", con=engine)        # Escritura acoplada

```

Dagster resuelve esto mediante los **I/O Managers** (*Input/Output Managers*).

```
[ Función Python: Retorna DataFrame ] 
                 │
                 ▼
     [ IOManager (DuckDB / S3) ]
      ├── Convierte DataFrame a Parquet / Tabla
      └── Guarda en almacenamiento configurado

```

### Ventajas de los I/O Managers:

1. **Separación de Responsabilidades**: Tu código solo transforma datos en memoria (DataFrames/Dicts). El `IOManager` maneja la conexión, escritura y lectura.
2. **Entornos Intercambiables**: Puedes ejecutar el pipeline localmente guardando en `DuckDBIOManager` o `FilesystemIOManager`, y en producción cambiando el recurso a `SnowflakeIOManager` o `S3ParquetIOManager` **sin cambiar una sola línea del código de tus activos**.

---

## ⚡ 4\. Particionamiento Incremental y Backfills

En pipelines de producción, rara vez procesamos la totalidad de los datos en cada ejecución. Dagster soporta **Particiones** de forma nativa para procesar rangos temporales o categóricos.

```
from dagster import DailyPartitionsDefinition, asset, AssetExecutionContext
import polars as pl

# Definición de partición diaria
daily_partitions = DailyPartitionsDefinition(start_date="2026-01-01")

@asset(partitions_def=daily_partitions)
def daily_user_activity(context: AssetExecutionContext) -&gt; pl.DataFrame:
    # Obtener la fecha de la partición actual (ej. '2026-09-24')
    partition_date = context.partition_key
    
    # Leer solo los datos del día correspondiente
    df = pl.read_parquet(f"s3://my-bucket/events/{partition_date}/*.parquet")
    
    return df.group_by("user_id").agg(pl.len().alias("total_events"))

```

### Backfills con un Solo Comando:

Si la lógica de un activo cambia, puedes ejecutar un **Backfill** desde la UI de Dagster o la CLI para re-procesar automáticamente los últimos 6 meses de particiones en paralelo de forma segura.

---

## 🏋️‍♂️ Ejercicio Práctico Hands-On: Pipeline Completo Medallion en Dagster

Construiremos un pipeline completo con 3 activos (Bronze, Silver y Gold), métricas de calidad (*Asset Materialization Metadata*) e I/O Manager efímero:

```
from dagster import (
    asset, 
    Definitions, 
    MetadataValue, 
    Output, 
    AssetExecutionContext,
    FilesystemIOManager
)
import polars as pl
import datetime

# --------------------------------------------------------------------
# 1. Capa Bronze: Ingesta Raw
# --------------------------------------------------------------------
@asset(group_name="medallion_bronze")
def bronze_transactions() -&gt; Output[pl.DataFrame]:
    """Simula la ingesta de transacciones crudas desde un sistema OLTP."""
    data = {
        "tx_id": [101, 102, 103, 104, 105],
        "user_id": [1, 2, 1, 3, 2],
        "amount": [150.50, -20.00, 300.00, 0.00, 450.75],
        "timestamp": [
            "2026-09-24T10:00:00", 
            "2026-09-24T10:05:00", 
            "2026-09-24T10:10:00",
            "2026-09-24T10:15:00",
            "2026-09-24T10:20:00"
        ]
    }
    df = pl.DataFrame(data)
    
    return Output(
        value=df,
        metadata={
            "row_count": len(df),
            "preview": MetadataValue.md(df.head(3).to_pandas().to_markdown())
        }
    )

# --------------------------------------------------------------------
# 2. Capa Silver: Limpieza y Filtrado de Anomalías
# --------------------------------------------------------------------
@asset(group_name="medallion_silver")
def silver_transactions(bronze_transactions: pl.DataFrame) -&gt; Output[pl.DataFrame]:
    """Filtra montos inválidos (&lt;= 0) y parsea timestamps."""
    clean_df = (
        bronze_transactions
        .filter(pl.col("amount") &gt; 0)
        .with_columns(pl.col("timestamp").str.to_datetime())
    )
    
    invalid_records = len(bronze_transactions) - len(clean_df)
    
    return Output(
        value=clean_df,
        metadata={
            "valid_records": len(clean_df),
            "dropped_records": invalid_records,
            "total_volume_usd": float(clean_df["amount"].sum())
        }
    )

# --------------------------------------------------------------------
# 3. Capa Gold: Agregación de Negocio
# --------------------------------------------------------------------
@asset(group_name="medallion_gold")
def gold_user_revenue(silver_transactions: pl.DataFrame) -&gt; Output[pl.DataFrame]:
    """Calcula el ingreso total por usuario para la capa analítica."""
    gold_df = (
        silver_transactions
        .group_by("user_id")
        .agg(
            pl.sum("amount").alias("total_spent"),
            pl.len().alias("transaction_count")
        )
        .sort("total_spent", descending=True)
    )
    
    return Output(
        value=gold_df,
        metadata={
            "unique_customers": len(gold_df),
            "top_customer_id": int(gold_df[0, "user_id"]),
            "top_customer_spent": float(gold_df[0, "total_spent"])
        }
    )

# --------------------------------------------------------------------
# Definición del Proyecto (Definitions)
# --------------------------------------------------------------------
defs = Definitions(
    assets=[bronze_transactions, silver_transactions, gold_user_revenue],
    resources={
        "io_manager": FilesystemIOManager(base_dir="/tmp/dagster_storage")
    }
)

```

---

## 🧠 Checkpoint de Autoevaluación

1. ¿Cuál es la diferencia fundamental entre el enfoque *Workflow-Centric* de Airflow y el *Asset-Centric* de Dagster?
2. ¿Cómo construye Dagster la gráfica de linaje de datos (*Data Lineage*) sin necesidad de declarar dependencias explícitas?
3. ¿Qué beneficio aporta un `IOManager` al separar la lógica de transformación de la persistencia física de datos?
4. ¿Cómo permite la propiedad `partitions_def` realizar ejecuciones incrementales y re-procesamientos (*Backfills*) eficientes?