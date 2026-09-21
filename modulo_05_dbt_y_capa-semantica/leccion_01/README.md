# 🚀 Lección 01: Fundamentos de dbt Core y el Paradigma ELT in-Warehouse

En los módulos anteriores aprendiste a procesar datos con Python y Polars (Módulo 01), optimizar motores relacionales a bajo nivel (Módulo 02), empaquetar entornos aislados con Docker (Módulo 03) y diseñar modelos analíticos multidimensionales en capas Medallón (Módulo 04).

En este **Módulo 05** adoptaremos la herramienta estándar de la industria que revolucionó el rol del Data Engineer y dio origen a la **Ingeniería de Analítica (** **Analytics Engineering** **)**: **dbt (data build tool)**.

---

## 1\. El Cambio de Paradigma: De ETL Tradicional a ELT Moderno

Para entender por qué nació dbt, debemos comprender la evolución de la arquitectura de datos:

```
ETL TRADICIONAL (Años 2000 - 2015):
[Fuente OLTP] ──► [ Servidor ETL Externo ] ──► [ Data Warehouse ]
                  (Python/Informatica/Talend)  (Solo almacena datos finales)
                  • Cómputo fuera de la DB
                  • Lento y costoso de escalar

ELT MODERNO (Data Warehousing Moderno):
[Fuente OLTP] ──► [ Carga Cruda (Bronze) ] ──► [ Transformación in-Warehouse (dbt) ]
                  (Fivetran / Airbyte / Python)  (Aprovecha la potencia SQL del DW)
                                                 • Bronze ──► Silver ──► Gold

```

### A. El Modelo Antiguo (ETL - Extract, Transform, Load)

En el pasado, los motores de bases de datos analíticas eran costosos y lentos. Por eso, los datos se extraían de las fuentes y **se transformaban fuera de la base de datos** (en servidores dedicados de Python, Talend o Informatica) antes de cargar el resultado final.

* **Inconveniente**: Duplicación de infraestructura, pipelines frágiles, lógica de negocio dispersa en scripts imperativos y bajo rendimiento al procesar volumen.

### B. El Modelo Moderno (ELT - Extract, Load, Transform)

Con la llegada de los Data Warehouses columnares y distribuidos de alta velocidad (Snowflake, BigQuery, ClickHouse, DuckDB, PostgreSQL), extraer y cargar datos crudos a la capa **Bronze** se volvió instantáneo.

Ahora, las transformaciones se realizan **directamente dentro del Data Warehouse utilizando SQL**, aprovechando la velocidad y capacidad de cómputo paralelo del propio motor analítico.

---

## 2\. ¿Qué es dbt (data build tool) y qué problema resuelve?

**dbt** es la herramienta enfocada exclusivamente en la **"T" (Transform) del paradigma ELT**.

Su lema principal es: **"Escribí únicamente sentencias** **SELECT** **de SQL; dbt se encarga de todo lo demás."**

```
Lo que escribís en dbt:               Lo que dbt compila y ejecuta en la Base de Datos:
┌─────────────────────────────┐        ┌────────────────────────────────────────────────┐
│ -- models/stg_clientes.sql  │        │ CREATE TABLE analytics.stg_clientes AS (       │
│ SELECT                      │ ────►  │   SELECT id, LOWER(email) AS email             │
│   id,                       │        │   FROM raw.clientes                            │
│   LOWER(email) AS email     │        │ );                                             │
│ FROM {{ source('raw', 'c') }}│        └────────────────────────────────────────────────┘
└─────────────────────────────┘

```

### Problemas Reales que resuelve dbt en Producción:

1. **Elimina el DDL Manual**: Ya no escribís `CREATE TABLE`, `CREATE VIEW` ni sentencias de alteración de tablas. dbt infiere las DDL automáticamente.
2. **Buenas Prácticas de Desarrollo de Software para SQL**: Trae control de versiones con Git, modularidad, entornos aislados (desarrollo, *staging*, producción) y CI/CD al código SQL.
3. **Gestión de Dependencias (DAG Automático)**: Mediante la función `ref('nombre_modelo')`, dbt construye automáticamente el Grafo Acíclico Dirigido (DAG) de dependencias, sabiendo exactamente qué modelos deben ejecutarse primero.
4. **Pruebas de Calidad (** **Data Testing** **) y Documentación**: Permite validar claves primarias, nulos e integridad referencial con un solo comando.

---

## 3\. Las 4 Materializaciones Principales en dbt

En dbt, cada archivo `.sql` dentro de la carpeta `models/` representa una vista o tabla física en la base de datos. La forma en que dbt crea ese objeto se define mediante la **Materialización**:

```
-- Configuración de materialización dentro de un modelo SQL
{{ config(materialized='table') }}

SELECT * FROM {{ ref('stg_ventas') }};

```

| Materialización          | Descripción / Mecanismo Interno                                                                                         | Caso de Uso Recomendado                                                                        |
| ------------------------ | ----------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| **view** *(por defecto)* | Crea una vista SQL (`CREATE VIEW AS ...`). No guarda datos físicamente; ejecuta la consulta al vuelo.                   | Modelos de la capa Silver/Staging livianos o consultas de poco volumen.                        |
| **table**                | Crea una tabla física reescribiéndola por completo (`CREATE TABLE AS ...`).                                             | Capa Gold (Business Marts), modelos multidimensionales y tablas de hechos pequeñas a medianas. |
| **incremental**          | Transforma e **inserta únicamente los registros nuevos o modificados** desde la última ejecución.                       | Tablas de hechos masivas con millones de filas diarias para optimizar costos de cómputo.       |
| **ephemeral**            | No crea nada en la base de datos. Convierte el modelo en una **CTE (** **WITH** **)** reusable dentro de otros modelos. | Transformaciones intermedias o limpiadores secundarios que no requieren auditoría directa.     |

---

## 4\. Estructura de un Proyecto dbt Profesional

Un proyecto de dbt sigue una estructura modular estandarizada:

```
mi_proyecto_dbt/
├── dbt_project.yml        &lt;-- Archivo central de configuración del proyecto
├── profiles.yml           &lt;-- Credenciales de conexión a la DB (fuera de Git por seguridad)
├── models/                &lt;-- Modelos SQL organizados por capas Medallón
│   ├── staging/           &lt;-- Capa Bronze/Silver (Limpieza inicial: stg_*.sql)
│   ├── intermediate/      &lt;-- Transformaciones intermedias y JOINs (int_*.sql)
│   └── marts/             &lt;-- Capa Gold (Fact_ y Dim_ para consumo final)
├── tests/                 &lt;-- Pruebas de calidad SQL personalizadas
└── macros/                &lt;-- Funciones reutilizables escritas en Jinja

```

### Comandos de Gestión Fundamentales:

* **dbt run**: Compila todo el proyecto y crea las tablas/vistas en la base de datos.
* **dbt test**: Ejecuta todas las pruebas de calidad de datos configuradas.
* **dbt compile**: Traduce las plantillas Jinja y referencias `ref()` a SQL puro (dentro de `target/compiled/`).
* **dbt docs generate &amp;&amp; dbt docs serve**: Genera una web interactiva con la documentación y el **linaje gráfico de datos (** **Data Lineage** **)**.

---

## 🏋️‍♂️ Práctica de la Lección 01

1. Ubicate en la carpeta `practica/modulo_05/` de tu repositorio local.
2. Creá el archivo `ej_01_fundamentos_dbt.py`.
3. Escribí un script Python que simule la **compilación de referencias** **ref()** **y la lógica de DAG que realiza dbt Core**:

```
# Simulación del motor de compilación de dbt Core
class DBTMockCompiler:
    def __init__(self):
        self.models = {}

    def register_model(self, name: str, sql_content: str, materialized: str = "view"):
        self.models[name] = {
            "sql": sql_content,
            "materialized": materialized
        }

    def compile_model(self, name: str) -&gt; str:
        model = self.models.get(name)
        if not model:
            raise ValueError(f"Modelo '{name}' no encontrado.")

        raw_sql = model["sql"]
        # Reemplazar la sintaxis {{ ref('otro_modelo') }} por el nombre físico de la tabla
        compiled_sql = raw_sql
        import re
        refs = re.findall(r"\{\{\s*ref\\('([^']+)'\\)\s*\}\}", raw_sql)
        for ref_name in refs:
            compiled_sql = compiled_sql.replace(f"{{{{ ref('{ref_name}') }}}}", f"analytics.{ref_name}")

        # Aplicar el DDL según la materialización
        mat = model["materialized"]
        if mat == "view":
            return f"CREATE VIEW analytics.{name} AS (\n{compiled_sql}\n);"
        elif mat == "table":
            return f"CREATE TABLE analytics.{name} AS (\n{compiled_sql}\n);"
        return compiled_sql

# Ejemplo de uso
dbt = DBTMockCompiler()

# Registrar modelo Staging (Capa Silver)
dbt.register_model(
    name="stg_usuarios",
    sql_content="SELECT id, LOWER(email) AS email FROM raw_usuarios",
    materialized="view"
)

# Registrar modelo Mart (Capa Gold) haciendo referencia a stg_usuarios mediante ref()
dbt.register_model(
    name="fct_usuarios_activos",
    sql_content="SELECT id, email FROM {{ ref('stg_usuarios') }} WHERE email IS NOT NULL",
    materialized="table"
)

print("--- SQL Compilado por dbt para 'stg_usuarios' ---")
print(dbt.compile_model("stg_usuarios"))

print("\n--- SQL Compilado por dbt para 'fct_usuarios_activos' ---")
print(dbt.compile_model("fct_usuarios_activos"))

```

1. Agregá comentarios al final del archivo respondiendo:
  * **Consigna A**: ¿Por qué utilizar la función `ref('stg_usuarios')` en lugar de hardcodear `analytics.stg_usuarios` permite a dbt construir el grafo de linaje (*Lineage DAG*) y controlar el orden de ejecución?
  * **Consigna B**: ¿En qué capa Medallón utilizarías la materialización `incremental` y qué beneficio aporta en términos de consumo de memoria y tiempo de CPU?