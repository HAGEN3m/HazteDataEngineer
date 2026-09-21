# 📊 Lección 05: Cierre del Módulo 04 — Proyecto Integrador de Modelado OLAP (Diseño y Construcción End-to-End de un Data Mart Analítico)

¡Llegamos al hito final del **Módulo 04: Modelado Dimensional y Arquitectura OLAP**!

A lo largo de este módulo hemos cubierto los pilares de la arquitectura analítica moderna:

* **Lección 01**: Fundamentos de OLTP vs. OLAP y la Metodología Kimball en 4 pasos (Proceso de Negocio, Grano, Dimensiones y Hechos).
* **Lección 02**: Dimensiones de Cambio Lento (**SCD Type 1, Type 2 y Type 3**) y el uso obligatorio de Claves Sustitutas (*Surrogate Keys*) para preservar la verdad histórica.
* **Lección 03**: Topología del Data Warehouse: **Esquema Estrella (** **Star Schema** **) vs. Copo de Nieve (** **Snowflake Schema** **)** y por qué priorizar la desnormalización para maximizar el rendimiento de lectura.
* **Lección 04**: **Arquitectura Medallón (** **Medallion Architecture** **)**: El flujo de refinar datos desde **Bronze (Raw)** a **Silver (Clean)** y **Gold (Business Marts)**.

En esta lección integradora combinaremos todas estas herramientas construyendo un **Data Mart Analítico completo End-to-End** que toma datos crudos JSON en la capa Bronze, los limpia en la capa Silver y los modela en un Esquema Estrella con historial SCD2 en la capa Gold.

---

## 1\. Escenario de Negocio: Data Mart de E-Commerce &amp; Logística

Imaginemos que nos asignan diseñar la arquitectura analítica para una plataforma de e-commerce que recibe transacciones en formato JSON. El área de Business Intelligence necesita responder:

1. **Evolución Histórica de Ventas**: Ingresos acumulados por día, mes y trimestre.
2. **Análisis por Residencia de Cliente**: Medir las ventas según el país en el que vivía el cliente al momento de la compra (preservando el historial cuando se mude mediante **SCD Type 2**).
3. **Rendimiento por Categoría de Producto**: Identificar las categorías más vendidas navegando por dimensiones desnormalizadas.

---

## 2\. Diagrama de la Arquitectura del Pipeline

```
  [ CAPA BRONZE ]                   [ CAPA SILVER ]                           [ CAPA GOLD ]
┌──────────────────┐            ┌──────────────────────┐               ┌────────────────────────┐
│ bronze_ventas_raw│            │ silver_ventas_clean  │               │ dim_cliente_scd2 (SCD2)│
├──────────────────┤            ├──────────────────────┤               ├────────────────────────┤
│ raw_payload (JSON) ─────────► │ transaccion_id       │ ────────────► │ dim_producto (Estrella)│
│ _ingested_at     │  Parsing   │ cliente_id           │ Modelado      ├────────────────────────┤
└──────────────────┘  Deduplic. │ producto_id          │ Kimball       │ dim_fecha              │
                      Casting   │ monto, fecha, estado │               ├────────────────────────┤
                                └──────────────────────┘               │ fact_ventas (Hechos)   │
                                                                       └────────────────────────┘

```

---

## 🟢 3\. Script SQL Completo del Proyecto Integrador

```
-- ============================================================================
-- PASO 1: CAPA BRONZE (Raw / Ingesta Cruda)
-- ============================================================================
CREATE TABLE bronze_ventas_raw (
    raw_payload JSONB,
    _ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Simulación de ingesta de eventos JSON (con duplicados por reintento de API)
INSERT INTO bronze_ventas_raw (raw_payload) VALUES
('{"id": 5001, "cliente_id": "C-10", "cliente_nombre": "Carlos Perez", "cliente_pais": "Argentina", "producto_id": "P-100", "producto_nombre": "Laptop Pro", "categoria": "Computacion", "monto": 1200.00, "fecha": "2025-06-10 14:30:00", "estado": "COMPLETADA"}'),
('{"id": 5001, "cliente_id": "C-10", "cliente_nombre": "Carlos Perez", "cliente_pais": "Argentina", "producto_id": "P-100", "producto_nombre": "Laptop Pro", "categoria": "Computacion", "monto": 1200.00, "fecha": "2025-06-10 14:30:00", "estado": "COMPLETADA"}'), -- Duplicado
('{"id": 5002, "cliente_id": "C-20", "cliente_nombre": "Ana Gomez", "cliente_pais": "Chile", "producto_id": "P-200", "producto_nombre": "Mouse Inalambrico", "categoria": "Accesorios", "monto": 45.00, "fecha": "2026-02-15 09:15:00", "estado": "COMPLETADA"}');

-- ============================================================================
-- PASO 2: CAPA SILVER (Limpieza, Parsing, Deduplicación y Tipado)
-- ============================================================================
CREATE TABLE silver_ventas_clean (
    transaccion_id INT PRIMARY KEY,
    cliente_id VARCHAR(20) NOT NULL,
    cliente_nombre VARCHAR(100) NOT NULL,
    cliente_pais VARCHAR(50) NOT NULL,
    producto_id VARCHAR(20) NOT NULL,
    producto_nombre VARCHAR(100) NOT NULL,
    categoria VARCHAR(50) NOT NULL,
    monto DECIMAL(10,2) NOT NULL,
    fecha_transaccion TIMESTAMP NOT NULL,
    estado VARCHAR(20) NOT NULL
);

-- Ingesta defensiva de Bronze a Silver con ROW_NUMBER()
INSERT INTO silver_ventas_clean
WITH parsed_data AS (
    SELECT 
        (raw_payload-&gt;&gt;'id')::INT AS transaccion_id,
        raw_payload-&gt;&gt;'cliente_id' AS cliente_id,
        raw_payload-&gt;&gt;'cliente_nombre' AS cliente_nombre,
        raw_payload-&gt;&gt;'cliente_pais' AS cliente_pais,
        raw_payload-&gt;&gt;'producto_id' AS producto_id,
        raw_payload-&gt;&gt;'producto_nombre' AS producto_nombre,
        raw_payload-&gt;&gt;'categoria' AS categoria,
        (raw_payload-&gt;&gt;'monto')::DECIMAL(10,2) AS monto,
        (raw_payload-&gt;&gt;'fecha')::TIMESTAMP AS fecha_transaccion,
        UPPER(TRIM(raw_payload-&gt;&gt;'estado')) AS estado,
        ROW_NUMBER() OVER (
            PARTITION BY (raw_payload-&gt;&gt;'id')::INT 
            ORDER BY _ingested_at DESC
        ) AS rn
    FROM bronze_ventas_raw
)
SELECT transaccion_id, cliente_id, cliente_nombre, cliente_pais, producto_id, producto_nombre, categoria, monto, fecha_transaccion, estado
FROM parsed_data
WHERE rn = 1 AND estado = 'COMPLETADA';

-- ============================================================================
-- PASO 3: CAPA GOLD (Modelo Dimensional Kimball - Esquema Estrella)
-- ============================================================================

-- 3.1 Dimensión Fecha
CREATE TABLE dim_fecha (
    fecha_key INT PRIMARY KEY, -- YYYYMMDD
    fecha_completa DATE NOT NULL,
    anio INT NOT NULL,
    mes INT NOT NULL,
    trimestre INT NOT NULL
);

INSERT INTO dim_fecha VALUES 
(20250610, '2025-06-10', 2025, 6, 2),
(20260215, '2026-02-15', 2026, 2, 1);

-- 3.2 Dimensión Cliente con SCD Type 2
CREATE TABLE dim_cliente_scd2 (
    cliente_key SERIAL PRIMARY KEY, -- Surrogate Key
    cliente_id_origen VARCHAR(20) NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    pais VARCHAR(50) NOT NULL,
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE,
    es_actual BOOLEAN NOT NULL DEFAULT TRUE
);

-- Ingesta Inicial en Dimensión Cliente
INSERT INTO dim_cliente_scd2 (cliente_id_origen, nombre, pais, fecha_inicio, fecha_fin, es_actual)
VALUES 
('C-10', 'Carlos Perez', 'Argentina', '2025-01-01', NULL, TRUE),
('C-20', 'Ana Gomez', 'Chile', '2025-01-01', NULL, TRUE);

-- 3.3 Dimensión Producto (Desnormalizada - Estrella)
CREATE TABLE dim_producto (
    producto_key SERIAL PRIMARY KEY,
    producto_id_origen VARCHAR(20) NOT NULL,
    nombre_producto VARCHAR(100) NOT NULL,
    categoria VARCHAR(50) NOT NULL
);

INSERT INTO dim_producto (producto_id_origen, nombre_producto, categoria)
VALUES 
('P-100', 'Laptop Pro', 'Computacion'),
('P-200', 'Mouse Inalambrico', 'Accesorios');

-- 3.4 Tabla de Hechos (fact_ventas)
-- Grano: Una fila por transacción individual completada
CREATE TABLE fact_ventas (
    fact_venta_id INT PRIMARY KEY,
    fecha_key INT NOT NULL REFERENCES dim_fecha(fecha_key),
    cliente_key INT NOT NULL REFERENCES dim_cliente_scd2(cliente_key),
    producto_key INT NOT NULL REFERENCES dim_producto(producto_key),
    monto_total_usd DECIMAL(10,2) NOT NULL
);

-- Carga final de la Tabla de Hechos cruzando contra la versión VIGENTE de las dimensiones
INSERT INTO fact_ventas (fact_venta_id, fecha_key, cliente_key, producto_key, monto_total_usd)
SELECT 
    s.transaccion_id,
    TO_CHAR(s.fecha_transaccion, 'YYYYMMDD')::INT AS fecha_key,
    c.cliente_key,
    p.producto_key,
    s.monto
FROM silver_ventas_clean s
JOIN dim_cliente_scd2 c ON s.cliente_id = c.cliente_id_origen AND c.es_actual = TRUE
JOIN dim_producto p ON s.producto_id = p.producto_id_origen;

```

---

## 4\. Validación de Negocio (Consulta OLAP en Capa Gold)

Para verificar el correcto funcionamiento del modelo en estrella desnormalizado, ejecutamos una consulta agregada que cruza la tabla de hechos con sus dimensiones:

```
SELECT 
    f.anio,
    c.pais AS pais_cliente,
    p.categoria,
    COUNT(v.fact_venta_id) AS total_transacciones,
    SUM(v.monto_total_usd) AS ingresos_totales
FROM fact_ventas v
JOIN dim_fecha f ON v.fecha_key = f.fecha_key
JOIN dim_cliente_scd2 c ON v.cliente_key = c.cliente_key
JOIN dim_producto p ON v.producto_key = p.producto_key
GROUP BY f.anio, c.pais, p.categoria
ORDER BY ingresos_totales DESC;

```

---

## 🏋️‍♂️ Práctica del Proyecto Integrador (Lección 05)

1. Ubicate en la carpeta `practica/modulo_04/` de tu repositorio local.
2. Creá el archivo `ej_05_proyecto_integrador_olap.sql`.
3. Copiá y ejecutá el script SQL completo de esta lección en tu base de datos de práctica (PostgreSQL o DuckDB).
4. Agregá al final del archivo el código SQL necesario para resolver el siguiente escenario de prueba:
  * **Consigna A**: El cliente `'C-10'` (Carlos Perez) se mudó de Argentina a España el día `'2026-03-01'`. Escribí las sentencias SQL que aplican la actualización **SCD Type 2** en `dim_cliente_scd2` (cerrando la versión de Argentina e insertando la nueva versión vigente para España).
  * **Consigna B**: Insertá una nueva transacción en la capa Silver para el cliente `'C-10'` realizada el `'2026-03-15'` e insertala en `fact_ventas`.
  * **Consigna C**: Volvé a ejecutar la consulta de validación OLAP y confirmá que la compra de 2025 se atribuye a Argentina y la nueva compra de marzo de 2026 se atribuye a España.