# 🐘 Lección 11: SQL Defensivo y Data Quality in-Database

En las lecciones anteriores del **Bloque 4** exploramos patrones analíticos avanzados como *Gaps &amp; Islands* y *Análisis de Cohortes*.

En producción, los pipelines de datos colapsan o producen reportes erróneos no por falta de sintaxis SQL, sino por **datos corruptos, incompletos o inesperados** provenientes de los sistemas de origen: valores nulos inesperados, divisiones por cero, registros duplicados e inconsistencias de tipos.

En esta lección aprenderemos el enfoque de **SQL Defensivo** y la aplicación de **Data Quality in-Database** para garantizar la integridad de las transformaciones antes de que impacten en el Data Lake o Data Warehouse.

---

## 1\. La Lógica Tri-Valuada en SQL (*Three-Valued Logic*) y la Trampa de los `NULL`s

A diferencia de la mayoría de los lenguajes de programación que usan lógica booleana bidimensional (`TRUE` / `FALSE`), SQL implementa **Lógica Tri-Valuada (** **Three-Valued Logic** **)**:

1. `TRUE`
2. `FALSE`
3. `UNKNOWN` (representado por `NULL`)

### 🚨 Comportamientos Peligrosos de `NULL`:

* **Comparaciones Directas**: `NULL = NULL` evalúa a `UNKNOWN` (falso en filtros `WHERE`). Por eso siempre se debe usar `IS NULL` o `IS NOT NULL`.
* **Subconsultas con** **NOT IN**: Si una subconsulta dentro de un `WHERE id NOT IN (SELECT id FROM ...)` retorna un solo valor `NULL`, **toda la consulta devolverá 0 filas**.
* **Agregaciones**: `SUM()`, `AVG()`, `COUNT(columna)` ignoran los valores `NULL`, pero `COUNT(*)` cuenta todas las filas incluyendo nulos.

```
-- ❌ RIESGO EXTREMO: Si la tabla descartados contiene un NULL, NO devolverá filas
SELECT * FROM clientes 
WHERE cliente_id NOT IN (SELECT cliente_id FROM descartados);

-- 🟢 SEGURO: Usar NOT EXISTS o filtrar explícitamente el NULL
SELECT * FROM clientes c
WHERE NOT EXISTS (
    SELECT 1 FROM descartados d WHERE d.cliente_id = c.cliente_id
);

```

---

## 2\. Funciones Defensivas Esenciales: `COALESCE` y `NULLIF`

### A. `COALESCE(val1, val2, ..., valN)`

Devuelve el primer valor **no nulo** de la lista de argumentos. Es la herramienta por excelencia para asignar valores por defecto en reportes o limpiadores.

```
-- Asigna 'DESCONOCIDO' si el nombre es NULL
SELECT COALESCE(nombre_cliente, 'DESCONOCIDO') AS cliente FROM dim_clientes;

```

### B. `NULLIF(val1, val2)`

Compara dos expresiones. Si `val1 == val2`, devuelve **NULL**; de lo contrario, devuelve `val1`.

### 🛡️ Prevención de División por Cero (*Division by Zero*)

En pipelines analíticos, calcular ratios o porcentajes sobre columnas con valor `0` provocará un error de ejecución que abortará el script. Combinar `NULLIF` con `COALESCE` previene el colapso:

```
SELECT 
    monto_total,
    cantidad_unidades,
    -- Si cantidad_unidades = 0, NULLIF devuelve NULL. 
    -- La división x / NULL da NULL (evitando el fallo por cero).
    -- COALESCE convierte ese NULL final a 0.0
    COALESCE(monto_total / NULLIF(cantidad_unidades, 0), 0.0) AS precio_promedio_unitario
FROM fact_ventas;

```

---

## 3\. Constraints Defensivos en Tabla (*Data Quality in-Database*)

El mejor lugar para evitar datos corruptos no es el código Python, sino el motor SQL mediante la aplicación de reglas de calidad atómicas (*Constraints*):

```
CREATE TABLE fact_ventas_defensiva (
    transaccion_id BIGINT PRIMARY KEY,
    cliente_id INT NOT NULL,
    monto DECIMAL(12,2) NOT NULL CHECK (monto &gt;= 0.0), -- ⚡ Garantiza montos positivos
    descuento DECIMAL(12,2) NOT NULL DEFAULT 0.0,
    estado VARCHAR(20) NOT NULL CHECK (estado IN ('PENDIENTE', 'COMPLETADA', 'CANCELADA')),
    fecha_transaccion DATE NOT NULL,
    
    -- Constraint compuesto: El descuento no puede superar al monto
    CONSTRAINT check_descuento_valido CHECK (descuento &lt;= monto)
);

```

---

## 4\. Inserciones Defensivas e Idempotencia (`ON CONFLICT` / `UPSERT`)

En arquitecturas de datos modernas, los pipelines deben ser **idempotentes**: ejecutarse múltiples veces con los mismos datos de entrada sin duplicar ni corromper el estado de la base de datos.

PostgreSQL permite manejar violaciones de clave primaria o índices únicos de forma elegante con **ON CONFLICT**:

```
-- Estrategia 1: Ignorar duplicados silenciosamente (Idempotencia en ingesta)
INSERT INTO dim_clientes (cliente_id, nombre, email)
VALUES (101, 'Ana Lopez', 'ana@email.com')
ON CONFLICT (cliente_id) DO NOTHING;

-- Estrategia 2: Actualización Atómica (UPSERT)
INSERT INTO fact_ventas_diarias (fecha, cliente_id, total_monto)
VALUES ('2026-01-15', 101, 1500.0)
ON CONFLICT (fecha, cliente_id) 
DO UPDATE SET 
    total_monto = fact_ventas_diarias.total_monto + EXCLUDED.total_monto,
    ultima_actualizacion = NOW();

```

---

## 🏋️‍♂️ Práctica de la Lección 11

1. Ubicate en la carpeta `practica/modulo_02/` de tu repositorio local.
2. Creá el archivo `ej_11_sql_defensivo.sql`.
3. Escribí un script SQL (compatible con PostgreSQL) que resuelva el saneamiento defensivo de una tabla staging ruidosa:

```
-- 1. Crear tabla staging con datos desprolijos
CREATE TABLE staging_ventas_raw (
    transaccion_id INT,
    cliente_id INT,
    monto_bruto DECIMAL(10,2),
    unidades INT,
    estado VARCHAR(30)
);

-- 2. Insertar registros con problemas de calidad (divisiones por cero, nulos, minúsculas)
INSERT INTO staging_ventas_raw VALUES
(101, 1, 500.00, 5, 'completada'),
(102, 2, 300.00, 0, 'COMPLETADA'),   -- Unidades = 0 (Riesgo de división por cero)
(103, 3, NULL, 2, 'Pendiente'),     -- Monto NULL
(104, 4, 150.00, NULL, 'CANCELADA');-- Unidades NULL

```

1. Completá el script escribiendo una consulta de **saneamiento defensivo** que retorne:
  * `transaccion_id`.
  * `cliente_id`.
  * `monto_limpio`: Reemplazar `NULL` por `0.0`.
  * `unidades_limpias`: Reemplazar `NULL` por `0`.
  * `precio_promedio_unitario`: Calculado defensivamente usando `COALESCE` y `NULLIF` para evitar colapsos de división por cero.
  * `estado_normalizado`: Convertido a mayúsculas con `UPPER()`.