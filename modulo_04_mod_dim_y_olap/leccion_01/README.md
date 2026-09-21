# 📊 Lección 01: Fundamentos de OLTP vs. OLAP y Metodología Kimball (Tablas de Hechos y Dimensiones)

En los módulos anteriores aprendiste a procesar datos con Python/Polars (Módulo 01), optimizar motores relacionales a bajo nivel (Módulo 02) y empaquetar entornos aislados con Docker (Módulo 03).

Ahora damos un salto de madurez fundamental: **¿Cómo debemos estructurar las bases de datos analíticas (Data Warehouses / Data Lakes) para que el negocio pueda responder preguntas de manera ultra rápida, intuitiva y escalable?**

---

## 1\. El Conflicto de Arquitectura: OLTP vs. OLAP

En Ingeniería de Datos dividimos los sistemas de almacenamiento en dos grandes familias con objetivos opuestos:

```
SISTEMAS OPERACIONALES (OLTP)              DATA WAREHOUSE / ANALÍTICA (OLAP)
┌───────────────────────────────┐          ┌───────────────────────────────┐
│  Base de Datos Transaccional  │          │   Base de Datos Analítica     │
│    (PostgreSQL, MySQL)        │          │ (ClickHouse, Snowflake, DuckDB)│
├───────────────────────────────┤  ETL/ELT ├───────────────────────────────┤
│ • Altísima frecuencia de      │ ───────► │ • Lecturas masivas (SELECTs)  │
│   INSERT / UPDATE / DELETE    │          │ • Millones/Miles de millones  │
│ • Consultas por ID (1 fila)   │          │   de filas agregadas          │
│ • Alta Normalización (3NF)    │          │ • Desnormalización Intencional│
└───────────────────────────────┘          └───────────────────────────────┘

```

### A. OLTP (*Online Transactional Processing*)

* **Propósito**: Dar soporte a las operaciones diarias del producto (el carrito de compras de una app, la creación de usuarios, transferencias bancarias).
* **Estructura**: **Tercera Forma Normal (3NF)**. Minimiza la redundancia dividiendo los datos en decenas de tablas pequeñas relacionadas por claves.
* **Patrón de Carga**: Miles de transacciones individuales por segundo (`INSERT`, `UPDATE`, `DELETE`).
* **¿Por qué falla para Analítica?**: Para calcular las "Ventas Totales por País del Último Año", una base OLTP debe hacer un `JOIN` de 15 tablas altamente normalizadas, consumiendo toda la memoria del servidor operante y bloqueando la app de los clientes.

### B. OLAP (*Online Analytical Processing*)

* **Propósito**: Responder preguntas de negocio, generar tableros BI, análisis de cohortes y reportes ejecutivos.
* **Estructura**: **Modelado Dimensional (Desnormalizado)**. Reduce la cantidad de `JOINs` juntando atributos descriptivos en tablas anchas.
* **Patrón de Carga**: Cargas masivas por lotes (*Batch Bulk Inserts*) o *Streaming*. Lecturas de millones de filas mediante consultas `SELECT`.

---

## 📊 Matriz Comparativa: OLTP vs. OLAP

| Criterio                | OLTP (Operacional)                       | OLAP (Analítico)                                   |
| ----------------------- | ---------------------------------------- | -------------------------------------------------- |
| **Audiencia**           | Aplicaciones, APIs, Usuarios finales     | Data Analysts, Analytics Engineers, Ejecutivos     |
| **Operación Principal** | Lectura/Escritura rápida de 1 fila       | Lectura masiva de columnas sobre millones de filas |
| **Diseño de Tablas**    | Normalizado (3NF) para evitar duplicados | **Dimensional (Estrella / Copo de Nieve)**         |
| **Volumen de Datos**    | Gigabytes                                | Terabytes a Petabytes                              |
| **Tolerancia a Fallos** | Transacciones ACID estrictas             | Re-procesamiento de datos (*Idempotencia*)         |

---

## 2\. La Metodología Kimball: Los 4 Pasos del Diseño Dimensional

Creada por **Ralph Kimball**, es el estándar de la industria para construir Data Warehouses comprensibles y de alto rendimiento mediante un enfoque *Bottom-Up* (de abajo hacia arriba).

Para diseñar cualquier Data Mart o tabla analítica, Kimball define un proceso estricto de **4 Pasos**:

```
┌────────────────────────────────────────────────────────┐
│ 1. Seleccionar el Proceso de Negocio (Business Process)│
├────────────────────────────────────────────────────────┤
│ 2. Declarar el Grano de los Datos (Declare the Grain) │
├────────────────────────────────────────────────────────┤
│ 3. Identificar las Dimensiones (Identify Dimensions)  │
├────────────────────────────────────────────────────────┤
│ 4. Identificar los Hechos (Identify Facts)            │
└────────────────────────────────────────────────────────┘

```

### Paso 1: Seleccionar el Proceso de Negocio

Identificar el evento operacional que genera datos en la organización (ej. *Emisión de Facturas*, *Envíos de Logística*, *Logins de Usuarios*, *Suscripciones Mensuales*).

### Paso 2: Declarar el Grano (*Declare the Grain*) — ¡La decisión más crítica!

El **Grano** define **qué representa exactamente una sola fila** dentro de la tabla de hechos.

* ❌ *Grano Vago*: "Ventas resumidas por día".
* 🟢 *Grano Atómico Atómico (Recomendado)*: "Una fila por cada ítem individual escaneado en el ticket de compra de la caja registradora".
* **Regla Ssr**: **Siempre modelá al nivel de grano más atómico disponible.** Si agrupás datos prematuramente, perdés la capacidad de hacer análisis detallados en el futuro.

### Paso 3: Identificar las Dimensiones (*Who, What, Where, When, Why*)

Son los **contextos cualitativos** que rodean al evento. Responden a las preguntas: ¿Quién compró?, ¿Qué producto?, ¿En qué sucursal?, ¿En qué fecha?, ¿Con qué medio de pago?

### Paso 4: Identificar los Hechos (*Numeric Metrics*)

Son las **medidas cuantitativas numéricas** resultantes del evento (ej. `monto_total`, `cantidad_unidades`, `descuento_aplicado`, `duración_segundos`).

---

## 3\. Anatomía de las Tablas: Fact Tables vs. Dimension Tables

```
                    TABLA DE HECHOS (Fact Table)
                  ┌──────────────────────────────┐
                  │ fact_ventas                  │
                  ├──────────────────────────────┤
                  │ cliente_key (FK)  ─────────┐ │
                  │ producto_key (FK) ──────┐  │ │
                  │ fecha_key (FK)    ────┐ │  │ │
                  │ cantidad_unidades     │ │  │ │
                  │ monto_total_usd       │ │  │ │
                  └───────────────────────┼─┼──┼─┘
                                          │ │  │
   ┌──────────────────────────────────────┘ │  └──────────────────────────────┐
   ▼                                        ▼                                 ▼
TABLA DE DIMENSIÓN                       TABLA DE DIMENSIÓN               TABLA DE DIMENSIÓN
┌────────────────────────┐               ┌────────────────────────┐       ┌────────────────────────┐
│ dim_fecha              │               │ dim_producto           │       │ dim_cliente            │
├────────────────────────┤               ├────────────────────────┤       ├────────────────────────┤
│ fecha_key (PK)         │               │ producto_key (PK)      │       │ cliente_key (PK)       │
│ fecha_actual           │               │ nombre_producto        │       │ nombre_completo        │
│ anio                   │               │ categoria              │       │ email                  │
│ trimestre              │               │ marca                  │       │ pais                   │
└────────────────────────┘               └────────────────────────┘       └────────────────────────┘

```

### A. Tablas de Dimensiones (`dim_`)

* Contienen atributos de texto/categorías desnormalizados para filtrar (`WHERE`) y agrupar (`GROUP BY`).
* Tienen pocas filas en comparación con los hechos, pero son "anchas" (muchas columnas).
* Usan una **Clave Sustituta (** **Surrogate Key** **)**: Un entero autoincremental (`INT` o `BIGINT`) propio del Data Warehouse que reemplaza a la clave primaria del sistema origen.

### B. Tablas de Hechos (`fact_`)

* Contienen las métricas numéricas acumulables y las Claves Foráneas (*Foreign Keys*) que apuntan a las dimensiones.
* Tienen millones o miles de millones de filas, pero son "angostas" (pocas columnas).

#### Tipos de Métricas en la Tabla de Hechos:

1. **Aditivas**: Se pueden sumar a través de cualquier dimensión (ej. `monto_total` se puede sumar por fecha, cliente o país).
2. **Semi-aditivas**: Se pueden sumar solo a través de algunas dimensiones (ej. `saldo_de_cuenta_bancaria`: podés sumarlo por cliente, pero NO podés sumar los saldos de distintos días del mes).
3. **No aditivas**: No se pueden sumar directamente (ej. `precio_unitario`, `porcentaje_descuento`, `temperatura`). Se deben calcular promedios o ratios.

---

## 🏋️‍♂️ Práctica de la Lección 01

1. Ubicate en la carpeta de tu repositorio local `practica/modulo_04/`.
2. Creá el archivo `ej_01_diseno_kimball.sql`.
3. Escribí un script SQL (compatible con PostgreSQL o DuckDB) que implemente el diseño dimensional DDL para un proceso de **Ventas de E-Commerce**:

```
-- 1. Crear Dimensión Fecha (dim_fecha)
CREATE TABLE dim_fecha (
    fecha_key INT PRIMARY KEY, -- Formato YYYYMMDD (Ej: 20260115)
    fecha_completa DATE NOT NULL,
    anio INT NOT NULL,
    trimestre INT NOT NULL,
    mes INT NOT NULL,
    nombre_mes VARCHAR(15) NOT NULL,
    dia_semana VARCHAR(15) NOT NULL
);

-- 2. Crear Dimensión Cliente (dim_cliente)
CREATE TABLE dim_cliente (
    cliente_key INT PRIMARY KEY, -- Surrogate Key
    cliente_id_origen INT NOT NULL, -- Natural Key del OLTP
    nombre VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    pais VARCHAR(50) NOT NULL
);

-- 3. Crear Dimensión Producto (dim_producto)
CREATE TABLE dim_producto (
    producto_key INT PRIMARY KEY,
    producto_id_origen VARCHAR(20) NOT NULL,
    nombre_producto VARCHAR(100) NOT NULL,
    categoria VARCHAR(50) NOT NULL,
    marca VARCHAR(50) NOT NULL
);

-- 4. Crear Tabla de Hechos (fact_ventas)
-- DECLARACIÓN DEL GRANO: Una fila por cada ítem individual comprado en una orden
CREATE TABLE fact_ventas (
    venta_id BIGINT PRIMARY KEY,
    -- Claves Foráneas (Relaciones con Dimensiones)
    fecha_key INT NOT NULL REFERENCES dim_fecha(fecha_key),
    cliente_key INT NOT NULL REFERENCES dim_cliente(cliente_key),
    producto_key INT NOT NULL REFERENCES dim_producto(producto_key),
    
    -- Métricas Numéricas
    cantidad_unidades INT NOT NULL CHECK (cantidad_unidades &gt; 0),
    monto_unitario_usd DECIMAL(10,2) NOT NULL,
    monto_total_usd DECIMAL(10,2) NOT NULL -- Métrica Aditiva
);

```

1. Agregá comentarios al final del archivo SQL respondiendo:
  * **Consigna A**: Explicá por qué `monto_total_usd` es una métrica **Aditiva** mientras que `monto_unitario_usd` es **No Aditiva**.
  * **Consigna B**: Si un gerente pide analizar las ventas por "Región Geográfica del Cliente", ¿qué tabla de dimensión se debe consultar y qué cláusula SQL utilizará?