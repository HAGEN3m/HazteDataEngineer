🚀 Lección 02: Modelado Modular en dbt (stg_, int_ y marts_) con Jinja y MacrosEn la Lección 01 aprendimos cómo dbt revolucionó el desarrollo analítico al introducir el paradigma ELT in-Warehouse, permitiéndonos transformar datos directamente dentro de la base de datos usando sentencias SELECT y gestionando automáticamente las dependencias con la función ref().En esta lección profundizaremos en la arquitectura modular de modelos (cómo organizar el proyecto dbt en capas stg_, int_ y marts_ alineadas con la Arquitectura Medallón) y aprenderemos a potenciar nuestro SQL utilizando el motor de plantillas Jinja y la creación de Macros reutilizables.1. Organización Modular de Modelos: De Raw a Business MartsPara evitar escribir consultas SQL gigantes de 1,000 líneas que mezclen limpieza, lógica de negocio y agregaciones, dbt promueve la modularidad: dividir las transformaciones en bloques pequeños, testeables y reusables.Un proyecto profesional de dbt organiza sus modelos en 3 capas principales:  [ FUENTES RAW ]           [ CAPA STAGING ]             [ CAPA INTERMEDIATE ]               [ CAPA MARTS ]
┌─────────────────┐       ┌─────────────────┐           ┌───────────────────┐            ┌───────────────────┐
│ source('pos',   │ ────► │ stg_pos__ventas │ ────────┐ │ int_ventas_con_   │ ─────────► │ fct_ventas_diarias│
│        'ventas')│       └─────────────────┘         ├─► clientes          │            └───────────────────┘
└─────────────────┘       ┌─────────────────┐         │ └───────────────────┘            ┌───────────────────┐
│ source('crm',   │ ────► │ stg_crm__cliente│ ────────┘                                  │ dim_clientes      │
│     'clientes') │       └─────────────────┘                                            └───────────────────┘
└─────────────────┘
A. Capa Staging (models/staging/ — prefijo stg_)Propósito: Es la interfaz de entrada a dbt. Existe en relación 1 a 1 con cada tabla fuente de la capa Bronze.Operaciones Permitidas:Renombrar columnas para estandarizar nombres (user_id $\rightarrow$ cliente_id).Castear explícitamente tipos de datos (created_at::timestamp).Limpieza de cadenas (TRIM, LOWER).Cálculos simples a nivel de fila (convertir centavos a dólares).Prohibiciones Estrictas: NO realizar JOINs entre tablas ni agrupaciones GROUP BY en esta capa.Sintaxis: Lee las tablas fuente utilizando la función {{ source('nombre_fuente', 'nombre_tabla') }}.-- models/staging/stg_pos__ventas.sql
WITH source AS (
    SELECT * FROM {{ source('pos_system', 'raw_transactions') }}
),
renamed AS (
    SELECT
        id AS transaccion_id,
        cust_id AS cliente_id,
        (amount / 100.0)::DECIMAL(10,2) AS monto_usd,
        created_at::TIMESTAMP AS fecha_transaccion,
        UPPER(status) AS estado
    FROM source
)
SELECT * FROM renamed;
B. Capa Intermedia (models/intermediate/ — prefijo int_)Propósito: Absorbe la complejidad de la lógica de negocio antes de llegar a los reportes finales. Es la capa de "carpintería" donde se unen múltiples staging models.Operaciones Permitidas:Realizar JOINs entre modelos staging (ref('stg_pos__ventas') con ref('stg_crm__cliente')).Aplicar filtros de negocio complejos (ej. "filtrar solo clientes activos con compras verificadas").Agregaciones intermedias o cálculo de métricas complejas.Materialización Recomendada: ephemeral (para no saturar la base de datos de tablas físicas) o view.-- models/intermediate/int_ventas_enriquecidas.sql
WITH ventas AS (
    SELECT * FROM {{ ref('stg_pos__ventas') }}
),
clientes AS (
    SELECT * FROM {{ ref('stg_crm__clientes') }}
)
SELECT
    v.transaccion_id,
    v.monto_usd,
    v.fecha_transaccion,
    c.cliente_id,
    c.pais_residencia,
    c.categoria_fidelidad
FROM ventas v
LEFT JOIN clientes c ON v.cliente_id = c.cliente_id
WHERE v.estado = 'COMPLETADA';
C. Capa Marts (models/marts/ — prefijos fct_ y dim_)Propósito: Capa Gold final. Expone el Modelo Dimensional Kimball (Esquema Estrella) consumible directamente por los analistas y tableros de BI.Estructura:fct_: Tablas de hechos con métricas numéricas acumulables (fct_ventas.sql).dim_: Tablas de dimensiones descriptivas desnormalizadas (dim_clientes.sql).Materialización Recomendada: table o incremental.2. Potenciando SQL con Jinja en dbtSQL por sí solo es un lenguaje estático. Jinja es un motor de plantillas que permite inyectar programación orientada a objetos dentro de nuestros archivos .sql:{{ ... }} (Expresiones): Imprimen valores o ejecutan funciones (ej. {{ ref('stg_ventas') }}).{% ... %} (Sentencias de Control): Ejecutan bucles for, condicionales if/else y declaración de variables.{# ... #} (Comentarios): Comentarios internos que dbt omite al compilar a SQL puro.Ejemplo: Evitar Código Repetitivo con un Bucle FOR en JinjaSupongamos que necesitamos calcular el total vendido para 4 métodos de pago distintos en una tabla dinámica (pivot):-- Sin Jinja: SQL Repetitivo y Frágil
SELECT
    cliente_id,
    SUM(CASE WHEN metodo_pago = 'tarjeta_credito' THEN monto ELSE 0 END) AS pago_tarjeta_credito,
    SUM(CASE WHEN metodo_pago = 'efectivo' THEN monto ELSE 0 END) AS pago_efectivo,
    SUM(CASE WHEN metodo_pago = 'transferencia' THEN monto ELSE 0 END) AS pago_transferencia,
    SUM(CASE WHEN metodo_pago = 'mercado_pago' THEN monto ELSE 0 END) AS pago_mercado_pago
FROM {{ ref('stg_ventas') }}
GROUP BY cliente_id;

-- 🟢 Con Jinja: Dinámico, Elegante y Mantenible
{% set metodos_pago = ['tarjeta_credito', 'efectivo', 'transferencia', 'mercado_pago'] %}

SELECT
    cliente_id,
    {% for metodo in metodos_pago %}
        SUM(CASE WHEN metodo_pago = '{{ metodo }}' THEN monto ELSE 0 END) AS pago_{{ metodo }}
        {% if not loop.last %},{% endif %}
    {% endfor %}
FROM {{ ref('stg_ventas') }}
GROUP BY cliente_id;
3. Reusabilidad Avanzada: Macros en dbtUna Macro en dbt es el equivalente a una función reutilizable en Python, pero escrita en Jinja/SQL dentro de la carpeta macros/. Permite empaquetar lógicas repetitivas y ejecutarlas en cualquier modelo del proyecto.Ejemplo de Macro: Prevención de División por CeroEn la Lección 11 del Módulo 02 aprendimos a combinar COALESCE y NULLIF para evitar colapsos por división por cero. Creemos una Macro para automatizar esto en todo el proyecto dbt:-- macros/calcular_ratio_defensivo.sql
{% macro calcular_ratio_defensivo(numerador, denominador, decimales=2) %}
    ROUND(
        COALESCE(
            {{ numerador }}::DECIMAL / NULLIF({{ denominador }}, 0), 
            0.0
        ), 
        {{ decimales }}
    )
{% endmacro %}
Uso de la Macro dentro de un Modelo:-- models/marts/fct_rendimiento_vendedores.sql
SELECT
    vendedor_id,
    monto_total_ventas,
    cantidad_ordenes,
    -- Invocación limpia de la Macro
    {{ calcular_ratio_defensivo('monto_total_ventas', 'cantidad_ordenes', decimales=2) }} AS ticket_promedio
FROM {{ ref('int_ventas_por_vendedor') }};
🏋️‍♂️ Práctica de la Lección 02Ubicate en la carpeta practica/modulo_05/ de tu repositorio local.Creá el archivo ej_02_modelado_modular_dbt.py.Escribí un script Python que simule el procesamiento Jinja de bucles y la expansión de Macros de dbt:# Simulación del motor Jinja / Macros de dbt Core
def macro_calcular_ratio(numerador: str, denominador: str) -> str:
    return f"ROUND(COALESCE({numerador}::DECIMAL / NULLIF({denominador}, 0), 0.0), 2)"

def render_jinja_pivot_model(model_name: str, ref_source: str, categorias: list) -> str:
    pivot_cols = []
    for cat in categorias:
        col_sql = f"  SUM(CASE WHEN categoria = '{cat}' THEN monto ELSE 0 END) AS total_{cat.lower()}"
        pivot_cols.append(col_sql)

    pivot_str = ",\n".join(pivot_cols)
    ratio_str = macro_calcular_ratio("SUM(monto)", "COUNT(transaccion_id)")

    sql = f"""-- Modelo Compilado: {model_name}
SELECT
    cliente_id,
{pivot_str},
    {ratio_str} AS ticket_promedio
FROM analytics.{ref_source}
GROUP BY cliente_id;"""
    return sql

# Ejecución de prueba
categorias_productos = ["ELECTRONICA", "HOGAR", "ROPA", "DEPORTES"]
sql_result = render_jinja_pivot_model(
    model_name="fct_ventas_por_categoria",
    ref_source="stg_ventas",
    categorias=categorias_productos
)

print(sql_result)
Agregá comentarios al final del archivo respondiendo:Consigna A: ¿Por qué la regla de arquitectura en dbt prohíbe realizar JOINs dentro de los modelos de la capa staging/ (stg_)?Consigna B: Si un cliente requiere agregar una quinta categoría ("JUGUETERIA"), ¿cuál es la ventaja de haber usado un bucle Jinja en lugar de tener las columnas hardcodeadas en SQL?