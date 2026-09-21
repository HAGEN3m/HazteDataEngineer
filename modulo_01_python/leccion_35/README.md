# 🐍 Lección 34: Ingesta e Inserción Masiva de Datos (*Bulk Loading*) y Comando `COPY` en PostgreSQL

En la Ingeniería de Datos, uno de los desafíos más críticos de rendimiento ocurre al mover volúmenes masivos de datos (cientos de miles o millones de filas) desde archivos locales, Data Lakes o APIs hacia bases de datos relacionales.

Si intentás insertar 1,000,000 de registros usando sentencias `INSERT INTO` tradicionales fila por fila, el script puede tardar horas debido al enorme overhead de red, el parseo individual de sentencias SQL y la sobrecarga de transacciones. En esta lección aprenderemos las estrategias de **Bulk Loading** e ingesta de alto rendimiento usando **chunksize**, **executemany** y el protocolo nativo **COPY** de PostgreSQL.

---

## 1\. El Problema del `INSERT` Fila por Fila vs. Bulk Loading

¿Por qué insertar registros de a uno es tan lento?

* **Overhead de Red (Round-Trips)**: Cada `INSERT` envía un paquete de red desde Python hacia la base de datos y espera una respuesta de confirmación.
* **Parseo de Sentencias SQL**: El motor de la base de datos debe analizar la sintaxis, compilar y planificar la ejecución para cada fila individual.
* **Sobrecarga de Transacciones y WAL**: Genera millones de escrituras en el log de transacciones (*Write-Ahead Logging*).

### 📊 Comparación de Tiempos para 100,000 Filas:

| Método de Inserción                      | Tiempo Aprox.            | Ratio de Velocidad    |
| ---------------------------------------- | ------------------------ | --------------------- |
| **INSERT** **fila por fila**             | \~8 - 15 minutos         | 1x (Inviable)         |
| **to\_sql()** **con** **chunksize=5000** | \~10 - 20 segundos       | \~40x más rápido      |
| **COPY** **nativo de PostgreSQL**        | **\~0.5 - 1.5 segundos** | **\~600x más rápido** |

---

## 2\. Inserción Eficiente por Lotes en Pandas y SQLAlchemy (`chunksize`)

Cuando usamos Pandas para guardar un DataFrame en una base de datos mediante `df.to_sql()`, por defecto se intenta generar sentencias individuales o un solo bloque gigante.

Para optimizar el rendimiento sin agotar la memoria de la base de datos, debemos usar dos parámetros clave:

* **chunksize**: Divide los datos en bloques de N filas (ej. 5,000 o 10,000).
* **method="multi"**: Agrupa múltiples valores dentro de una sola instrucción SQL (`INSERT INTO tabla VALUES (row1), (row2), ...`).

```
import pandas as pd
from sqlalchemy import create_engine

engine = create_engine("sqlite:///:memory:")

# Dataset de prueba
df_ventas = pd.DataFrame({
    "transaccion_id": range(1, 50001),
    "monto": [100.5 * i for i in range(1, 50001)],
    "estado": "COMPLETADA"
})

# Inserción optimizada por lotes
df_ventas.to_sql(
    name="fact_ventas",
    con=engine,
    if_exists="append",
    index=False,
    chunksize=5000,      # Inserta en bloques de 5,000 filas
    method="multi"       # Combina múltiples VALUES en un solo INSERT
)

```

---

## 3\. La Técnica Definitiva: El Comando Nativo `COPY` de PostgreSQL

El comando **COPY** de PostgreSQL es el mecanismo de carga masiva más rápido disponible en bases de datos relacionales. En lugar de parsear instrucciones SQL, transmite los datos directamente en formato de texto plano o binario hacia los archivos de almacenamiento físico de la base de datos, omitiendo el validador de sintaxis SQL.

En Python, podemos combinar el driver **psycopg2** con un búfer de memoria **io.StringIO** para transmitir DataFrames a PostgreSQL sin necesidad de escribir archivos temporales en el disco.

```
import io
import pandas as pd
import psycopg2

def bulk_insert_copy_postgres(df: pd.DataFrame, nombre_tabla: str, conn_psycopg2) -&gt; None:
    """Carga masiva ultra rápida hacia PostgreSQL usando COPY y búfer en memoria RAM."""
    
    # 1. Creamos un búfer de texto en memoria RAM
    buffer = io.StringIO()
    
    # 2. Exportamos el DataFrame al búfer en formato CSV (sin índice ni encabezados)
    df.to_csv(buffer, index=False, header=False, sep="\t")
    buffer.seek(0)  # Rebobinamos el cursor al inicio del búfer
    
    # 3. Ejecutamos copy_expert usando el cursor nativo de psycopg2
    cursor = conn_psycopg2.cursor()
    try:
        sql_copy = f"COPY {nombre_tabla} FROM STDIN WITH (FORMAT csv, DELIMITER '\t', NULL '')"
        cursor.copy_expert(sql=sql_copy, file=buffer)
        conn_psycopg2.commit()
        print(f"🚀 Carga masiva completada: {len(df)} filas insertadas con COPY.")
    except Exception as e:
        conn_psycopg2.rollback()
        print(f"🔴 Error durante el COPY: {e}")
    finally:
        cursor.close()

```

---

## 4\. Patrón de Arquitectura: Staging Table + Upsert (`ON CONFLICT`)

En pipelines de producción, realizar un `COPY` directo sobre las tablas principales de tu Data Warehouse puede ser riesgoso si el lote contiene registros duplicados o corruptos.

El patrón recomendado por arquitectos de datos consta de 3 pasos:

```
┌────────────────┐      COPY (Ultra Rápido)      ┌───────────────────────┐
│ DataFrame /    │ ────────────────────────────&gt; │  Tabla Temporal       │
│ CSV de Ingesta │                               │  (staging_ventas)     │
└────────────────┘                               └──────────┬────────────┘
                                                            │
                                         SQL INSERT ...     │
                                         ON CONFLICT UPDATE │
                                                            ▼
                                                 ┌───────────────────────┐
                                                 │  Tabla Final          │
                                                 │  (fact_ventas)        │
                                                 └───────────────────────┘

```

```
-- Ejemplo de Upsert final desde Staging hacia la Tabla Principal
INSERT INTO fact_ventas (transaccion_id, monto, estado, fecha_actualizacion)
SELECT transaccion_id, monto, estado, NOW()
FROM staging_ventas
ON CONFLICT (transaccion_id) 
DO UPDATE SET 
    monto = EXCLUDED.monto,
    estado = EXCLUDED.estado,
    fecha_actualizacion = NOW();

```

---

## 🏋️‍♂️ Práctica de la Lección 34

1. Creá el archivo `ej_34_bulk_loading.py` dentro de la carpeta `practica/`.
2. Escribí un script de **benchmark de inserción masiva en SQLite**:
  * Importá `time`, `io`, `pandas as pd` y `sqlite3`.
  * Creá una conexión SQLite en memoria: `conn = sqlite3.connect(":memory:")`.
  * Creá la tabla `ventas_bulk`: `(id INTEGER, cliente TEXT, monto REAL)`.
  * Generá un DataFrame de prueba de **50,000 filas**:

```
df_test = pd.DataFrame({
    "id": range(1, 50001),
    "cliente": [f"Cliente_{i}" for i in range(1, 50001)],
    "monto": [99.9 * i for i in range(1, 50001)]
})

```

1. **Prueba A**: Medí el tiempo de insertar el DataFrame usando `df_test.to_sql("ventas_bulk", conn, if_exists="replace", index=False)` sin `chunksize`.
2. **Prueba B**: Medí el tiempo de insertar el mismo DataFrame usando `df_test.to_sql("ventas_bulk", conn, if_exists="replace", index=False, chunksize=5000, method="multi")`.
3. Imprimí la diferencia de tiempo entre ambas ejecuciones.
4. Ejecutá tu script desde la terminal: `python3 practica/ej_34_bulk_loading.py`