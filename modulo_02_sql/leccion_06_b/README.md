# 🦆 Lección 06.B: Analytics en Data Lakes con DuckDB: Parquet, S3 y Pushdowns

&gt; **Propósito**: Dominar el análisis de datos de alto rendimiento directamente sobre Data Lakes (archivos Parquet en S3/MinIO) utilizando **DuckDB**, aprovechando la lectura de metadatos (footers), las optimizaciones de *Predicate/Projection Pushdown* y la integración *Zero-Copy* con el ecosistema de Python y Apache Arrow.

---

## 📌 1\. ¿Por qué DuckDB para Data Lakes?

Tradicionalmente, consultar un Data Lake con terabytes de archivos Parquet requería encender un clúster de **Apache Spark**, levantar un almacén en **Snowflake/BigQuery**, o usar motores como **Trino/Presto**.

**DuckDB** revoluciona esta arquitectura al ser un motor OLAP **embebido** (*in-process*):

* **Cero Infraestructura**: Corre dentro del mismo proceso de Python o ejecutable sin levantar servidores ni demonios.
* **Procesamiento Vectorizado**: Ejecuta consultas SQL sobre Parquet a velocidades comparables o superiores a clústeres distribuidos para volúmenes de hasta cientos de gigabytes.
* **Streaming In-Memory**: Puede procesar archivos más grandes que la memoria RAM disponible reduciendo el buffer al disco (*out-of-core processing*).

```
   [ Servidor S3 / MinIO ] (Archivos Parquet)
              │
              │  HTTP Range Requests (Solo lee metadatos + columnas necesarias)
              ▼
   [ Proceso de Python + DuckDB ] (Vectorized Execution + Zero-Copy)
              │
              ▼
   [ DataFrame de Polars / PyArrow ] (Sin costo de serialización)

```

---

## 🔬 2\. Cómo lee DuckDB un archivo Parquet en S3: Footers y Pushdowns

Un archivo Parquet almacena los datos en **Row Groups** (grupos de filas) y las columnas de forma contigua. Al final del archivo existe un **Footer (metadatos)** con estadísticas (valores MÍNIMO y MÁXIMO por columna y por grupo de filas).

```
+-------------------------------------------------------------------+
| ROW GROUP 1 (Filas 1 - 100,000)                                   |
|   Columna 'edad': [min: 18, max: 25]                              |
+-------------------------------------------------------------------+
| ROW GROUP 2 (Filas 100,001 - 200,000)                             |
|   Columna 'edad': [min: 40, max: 65]                              |
+-------------------------------------------------------------------+
| FOOTER: Metadatos del archivo, esquemas y límites por Row Group   |
+-------------------------------------------------------------------+

```

### El Flujo de Lectura Eficiente

1. **HTTP Range Request al Footer**: DuckDB realiza una petición HTTP solicitando únicamente los últimos bytes del archivo en S3 para leer el Footer.
2. **Projection Pushdown**: Si la consulta pide 2 de 50 columnas, DuckDB solo solicita las secciones del archivo donde habitan esas 2 columnas.
3. **Predicate Pushdown**: Si ejecutas `WHERE edad &lt; 30`, DuckDB lee los metadatos del *Row Group 2* (`min: 40, max: 65`), determina que NINGUNA fila cumple la condición y **descarta descargar ese bloque de S3 completo**.

---

## 🛠️ 3\. Integración Zero-Copy con Apache Arrow y Polars

DuckDB utiliza el estándar de memoria **Apache Arrow**. Esto permite ejecutar consultas SQL sobre objetos de Python y devolver los resultados directamente a **Polars** o **Pandas** sin duplicar ni copiar la memoria RAM.

```
import duckdb
import polars as pl

# 1. Objeto Polars en RAM
df_polars = pl.DataFrame({"id": [1, 2, 3], "monto": [100.0, 250.0, 500.0]})

# 2. DuckDB consulta directamente el objeto en RAM de Polars (Zero-Copy)
resultado_df = duckdb.sql("""
    SELECT 
        AVG(monto) AS monto_promedio
    FROM df_polars
    WHERE monto &gt; 150.0
""").pl()  # Devuelve de nuevo un DataFrame de Polars

print(resultado_df)

```

---

## ⚡ 4\. Consultas Directas a S3 con Extensión `httpfs`

DuckDB permite configurar credenciales de AWS / S3 o almacenamiento compatible con S3 (MinIO, Cloudflare R2, DigitalOcean Spaces) mediante la extensión `httpfs`.

```
-- Configurar acceso a S3 en DuckDB
INSTALL httpfs;
LOAD httpfs;

SET s3_region = 'us-east-1';
SET s3_access_key_id = 'TU_ACCESS_KEY';
SET s3_secret_access_key = 'TU_SECRET_KEY';

-- Consulta SQL analítica directa sobre miles de archivos Parquet usando comodines
SELECT 
    DATE_TRUNC('month', fecha_transaccion) AS mes,
    pais_id,
    SUM(monto) AS total_ventas,
    COUNT(DISTINCT cliente_id) AS clientes_unicos
FROM 's3://mi-bucket-datalake/gold/ventas/*/*.parquet'
WHERE fecha_transaccion &gt;= '2026-01-01'
GROUP BY ALL
ORDER BY mes DESC, total_ventas DESC;

```

---

## 🏋️‍♂️ Ejercicio Práctico Hands-On: Pipeline de Consulta sobre Parquet Local

Crea el archivo `consultas_datalake.py` para medir la diferencia de velocidad entre leer un CSV completo frente a consultar Parquet con Pushdown:

```
import time
import duckdb
import polars as pl

# 1. Crear dataset de prueba masivo
print("Generando dataset de prueba...")
df_masivo = pl.DataFrame(
    {
        "id": range(1, 2_000_001),
        "categoria": ["Electronica", "Hogar", "Ropa", "Jardín"] * 500_000,
        "monto": [15.0, 120.5, 450.0, 89.9] * 500_000,
        "region": ["LATAM", "US", "EU", "APAC"] * 500_000,
    }
)

df_masivo.write_parquet("datalake_ventas.parquet")
print("Archivo 'datalake_ventas.parquet' creado.")

# 2. Consulta con DuckDB aprovechando Projection y Predicate Pushdown
inicio = time.perf_counter()

query_pushdown = """
    SELECT 
        categoria,
        SUM(monto) AS total_monto,
        COUNT(*) AS total_ventas
    FROM 'datalake_ventas.parquet'
    WHERE region = 'LATAM' AND monto &gt; 100.0
    GROUP BY categoria
    ORDER BY total_monto DESC
"""

resultado = duckdb.sql(query_pushdown).pl()
fin = time.perf_counter()

print(f"\n✅ Consulta completada en {fin - inicio:.4f} segundos:")
print(resultado)

```

---

## 🧠 Checkpoint de Autoevaluación

1. ¿Qué información almacena el *Footer* de un archivo Parquet y cómo la utiliza DuckDB para optimizar las descargas desde S3?
2. Explica la diferencia entre *Projection Pushdown* y *Predicate Pushdown* en el contexto de un Data Lake.
3. ¿Por qué se dice que la integración entre DuckDB y Polars/PyArrow es *Zero-Copy*?
4. ¿En qué casos es preferible usar DuckDB directamente sobre archivos Parquet en lugar de cargar los datos en una base de datos relacional tradicional?