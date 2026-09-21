# 🐍 Lección 33: Interacción con Bases de Datos Relacionales (`SQLAlchemy` y `psycopg2`)

En la Ingeniería de Datos, las bases de datos relacionales (como PostgreSQL, MySQL o SQL Server) son tanto fuentes primarias de ingesta (*OLTP*) como destinos de almacenamiento en esquemas modulares (*Data Warehouses / Marts*).

En esta lección aprenderemos a interactuar con bases de datos SQL desde Python utilizando el driver nativo **psycopg2** y la capa de abstracción **SQLAlchemy**, el estándar de la industria para gestionar conexiones, transacciones y pools de forma segura y eficiente.

---

## 1\. Driver Nativo (`psycopg2`) vs. Abstracción (`SQLAlchemy`)

* **psycopg2**: Es el adaptador/driver de bajo nivel más popular para conectar Python directamente con PostgreSQL.
* **SQLAlchemy**: Es un toolkit y ORM que abstrae el motor SQL subyacente. Permite cambiar entre PostgreSQL, MySQL, SQLite o Snowflake cambiando únicamente la URI de conexión (*Connection String*), sin modificar las consultas ni el código de negocio.

```
┌────────────────────────────────────────────────────────┐
│                   Tu Pipeline Python                   │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│              SQLAlchemy (Core / Engine)                │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│             Driver DB (psycopg2 / pymysql)             │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│              Base de Datos (PostgreSQL)                │
└────────────────────────────────────────────────────────┘

```

---

## 2\. Definir la Cadena de Conexión (Connection String)

La URI de conexión sintetiza las credenciales de acceso (obtenidas desde variables de entorno `.env` como aprendimos en la **Lección 16**):

```
# Sintaxis Estándar:
# motor+driver://usuario:contraseña@host:puerto/nombre_base_datos

postgresql+psycopg2://data_engineer:SecretPass123@127.0.0.1:5432/dw_ventas
sqlite:///:memory:   &lt;-- Base de datos en memoria (ideal para pruebas local/pytest)

```

---

## 3\. Conexión Segura, `text()` y Prevención de Inyección SQL

🚨 **La regla de oro de la seguridad SQL**: Nunca concatenes cadenas ni uses f-strings para construir consultas SQL con variables recibidas desde afuera. Esto expone tu pipeline a ataques catastróficos de **Inyección SQL**.

Utilizá siempre la función **text()** de SQLAlchemy con **parámetros nombrados**:

```
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

# Instanciamos el Motor de Conexión (Engine)
db_uri = os.getenv("DATABASE_URL", "sqlite:///:memory:")
engine = create_engine(db_uri, echo=False)

# Ejecución segura con administrador de contexto (cierra la conexión automáticamente)
with engine.connect() as conn:
    # Consulta parametrizada segura (:estado)
    query = text("SELECT id, cliente, monto FROM ventas WHERE estado = :estado")
    
    # Pasamos los parámetros dentro de un diccionario
    resultado = conn.execute(query, {"estado": "COMPLETADA"})
    
    for fila in resultado:
        print(f"ID: {fila.id} | Cliente: {fila.cliente} | Monto: ${fila.monto}")

```

---

## 4\. Control de Transacciones (`commit` y `rollback`)

Para modificar datos (*INSERT, UPDATE, DELETE*), debemos garantizar la **atomicidad**: o se guardan todos los cambios con éxito o se revierten completamente (*rollback*) si ocurre algún error.

El bloque `with engine.begin()` maneja la transacción de forma automática:

```
from sqlalchemy import text

# engine.begin() abre la transacción e inicia un commit automático al salir del bloque.
# Si dentro del bloque ocurre una excepción, ejecuta un ROLLBACK de forma automática.
try:
    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO ventas (cliente, monto, estado) VALUES (:cliente, :monto, :estado)"),
            [
                {"cliente": "Juan Perez", "monto": 1500.0, "estado": "COMPLETADA"},
                {"cliente": "Maria Gomez", "monto": 2300.5, "estado": "COMPLETADA"}
            ]
        )
    print("✅ Transacción completada con éxito (COMMIT).")
except Exception as e:
    print(f"🔴 Fallo en la transacción. Se ejecutó ROLLBACK: {e}")

```

---

## 5\. Integración Nativa con Pandas (`read_sql` y `to_sql`)

Pandas se integra directamente con los objetos `Engine` de SQLAlchemy para leer y escribir tablas de forma masiva:

```
import pandas as pd
from sqlalchemy import create_engine

engine = create_engine("sqlite:///:memory:")

# 1. Leer directamente el resultado de una consulta SQL a un DataFrame
df_ventas = pd.read_sql(
    sql="SELECT cliente, SUM(monto) as total FROM ventas GROUP BY cliente",
    con=engine
)

# 2. Escribir un DataFrame de Pandas hacia una tabla de la Base de Datos
# chunksize=1000 envía los registros por lotes para evitar saturar la memoria de la DB
df_ventas.to_sql(
    name="resumen_clientes",
    con=engine,
    if_exists="append",  # 'fail', 'replace' o 'append'
    index=False,
    chunksize=1000
)

```

---

## 🏋️‍♂️ Práctica de la Lección 33

1. Creá el archivo `ej_33_sqlalchemy.py` dentro de la carpeta `practica/`.
2. Escribí un script de **creación, inserción y consulta transaccional en SQLite**:
  * Importá `create_engine`, `text` de `sqlalchemy` y `pandas as pd`.
  * Creá un motor SQLite en memoria: `engine = create_engine("sqlite:///:memory:")`.
  * **Paso 1**: Creá una tabla llamada `transacciones` con columnas: `id` (INTEGER PRIMARY KEY), `cliente` (TEXT), `monto` (REAL), `categoria` (TEXT).
  * **Paso 2**: Usá `with engine.begin()` para insertar un lote de 4 transacciones parametrizadas de prueba.
  * **Paso 3**: Usá `pd.read_sql()` para consultar todas las transacciones donde `monto &gt; 100.0` y cargalas en un DataFrame.
  * **Paso 4**: Imprimí en pantalla el DataFrame obtenido y sus tipos de datos (`df.dtypes`).
3. Ejecutá tu script desde la terminal: `python3 practica/ej_33_sqlalchemy.py`