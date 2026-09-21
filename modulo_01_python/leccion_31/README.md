# 🐍 Lección 31: Procesamiento Eficiente de Archivos Parquet y Almacenamiento Columnar

¡Damos la bienvenida al **Bloque 4: Python para Data Engineering Ssr (Lecciones 31 a 40)**[1]!

En los bloques anteriores aprendimos los cimientos del lenguaje, la programación modular y las herramientas avanzadas de desarrollo (entornos virtuales, testing, logging y concurrencia). En este nuevo bloque daremos el salto hacia las arquitecturas de **Ingeniería de Datos a escala productiva**, comenzando por cómo se almacenan y procesan los volúmenes masivos de datos en Data Lakes y Data Warehouses modernos[2].

---

## 1\. Formatos de Fila (CSV/JSON) vs. Formatos Columnares (Apache Parquet)

En las etapas iniciales es común trabajar con archivos planos orientados a filas como **CSV** o **JSON**[3]. Sin embargo, a medida que los volúmenes de datos escalan a gigabytes o terabytes, estos formatos presentan graves limitaciones de rendimiento y costo[2][3].

### A. Formato Orientado a Filas (CSV / JSON)

Los datos se almacenan registro por registro de forma continua en disco.

* **Ventaja**: Excelente para operaciones transaccionales (OLTP) donde se necesita insertar o leer un registro completo con todos sus atributos a la vez.
* **Desventaja en Analítica**: Si tenés una tabla con 100 columnas y 50 millones de filas, pero solo querés calcular el promedio de la columna `monto`, el motor tiene que **leer el 100% del archivo** en disco para descartar las 99 columnas que no necesitás.

### B. Formato Orientado a Columnas (Apache Parquet)

**Apache Parquet** es un formato abierto de almacenamiento columnar comprimido y binario, diseñado para consultas analíticas de alto rendimiento (OLAP)[2][3].

* **Proyección de Columnas (** **Column Projection Pushdown** **)**: Permite leer únicamente las columnas especificadas en la consulta, ignorando físicamente el resto de los datos del disco[3].
* **Compresión Extrema**: Como todos los valores de una misma columna son del mismo tipo de dato, los algoritmos de compresión (Snappy, ZSTD) logran reducciones de tamaño de entre **70% y 90%** comparado con un CSV.
* **Metadatos e Inserción de Filas (** **Predicate Pushdown** **)**: Parquet guarda metadatos (valores mínimo y máximo) por bloques de filas (*Row Groups*). Si filtrás `monto &gt; 1000`, el lector puede saltearse bloques enteros de datos sin siquiera leerlos.

---

## 2\. Apache Arrow y el Ecosistema Python

**Apache Arrow** es el estándar de representación de datos columnares en memoria RAM sin costo de copia (*zero-copy*)[4][5]. Tanto Pandas como PyArrow y DuckDB utilizan Apache Arrow internamente para procesar Parquet a velocidades vertiginosas[4][5].

En Python, la lectura y escritura de Parquet se realiza principalmente con las librerías `pyarrow` o `fastparquet`, integradas de forma nativa en `pandas`[6]:

```
import pandas as pd

# Lectura básica
df = pd.read_parquet("ventas.parquet")

# Lectura defensiva y optimizada: Solo cargamos las columnas necesarias
df_subconjunto = pd.read_parquet(
    "ventas.parquet", 
    columns=["transaccion_id", "monto", "fecha"]
)

```

---

## 3\. Particionamiento de Datasets en Disco (*Partitioning*)

Cuando guardamos un dataset gigante en formato Parquet, la mejor práctica es dividirlo físicamente en subcarpetas según claves organizativas (como fechas o regiones)[2][3]:

```
data_lake/ventas/
├── anio=2026/
│   ├── mes=01/
│   │   ├── particion_001.parquet
│   │   └── particion_002.parquet
│   └── mes=02/
│       └── particion_001.parquet

```

Al consultar datos de una fecha específica (`anio == 2026 and mes == 01`), la librería solo abrirá los archivos dentro de esa carpeta en particular, evitando escanear el resto del Data Lake (*Partition Pruning*).

```
import pandas as pd

# Guardar un DataFrame particionado por columna en disco
df.to_parquet(
    "data_lake/ventas/",
    partition_cols=["anio", "mes"],
    engine="pyarrow"
)

```

---

## 4\. Comparación Práctica: CSV vs. Parquet

| Criterio                 | Archivo CSV                                    | Archivo Apache Parquet                                 |
| ------------------------ | ---------------------------------------------- | ------------------------------------------------------ |
| **Estructura**           | Orientado a filas (Texto plano)[3]           | Orientado a columnas (Binario)[3]                    |
| **Tipos de Datos**       | Sin esquema (todo ingresa como texto)          | Esquema tipado estricto (int64, float, timestamp)[3] |
| **Compresión**           | Sin compresión por defecto (Archivos pesados)  | Alta compresión integrada (Snappy/ZSTD)[3]           |
| **Velocidad de Lectura** | Lenta (debe parsear texto e interpretar tipos) | Ultra rápida (lectura vectorial directa)[4][5]     |
| **Filtros/Selección**    | Debe leer todas las filas y columnas           | Lee solo las columnas y particiones requeridas[3]    |

---

## 🏋️‍♂️ Práctica de la Lección 31

1. Creá el archivo `ej_31_parquet.py` dentro de la carpeta `practica/`.
2. Escribí un script de **conversión, compresión y benchmark de rendimiento**:
  * Instalá las dependencias en tu entorno virtual: `pip install pyarrow pandas`.
  * **Paso 1**: Generá un dataset sintético de 100,000 filas con las columnas: `id`, `fecha`, `categoria`, `monto`, `descripcion_larga`.
  * **Paso 2**: Guardá el dataset en formato CSV (`practica/dataset_test.csv`) y en formato Parquet (`practica/dataset_test.parquet`).
  * **Paso 3**: Medí y compará:
    * El tamaño en disco (Megabytes) de ambos archivos con el módulo `os.path.getsize()`.
    * El tiempo de lectura completa de ambos archivos.
    * El tiempo de lectura parcial cargando solo las columnas `id` y `monto` desde Parquet vs. cargando todo el CSV.
  * **Paso 4**: Guardá una versión particionada por `categoria` dentro de la carpeta `practica/data_lake_parquet/`.
3. Ejecutá tu script desde la terminal: `python3 practica/ej_31_parquet.py`