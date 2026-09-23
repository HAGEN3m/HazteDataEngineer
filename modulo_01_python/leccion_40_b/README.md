# 🐍 Lección 40.B: Arquitectura Interna de Apache Arrow y Motores Vectorizados (Polars vs. DuckDB)

&gt; **Propósito**: Comprender el formato de memoria columnar estandarizado (Apache Arrow), la ejecución vectorizada mediante instrucciones SIMD y las diferencias operativas entre motores OLAP modernos como Polars y DuckDB para procesar datasets masivos con velocidad cercana a código C/Rust.

---

## 📌 1\. El Límite de Pandas 1.x y la Revolución Columnar

Históricamente, Pandas (construido sobre NumPy y CPython) almacenaba datos utilizando un modelo orientado a filas o punteros heterogéneos.

```
Orientado a Filas (Row-Oriented):      [ID_1, Ana, 25, 1500.0] -&gt; [ID_2, Pedro, 30, 2200.0]
Orientado a Columnas (Columnar):        ID:   [ID_1, ID_2]
                                       Edad: [25, 30]
                                       Sueldo: [1500.0, 2200.0]

```

### ¿Por qué el modelo columnar es infinitamente más rápido para Analytics?

1. **Localidad de Caché de CPU (L1/L2/L3)**: Al calcular un promedio de sueldos, la CPU carga secuencialmente en caché solo el arreglo continuo de sueldos, ignorando las demás columnas.
2. **Ejecución Vectorizada (SIMD)**: *Single Instruction, Multiple Data*. Permite que los procesadores modernos ejecuten la misma instrucción matemática sobre 4, 8 o 16 valores numéricos simultáneamente en un solo ciclo de reloj.
3. **Compresión Extrema**: Al agrupar valores del mismo tipo de dato consecutivamente, algoritmos como *Dictionary Encoding* o *Run-Length Encoding (RLE)* reducen el tamaño en RAM drásticamente.

---

## 🔬 2\. Apache Arrow y la Interoperabilidad Zero-Copy

**Apache Arrow** es el estándar global de memoria en formato columnar de código abierto.

```
   [ Python / Polars ] &lt;─── Zero-Copy (Misma RAM) ───&gt; [ DuckDB / C++ ]
                                     │
                                     ▼
                             [ Apache Arrow ]

```

### Ventaja Crucial: Eliminación de la Serialización

Antes de Arrow, pasar datos de Python a C++ o Spark requería **serializar** (convertir objetos a bytes en disco/red) y **deserializar** (reconstruir los objetos), consumiendo hasta el 80% del tiempo total del proceso.

Con Apache Arrow, múltiples herramientas comparten el **mismo puntero de memoria RAM sin copiar datos** (*Zero-Copy Memory Sharing*).

---

## 🛠️ 3\. Polars vs. DuckDB: Comparativa de Motores Vectorizados

| Característica          | Polars                                                                       | DuckDB                                                              |
| ----------------------- | ---------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| **Lenguaje Core**       | Rust                                                                         | C++                                                                 |
| **Paradigma Principal** | DataFrames y API de Expresiones (`pl.col()`)                                 | SQL Nativo Embebido (*SQLite para Analytics*)                       |
| **Caso de Uso Ideal**   | Transformación de datos compleja, feature engineering y pipelines en Python. | Consultas SQL ad-hoc sobre Parquet/CSV gigantes sin importar datos. |
| **Motor de Ejecución**  | Multithreaded por bloques de vectores Arrow                                  | Vectorized Query Execution Engine (Streaming In-Memory)             |

---

## ⚡ 4\. Lazy Execution y Optimización de Consultas (*Query Engine*)

Tanto Polars como DuckDB utilizan un **Motor de Ejecución Perezoso (** **Lazy Engine** **)**:

```
[ Consulta Declarada ] ──&gt; [ Plan Lógico ] ──&gt; [ Query Optimizer ] ──&gt; [ Plan Físico Optimizado ] ──&gt; [ Ejecución ]

```

### Optimizaciones Automáticas Clave:

1. **Predicate Pushdown (Filtrado Temprano)**: Si pides registros donde `estado == 'ACTIVO'`, el motor aplica el filtro directamente en la fase de lectura del archivo Parquet, evitando cargar en RAM millones de filas innecesarias.
2. **Projection Pushdown (Selección de Columnas)**: Si el dataset tiene 100 columnas y solo utilizas 3, solo se leen de disco esas 3 columnas.

---

## 🏋️‍♂️ Ejercicio Práctico Hands-On: Benchmark de Polars y DuckDB sobre Parquet

Crea el archivo `benchmark_motores.py` para consultar un dataset en formato Parquet utilizando la API perezosa de Polars y consultas SQL en DuckDB:

```
import time
import duckdb
import polars as pl

# 1. Crear un dataset de prueba en formato Parquet
df_prueba = pl.DataFrame(
    {
        "cliente_id": range(1, 1_000_001),
        "categoria": ["A", "B", "C", "D"] * 250_000,
        "monto": [10.5, 20.0, 150.25, 500.0] * 250_000,
    }
)
df_prueba.write_parquet("transacciones.parquet")

# ----------------------------------------------------
# A. Procesamiento con Polars Lazy API
# ----------------------------------------------------
inicio_polars = time.perf_counter()

res_polars = (
    pl.scan_parquet("transacciones.parquet")  # Carga perezosa (Lazy)
    .filter(pl.col("monto") &gt; 100.0)  # Predicate Pushdown
    .group_by("categoria")
    .agg(
        pl.col("monto").sum().alias("monto_total"),
        pl.col("cliente_id").count().alias("total_clientes"),
    )
    .collect()  # Ejecución optimizada final
)

fin_polars = time.perf_counter()
print(f"✅ Polars Lazy ejecutado en: {fin_polars - inicio_polars:.4f} seg")
print(res_polars)

# ----------------------------------------------------
# B. Procesamiento con DuckDB (SQL sobre Parquet sin import)
# ----------------------------------------------------
inicio_duckdb = time.perf_counter()

res_duckdb = duckdb.sql("""
    SELECT 
        categoria,
        SUM(monto) AS monto_total,
        COUNT(cliente_id) AS total_clientes
    FROM 'transacciones.parquet'
    WHERE monto &gt; 100.0
    GROUP BY categoria
""").df()

fin_duckdb = time.perf_counter()
print(f"✅ DuckDB SQL ejecutado en: {fin_duckdb - inicio_duckdb:.4f} seg")
print(res_duckdb)

```

---

## 🧠 Checkpoint de Autoevaluación

1. ¿Por qué el almacenamiento orientado a columnas permite ejecutar instrucciones vectorizadas (SIMD) en los procesadores modernos?
2. ¿Qué significa que Apache Arrow permita la interoperabilidad *Zero-Copy* entre Python, Rust y C++?
3. ¿Cuál es la diferencia entre *Predicate Pushdown* y *Projection Pushdown* al leer un archivo Parquet?
4. ¿En qué escenario de ingeniería de datos elegirías usar DuckDB en lugar de Polars o Pandas?