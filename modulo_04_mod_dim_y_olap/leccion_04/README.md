# 📊 Lección 04: Arquitectura Medallón (*Medallion Architecture*) — Capas Bronze (Raw), Silver (Cleansed/Enriched) y Gold (Business Marts)

En las lecciones anteriores aprendimos a diseñar **Tablas de Hechos y Dimensiones** (Lección 01), gestionar el historial de cambios con **SCD Types** (Lección 02) y elegir la topología del Data Warehouse entre **Estrella y Copo de Nieve** (Lección 03).

Sin embargo, en los entornos modernos de Ingeniería de Datos (*Data Lakes* y *Data Lakehouses*), intentar transformar los datos crudos que llegan desde aplicaciones o APIs directamente a un modelo dimensional en un solo paso produce código frágil, difícil de depurar y propenso a errores.

Para estructurar un pipeline de transformaciones limpio, auditable y escalable, la industria adoptó el patrón de la **Arquitectura Medallón (** **Medallion Architecture** **)**, popularizado en los entornos de Data Lakehouse (Delta Lake, Databricks, Snowflake, DuckDB).

---

## 1\. El Problema del "Data Swamp" (Pantano de Datos) y la Solución Medallón

Históricamente, los Data Lakes recibían archivos sin ningún tipo de control, convirtiéndose rápidamente en "pantanos de datos" donde nadie sabía si una tabla estaba limpia, si tenía duplicados o si las reglas de negocio estaban aplicadas a medias.

La **Arquitectura Medallón** resuelve esto dividiendo el almacenamiento y las transformaciones en **3 capas de calidad y refinamiento progresivo**:

```
 ┌──────────────────────┐     ┌──────────────────────┐     ┌──────────────────────┐
 │    CAPA BRONZE       │     │     CAPA SILVER      │     │      CAPA GOLD       │
 │   (Raw / Crudo)      │ ──► │  (Clean / Enriched)  │ ──► │   (Business Marts)   │
 ├──────────────────────┤     ├──────────────────────┤     ├──────────────────────┤
 │ • Datos crudos tal  │     │ • Datos limpios     │     │ • Modelo Dimensional │
 │   como vienen        │     │ • Deduplicados       │     │   Kimball (Estrella) │
 │ • Sin filtros        │     │ • Tipos de datos     │     │ • Agregaciones BI    │
 │ • Append-Only        │     │   casteados          │     │ • Consumo de Negocio │
 └──────────────────────┘     └──────────────────────┘     └──────────────────────┘

```

---

## 2\. Las 3 Capas de la Arquitectura Medallón

### 🥉 A. Capa Bronze (Raw / Ingestion Layer)

Es la puerta de entrada del Data Lake/Lakehouse. Recibe los datos crudos extraídos directamente de los sistemas de origen (APIs, archivos JSON, dumps de PostgreSQL, logs de eventos).

* **Regla de Oro**: **Se guarda el dato tal como viene, sin modificar ni filtrar.**
* **Patrón de Carga**: *Append-Only* (solo inserciones acumulativas).
* **Metadatos de Control**: Se agregan columnas de auditoría como `_ingested_at` (fecha/hora de ingesta) y `_source_file` (nombre del archivo origen).
* **¿Por qué existe?**: Permite auditar el estado original de la fuente y **reprocesar todo el historial hacia adelante** si en el futuro cambian las reglas de negocio o se descubre un bug en las transformaciones.

---

### 🥈 B. Capa Silver (Cleansed / Enriched Layer)

Es la capa de limpieza, estandarización y calidad de datos. Toma los datos de la capa Bronze y aplica transformaciones estructurales.

* **Operaciones Principales**:
  * Casteo explícito de tipos de datos (convertir cadenas de texto a `TIMESTAMP`, `DECIMAL` o `BOOLEAN`).
  * Limpieza y normalización de textos (remover espacios sobrantes, pasar a mayúsculas).
  * Tratamiento defensivo de nulos (`COALESCE`) y parsing de objetos anidados (`JSON`).
  * **Deduplicación de registros** (retener la versión más reciente usando `ROW_NUMBER()`).
  * Validación de Contratos de Datos (*Data Contracts*).
* **Uso**: Es la fuente de verdad técnica para los Data Engineers y Data Scientists para explorar datos limpios pero a nivel de transacción individual.

---

### 🥇 C. Capa Gold (Curated / Business Marts Layer)

Es la capa final optimizada para el consumo de la organización, tableros de BI (PowerBI, Tableau) y modelos de Machine Learning.

* **Estructura**: Aplica el **Modelado Dimensional Kimball** que estudiamos en las lecciones 01-03: **Tablas de Hechos (** **fact\_** **) y Dimensiones (** **dim\_** **) en Esquema Estrella**.
* **Operaciones Principales**:
  * Construcción de dimensiones con claves sustitutas (*Surrogate Keys*) y gestión de historial **SCD Type 2**.
  * Creación de métricas de negocio pre-calculadas y agregaciones.
  * Aplicación de reglas de negocio específicas (ej. "Ventas Netas con Impuestos Descontados").

---

## 📊 Matriz Comparativa de las Capas Medallón

| Criterio                          | Capa Bronze (Raw)                     | Capa Silver (Clean)                | Capa Gold (Business)              |
| --------------------------------- | ------------------------------------- | ---------------------------------- | --------------------------------- |
| **Calidad de Datos**              | Cruda / Incierta                      | Alta / Validada                    | **Garantizada / Negocio**         |
| **Estructura**                    | Esquema en origen (JSON, CSV, tablas) | Tablas tabulares estandarizadas    | **Modelado Estrella (Kimball)**   |
| **Deduplicación**                 | No (Contiene duplicados)              | **Sí (Deduplicada)**               | Sí (Atómica o Agregada)           |
| **Público Objetivo**              | Data Engineers                        | Data Engineers, Data Scientists    | **Data Analysts, BI, Ejecutivos** |
| **Frecuencia de Reprocesamiento** | Rara vez (Es el respaldo)             | Frecuente (Ante cambios de lógica) | Constante (Consumo final)         |

---

## 🛠️ Implementación del Pipeline Medallón en SQL

A continuación se muestra cómo fluyen los datos entre las 3 capas dentro de una base analítica (ej. PostgreSQL o DuckDB):

```
-- ============================================================
-- 1. CAPA BRONZE: Tabla Cruda de Ingesta (JSON / Textos)
-- ============================================================
CREATE TABLE bronze_ventas_raw (
    raw_payload JSONB,
    _ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- 2. CAPA SILVER: Limpieza, Parsing JSON, Tipado y Deduplicación
-- ============================================================
CREATE TABLE silver_ventas (
    transaccion_id INT PRIMARY KEY,
    cliente_id INT,
    monto DECIMAL(10,2),
    fecha_transaccion TIMESTAMP,
    estado VARCHAR(20)
);

-- ETL / ELT: De Bronze a Silver
INSERT INTO silver_ventas
WITH parsed_data AS (
    SELECT 
        (raw_payload-&gt;&gt;'id')::INT AS transaccion_id,
        (raw_payload-&gt;&gt;'cliente_id')::INT AS cliente_id,
        (raw_payload-&gt;&gt;'monto')::DECIMAL(10,2) AS monto,
        (raw_payload-&gt;&gt;'fecha')::TIMESTAMP AS fecha_transaccion,
        UPPER(TRIM(raw_payload-&gt;&gt;'estado')) AS estado,
        ROW_NUMBER() OVER (
            PARTITION BY (raw_payload-&gt;&gt;'id')::INT 
            ORDER BY _ingested_at DESC
        ) AS rn
    FROM bronze_ventas_raw
)
SELECT transaccion_id, cliente_id, monto, fecha_transaccion, estado
FROM parsed_data
WHERE rn = 1 AND estado = 'COMPLETADA'; -- Deduplicado y filtrado

-- ============================================================
-- 3. CAPA GOLD: Modelo Dimensional Kimball (Estrella)
-- ============================================================
-- Insertar en la Fact Table (Gold) desde Silver
INSERT INTO fact_ventas (venta_id, cliente_key, fecha_key, monto_total_usd)
SELECT 
    s.transaccion_id,
    c.cliente_key, -- Clave sustituta de dim_cliente
    TO_CHAR(s.fecha_transaccion, 'YYYYMMDD')::INT AS fecha_key,
    s.monto
FROM silver_ventas s
JOIN dim_cliente c ON s.cliente_id = c.cliente_id_origen AND c.es_actual = TRUE;

```

---

## 🏋️‍♂️ Práctica de la Lección 04

1. Ubicate en la carpeta `practica/modulo_04/` de tu repositorio local.
2. Creá el archivo `ej_04_arquitectura_medallon.sql`.
3. Escribí un script SQL (compatible con PostgreSQL o DuckDB) que implemente las 3 capas para un sistema de **Telemetría de Sensores**:
  * **Bronze**: Tabla `bronze_logs` con columnas `log_id` (autoincremental), `payload_str` (cadena de texto desprolija) y `_ingested_at`. Insertá 3 filas sintéticas (incluyendo 1 duplicada).
  * **Silver**: Tabla `silver_telemetria` con columnas limpias (`sensor_id INT`, `temperatura DECIMAL`, `fecha TIMESTAMP`). Escribí la consulta `INSERT INTO ... SELECT` deduplicando y casteando los tipos de datos desde Bronze.
  * **Gold**: Tabla de agregación diaria `gold_resumen_sensores_diario` que calcule `sensor_id`, `fecha`, `temperatura_promedio`, `temperatura_maxima` y `total_lecturas`.
4. Agregá comentarios al final del archivo respondiendo:
  * **Consigna A**: Si la regla de negocio para calcular la `temperatura_promedio` cambia el mes que viene, ¿por qué la Capa Bronze nos permite recalcularla sin perder datos históricos ni depender de la fuente de origen?
  * **Consigna B**: ¿A qué capa Medallón corresponden los modelos que construimos en la Lección 01 (`dim_cliente`, `fact_ventas`)?