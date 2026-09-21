# 🐘 Lección 06: Motores Columnares OLAP (`DuckDB` y `ClickHouse`) vs. Motores Transaccionales Row-Based (`PostgreSQL`) — Cómputo Vectorizado en SQL

En las lecciones anteriores del **Módulo 02** exploramos cómo optimizar bases de datos relacionales tradicionales como **PostgreSQL** mediante el análisis de planes de ejecución (`EXPLAIN ANALYZE`), estructuras de índices (`B-Tree`, `GIN`, `BRIN`) y particionamiento físico.

Sin embargo, a partir de ciertos volúmenes de datos o patrones de consulta puramente analíticos (ej. calcular agregaciones sobre miles de millones de filas), incluso una base de datos PostgreSQL perfectamente configurada e indexada llega a su límite de arquitectura.

En esta lección analizaremos el cambio de paradigma fundamental en la Ingeniería de Datos moderna: la diferencia entre **motores relacionales orientados a filas (** **OLTP / Row-Based** **)** y **motores columnares de alto rendimiento (** **OLAP / Columnar** **)** como **DuckDB** y **ClickHouse**, impulsados por **Cómputo Vectorizado**.

---

## 1\. Almacenamiento Orientado a Filas (OLTP) vs. Orientado a Columnas (OLAP)

### A. Motores Orientados a Filas (ej. PostgreSQL, MySQL, SQLite)

En PostgreSQL, los datos se almacenan físicamente en páginas de disco de 8 KB de forma **continua fila por fila**:

```
Página de Disco (8 KB):
[Fila 1: ID, Fecha, Cliente, Monto, Estado, Payload...] 
[Fila 2: ID, Fecha, Cliente, Monto, Estado, Payload...] 

```

* **Ventaja (OLTP)**: Excelente para **operaciones transaccionales rápidas**. Insertar una fila completa (`INSERT`) o modificar un usuario (`UPDATE`) requiere escribir un único bloque contiguo en disco.
* **Desventaja Analítica**: Si ejecutas `SELECT SUM(monto) FROM fact_ventas`, el motor debe **leer el 100% de la tabla de disco a RAM** (incluyendo nombres, payloads y estados) solo para extraer y sumar el campo `monto`.

### B. Motores Orientados a Columnas (ej. DuckDB, ClickHouse, Snowflake, Redshift)

En los motores columnares, los datos de cada columna se almacenan en bloques de disco contiguos e independientes:

```
Bloque Columna 'ID':    [1, 2, 3, 4, 5, ...]
Bloque Columna 'Monto': [100.5, 200.0, 50.2, 300.0, ...]  &lt;-- ⚡ Solo se lee este bloque
Bloque Columna 'Estado':[OK, OK, FAIL, OK, ...]

```

* **Ventaja (OLAP)**: Para calcular `SUM(monto)`, el motor **solo lee del disco el bloque de la columna** **monto**, ignorando por completo el resto de los atributos.
* **Compresión Extrema**: Al almacenar valores del mismo tipo contiguos en disco (ejemplo: millones de números enteros o fechas), los algoritmos de compresión (ZSTD, RLE, Bit-Packing) reducen el tamaño de almacenamiento entre un **70% y 90%**.

---

## 2\. Cómputo Vectorizado (*Vectorized Query Execution*)

Además de la disposición física en disco, la diferencia drástica de velocidad se debe al **Motor de Procesamiento de CPU**:

* **Procesamiento Fila por Fila (Volcano Model - PostgreSQL)**: Para cada fila devuelta por un escaneo, el motor realiza una llamada a función virtual en C para evaluar la expresión. Para 100 millones de filas, esto genera **100 millones de sobrecargas de funciones en CPU**.
* **Cómputo Vectorizado (DuckDB / ClickHouse)**: El motor procesa los datos en **vectores contiguos de memoria RAM** (lotes de 2,048 o 4,096 valores). Esto permite que los procesadores modernos utilicen instrucciones avanzadas **SIMD (** **Single Instruction, Multiple Data** **)**, aplicando una misma operación matemática sobre múltiples valores en un solo ciclo de reloj de la CPU.

---

## 3\. DuckDB: El "SQLite de la Analítica" en la Capa Moderna

En la lección 37 del Módulo 01 aprendimos sobre Polars. En el mundo SQL, **DuckDB** es el equivalente analítico: una base de datos columnar en memoria (*In-Process*), escrita en C++, que se ejecuta dentro del propio proceso de Python sin requerir un servidor ni cliente de base de datos externo.

### Zero-Copy e Ingesta Directa de Parquet / Data Lakes

DuckDB puede consultar directamente archivos **Parquet**, CSVs o tablas de PostgreSQL sin necesidad de importar los datos previamente a su propio formato interno:

```
-- Consulta analítica directa sobre miles de archivos Parquet usando DuckDB
SELECT 
    categoria, 
    COUNT(*) AS total_ventas,
    SUM(monto) AS volumen_total
FROM 'data_lake/ventas/*.parquet'
WHERE fecha &gt;= '2026-01-01'
GROUP BY categoria
ORDER BY volumen_total DESC;

```

---

## 📊 Matriz Comparativa: PostgreSQL vs. DuckDB vs. ClickHouse

| Criterio                  | PostgreSQL                             | DuckDB                                   | ClickHouse                              |
| ------------------------- | -------------------------------------- | ---------------------------------------- | --------------------------------------- |
| **Arquitectura**          | Servidor Relacional Row-Based          | Motor OLAP In-Process (Embedded)         | Servidor OLAP Distribuido Masivo        |
| **Caso de Uso Principal** | Aplicaciones OLTP, APIs, Transacciones | Analítica local, Transformación ELT, ETL | Data Warehouses gigantes, Telemetría    |
| **Procesamiento**         | Mono-hilo por query (Fila por fila)    | Multihilo Vectorizado en RAM             | Multihilo Vectorizado Distribuido       |
| **Consultas Parquet/S3**  | Vía extensiones (FDW - Lento)          | **Nativo y ultra rápido (Zero-Copy)**    | **Nativo (Escala Terabytes/Petabytes)** |
| **Despliegue**            | Requiere instancia DB                  | Simplemente `pip install duckdb`         | Requiere cluster o servicio gestionado  |

---

## 🏋️‍♂️ Práctica de la Lección 06

1. Ubicate en la carpeta `practica/modulo_02/` de tu repositorio local.
2. Creá el archivo `ej_06_duckdb_olap.py`.
3. Escribí un script en Python utilizando la librería `duckdb` (podés instalarla con `pip install duckdb` en tu entorno virtual):

```
import time
import duckdb

# Conexión a DuckDB en memoria RAM
con = duckdb.connect(database=":memory:")

# 1. Crear una tabla columnar sintética de 2,000,000 de filas en RAM
print("🚀 Generando dataset analítico de 2 millones de filas...")
con.execute("""
    CREATE TABLE fact_telemetria AS 
    SELECT 
        range AS id,
        (range % 100)::INT AS sensor_id,
        (random() * 1000)::DOUBLE AS lectura_monto,
        CASE WHEN range % 2 = 0 THEN 'SUDAMERICA' ELSE 'EUROPA' END AS region,
        CURRENT_DATE - (range % 365)::INT AS fecha
    FROM range(2000000);
""")

# 2. Medir tiempo de agregación vectorial
inicio = time.time()
res = con.execute("""
    SELECT 
        region, 
        COUNT(*) AS total_registros,
        ROUND(SUM(lectura_monto), 2) AS suma_total,
        ROUND(AVG(lectura_monto), 2) AS promedio
    FROM fact_telemetria
    WHERE fecha &gt;= '2026-01-01'
    GROUP BY region;
""").df()
fin = time.time()

print(res)
print(f"\n⏱️ Consulta OLAP vectorizada completada en {fin - inicio:.4f} segundos.")

```

1. Agregá comentarios en el script respondiendo:
  * **Consigna A**: ¿Por qué DuckDB es capaz de procesar agregaciones sobre 2 millones de filas en milisegundos sin requerir índices B-Tree previa creación?
  * **Consigna B**: ¿En qué capa del Data Lake (Bronze, Silver o Gold) resulta ideal utilizar DuckDB combinado con archivos Parquet?