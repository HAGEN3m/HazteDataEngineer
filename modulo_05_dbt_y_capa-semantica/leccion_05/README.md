# 🚀 Lección 05: Cierre del Módulo 05 — Proyecto Integrador con dbt y DuckDB/PostgreSQL

¡Llegamos al hito final del **Módulo 05: dbt (data build tool) y Capa Semántica**!

A lo largo de este módulo dominamos los estándares de la Ingeniería de Analítica (*Analytics Engineering*):

* **Lección 01**: Fundamentos de dbt Core y el paradigma **ELT in-Warehouse**, comprendiendo las materializaciones (`view`, `table`, `incremental`, `ephemeral`).
* **Lección 02**: Arquitectura modular de modelos (`stg_`, `int_` y `marts_`) potencian do SQL con **Jinja y Macros** reutilizables.
* **Lección 03**: Calidad de datos con **Pruebas Genéricas y Singulares**, documentación automática y control de selección mediante el **Grafo de Linaje (** **Data Lineage** **)**.
* **Lección 04**: Centralización de métricas de negocio con la **Capa Semántica (** **dbt MetricFlow** **)**.

En esta lección integramos todos estos conceptos en un **Proyecto Integrador Capstone**, construyendo un pipeline end-to-end listo para producción sobre **DuckDB** o **PostgreSQL**.

---

## 1\. Escenario del Proyecto Integrador

Imaginemos que nos asignan estructurar el pipeline de analítica para una plataforma SaaS. La base de datos contiene tablas crudas en el esquema `raw`.

Nuestra misión es construir el proyecto dbt completo que:

1. Defina las fuentes de entrada (`sources.yml`).
2. Limpie y estandarice las fuentes en la capa **Staging** (`stg_`).
3. Combine y enriquezca la lógica de negocio en la capa **Intermedia** (`int_`).
4. Modele las tablas finales en la capa **Marts** (`fct_` y `dim_`).
5. Aplique pruebas de calidad genéricas y una prueba singular de validación.
6. Exponga la métrica de **"Ingresos Totales"** y **"Ticket Promedio"** mediante la **Capa Semántica**.

---

## 2\. Arquitectura de Archivos del Proyecto dbt

```
proyecto_dbt_saas/
├── dbt_project.yml
├── models/
│   ├── staging/
│   │   ├── _sources.yml
│   │   ├── stg_raw__clientes.sql
│   │   └── stg_raw__ventas.sql
│   ├── intermediate/
│   │   └── int_ventas_enriquecidas.sql
│   ├── marts/
│   │   ├── _marts_models.yml
│   │   ├── dim_clientes.sql
│   │   └── fct_ventas.sql
│   └── semantic/
│       ├── _semantic_models.yml
│       └── _metrics.yml
└── tests/
    └── assert_monto_venta_positivo.sql

```

---

## 🟢 3\. Código Completo del Proyecto

### A. Capa Staging y Fuentes (`models/staging/`)

```
# models/staging/_sources.yml
version: 2

sources:
  - name: saas_raw
    schema: raw
    tables:
      - name: raw_customers
      - name: raw_orders

```

```
-- models/staging/stg_raw__clientes.sql
WITH source AS (
    SELECT * FROM {{ source('saas_raw', 'raw_customers') }}
),
renamed AS (
    SELECT
        id AS cliente_id,
        LOWER(TRIM(email)) AS email,
        UPPER(country) AS pais,
        created_at::TIMESTAMP AS fecha_registro
    FROM source
)
SELECT * FROM renamed;

```

```
-- models/staging/stg_raw__ventas.sql
WITH source AS (
    SELECT * FROM {{ source('saas_raw', 'raw_orders') }}
),
renamed AS (
    SELECT
        order_id AS venta_id,
        customer_id AS cliente_id,
        (amount_cents / 100.0)::DECIMAL(10,2) AS monto_usd,
        UPPER(status) AS estado,
        order_date::TIMESTAMP AS fecha_venta
    FROM source
)
SELECT * FROM renamed;

```

---

### B. Capa Intermedia y Marts (`models/intermediate/` y `models/marts/`)

```
-- models/intermediate/int_ventas_enriquecidas.sql
{{ config(materialized='ephemeral') }}

WITH ventas AS (
    SELECT * FROM {{ ref('stg_raw__ventas') }}
),
clientes AS (
    SELECT * FROM {{ ref('stg_raw__clientes') }}
)
SELECT
    v.venta_id,
    v.cliente_id,
    c.pais AS pais_cliente,
    v.monto_usd,
    v.fecha_venta
FROM ventas v
INNER JOIN clientes c ON v.cliente_id = c.cliente_id
WHERE v.estado = 'COMPLETADA';

```

```
-- models/marts/fct_ventas.sql
{{ config(materialized='table') }}

SELECT
    venta_id,
    cliente_id,
    pais_cliente,
    monto_usd,
    fecha_venta
FROM {{ ref('int_ventas_enriquecidas') }};

```

---

### C. Testing y Calidad de Datos (`schema.yml` y `tests/`)

```
# models/marts/_marts_models.yml
version: 2

models:
  - name: fct_ventas
    description: "Tabla de hechos de ventas completadas para consumo analítico."
    columns:
      - name: venta_id
        tests:
          - unique
          - not_null
      - name: cliente_id
        tests:
          - not_null
          - relationships:
              to: ref('stg_raw__clientes')
              field: cliente_id

```

```
-- tests/assert_monto_venta_positivo.sql
-- Test Singular: Retorna filas erróneas (Monto &lt;= 0)
SELECT
    venta_id,
    monto_usd
FROM {{ ref('fct_ventas') }}
WHERE monto_usd &lt;= 0;

```

---

### D. Capa Semántica (`models/semantic/`)

```
# models/semantic/_semantic_models.yml
version: 2

semantic_models:
  - name: sm_fct_ventas
    model: ref('fct_ventas')
    defaults:
      agg_time_dimension: fecha_venta

    entities:
      - name: venta_id
        type: primary
      - name: cliente_id
        type: foreign

    measures:
      - name: ingresos_totales_usd
        expr: monto_usd
        agg: sum
      - name: conteo_ventas
        expr: venta_id
        agg: count_distinct

    dimensions:
      - name: fecha_venta
        type: time
        type_params:
          time_granularity: day
      - name: pais_cliente
        type: categorical

```

```
# models/semantic/_metrics.yml
version: 2

metrics:
  - name: ingresos_totales
    label: "Ingresos Totales (USD)"
    type: simple
    type_params:
      measure: ingresos_totales_usd

  - name: ticket_promedio
    label: "Ticket Promedio por Venta"
    type: ratio
    type_params:
      numerator: ingresos_totales_usd
      denominator: conteo_ventas

```

---

## 🏋️‍♂️ Práctica del Proyecto Integrador (Lección 05)

1. Ubicate en la carpeta `practica/modulo_05/` de tu repositorio local.
2. Creá el archivo `ej_05_proyecto_integrador_dbt.py`.
3. Escribí un script Python que simule la **ejecución completa del pipeline dbt (compilación, ejecución de DDL, testing y resolución semántica)**:

```
import pandas as pd

# 1. Base de Datos Mock (Capa Bronze)
raw_customers = pd.DataFrame([
    {"id": "C1", "email": "ANA@EMAIL.COM ", "country": "argentina", "created_at": "2025-01-01"},
    {"id": "C2", "email": "luis@email.com", "country": "chile", "created_at": "2025-01-02"}
])

raw_orders = pd.DataFrame([
    {"order_id": 1001, "customer_id": "C1", "amount_cents": 15000, "status": "completada", "order_date": "2026-02-01"},
    {"order_id": 1002, "customer_id": "C2", "amount_cents": 5000, "status": "completada", "order_date": "2026-02-02"},
    {"order_id": 1003, "customer_id": "C1", "amount_cents": -100, "status": "completada", "order_date": "2026-02-03"} # Anómala para test
])

# 2. Simulación de Transformación dbt (Staging -&gt; Int -&gt; Marts)
def run_dbt_pipeline():
    print("--- 1. EJECUTANDO STAGING ---")
    stg_customers = raw_customers.rename(columns={"id": "cliente_id"}).copy()
    stg_customers["email"] = stg_customers["email"].str.strip().str.lower()
    stg_customers["pais"] = stg_customers["country"].str.upper()

    stg_orders = raw_orders.rename(columns={"order_id": "venta_id", "customer_id": "cliente_id"}).copy()
    stg_orders["monto_usd"] = stg_orders["amount_cents"] / 100.0
    stg_orders["estado"] = stg_orders["status"].str.upper()

    print("--- 2. EJECUTANDO MARTS (fct_ventas) ---")
    fct_ventas = stg_orders[stg_orders["estado"] == "COMPLETADA"].merge(
        stg_customers[["cliente_id", "pais"]], on="cliente_id", how="inner"
    )

    print("--- 3. EJECUTANDO DBT TESTS ---")
    # Test Singular: assert_monto_venta_positivo
    anomalous = fct_ventas[fct_ventas["monto_usd"] &lt;= 0]
    if len(anomalous) &gt; 0:
        print(f"❌ TEST SINGULAR FAILED: {len(anomalous)} ventas con monto &lt;= 0 detectadas.")
    else:
        print("✅ ALL DBT TESTS PASSED.")

    print("\n--- 4. MÉTRICA SEMÁNTICA: Ticket Promedio por País ---")
    metrics = fct_ventas.groupby("pais").agg(
        ingresos_totales=("monto_usd", "sum"),
        conteo_ventas=("venta_id", "count")
    )
    metrics["ticket_promedio"] = (metrics["ingresos_totales"] / metrics["conteo_ventas"]).round(2)
    print(metrics[["ingresos_totales", "ticket_promedio"]])

run_dbt_pipeline()

```

1. Agregá comentarios al final del archivo respondiendo:
  * **Consigna A**: ¿Qué comando de la CLI de dbt deberías ejecutar en tu terminal para correr únicamente los tests de calidad declarados sobre la tabla `fct_ventas`?
  * **Consigna B**: Explica la diferencia entre ejecutar `dbt run` vs `dbt build`.