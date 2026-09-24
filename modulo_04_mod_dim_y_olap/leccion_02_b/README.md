# 📐 Lección 02.B (Módulo 04): Slowly Changing Dimensions (SCD Tipos 0 a 6) y Patrones de MERGE / UPSERT

&gt; **Propósito**: Dominar el manejo del cambio histórico en tablas de dimensiones analíticas mediante la implementación de Slowly Changing Dimensions (SCD) de Tipo 0 al Tipo 6, comprendiendo el impacto en el almacenamiento, la complejidad de consulta y la construcción de pipelines idempotentes con SQL ANSI y Python/DataFrames.

---

## 📌 1\. El Desafío de la Historiabilidad en Datos Analíticos

En sistemas OLTP, cuando un cliente cambia su dirección o correo, el registro se sobrescribe directamente. Sin embargo, en un Data Warehouse o Data Lakehouse, si un cliente vivía en "Buenos Aires" en 2024 y compró $1,000, pero en 2026 se mudo a "Madrid", ¿a qué ubicación debemos atribuir las ventas de 2024?

Para resolver esto, Ralph Kimball definió el patrón de **Slowly Changing Dimensions (SCD)**.

---

## 🔬 2\. Clasificación Completa de SCD (Tipos 0 al 6)

### A. SCD Tipo 0: Retener Original (Inmutable)

* **Concepto**: El dato nunca cambia. Una vez insertado, permanece intacto (ej. fecha de nacimiento, país de origen del registro).
* **Uso**: Atributos estáticos.

### B. SCD Tipo 1: Sobrescribir (Sin Historial)

* **Concepto**: El valor nuevo reemplaza al valor viejo. Se pierde la historia anterior.
* **Uso**: Corrección de errores ortográficos, cambios no relevantes para el negocio (ej. código postal corregido).

### C. SCD Tipo 2: Agregar Nueva Fila (Historial Completo)

* **Concepto**: Se inserta una nueva fila con la nueva versión. Se utilizan columnas de control: `surrogate_key`, `is_current` (BOOLEAN), `valid_from` (TIMESTAMP) y `valid_to` (TIMESTAMP).
* **Uso**: Atributos críticos para análisis histórico (ej. cambio de categoría de cliente, cambio de región de ventas).

### D. SCD Tipo 3: Agregar Nueva Columna (Historial Limitado)

* **Concepto**: Se guarda el valor anterior en una columna dedicada (`direccion_actual`, `direccion_anterior`). Solo mantiene N versiones fijas.
* **Uso**: Comparación directa de 2 estados sin agregar filas a la dimensión.

### E. SCD Tipo 4: Tabla de Historia Separada (Mini-Dimension)

* **Concepto**: La dimensión principal mantiene solo el estado actual (Tipo 1), y los cambios se envían a una tabla histórica independiente (*History Table* / *Outrigger*).
* **Uso**: Atributos que cambian muy rápido (*Fast-Changing Attributes*) en dimensiones masivas de millones de filas.

### F. SCD Tipo 6: Híbrido (1 + 2 + 3 = 6)

* **Concepto**: Combina Tipo 1, Tipo 2 y Tipo 3\. Crea nuevas filas para el historial (Tipo 2), incluye una columna para el valor anterior (Tipo 3) y actualiza el valor actual en todas las filas históricas (Tipo 1).
* **Uso**: Reportes que requieren analizar transacciones pasadas con la perspectiva actual Y con la perspectiva histórica simultáneamente.

---

## 🛠️ 3\. Comparativa de Complejidad y Almacenamiento

| Tipo SCD  | Mantiene Historial    | Impacto en RAM/Almacenamiento   | Complejidad de Consulta (`JOIN`)                   |
| --------- | --------------------- | ------------------------------- | -------------------------------------------------- |
| **SCD 0** | No                    | Nulo                            | Muy Baja                                           |
| **SCD 1** | No                    | Nulo                            | Muy Baja                                           |
| **SCD 2** | ✅ Sí (Completo)       | Alto (Duplica/multiplica filas) | Media (`valid_from &lt;= fecha AND valid_to &gt; fecha`) |
| **SCD 3** | ✅ Parcial (1 versión) | Muy Bajo                        | Baja                                               |
| **SCD 4** | ✅ Sí (Separado)       | Medio                           | Media                                              |
| **SCD 6** | ✅ Sí (Híbrido)        | Alto                            | Alta                                               |

---

## ⚡ 4\. Implementación de SCD Tipo 2 en SQL con `MERGE INTO` / `UPDATE` \+ `INSERT`

En motores modernos (PostgreSQL 15+, Databricks Delta, Snowflake, BigQuery), el patrón SCD 2 se implementa combinando un `UPDATE` de las filas existentes para cerrar su vigencia (`valid_to = NOW()`, `is_current = FALSE`) seguido de un `INSERT` de la nueva versión.

```
-- Paso 1: Cerrar vigencia de registros que cambiaron (Inactivar versión vieja)
UPDATE dim_clientes d
SET
    valid_to = s.fecha_efectiva,
    is_current = FALSE
FROM staging_clientes s
WHERE d.cliente_id = s.cliente_id
  AND d.is_current = TRUE
  AND (d.direccion &lt;&gt; s.direccion OR d.categoria &lt;&gt; s.categoria);

-- Paso 2: Insertar la nueva versión activa (SCD Tipo 2)
INSERT INTO dim_clientes (
    cliente_id, nombre, direccion, categoria, is_current, valid_from, valid_to
)
SELECT
    s.cliente_id, s.nombre, s.direccion, s.categoria,
    TRUE AS is_current,
    s.fecha_efectiva AS valid_from,
    '9999-12-31 23:59:59'::TIMESTAMP AS valid_to
FROM staging_clientes s
LEFT JOIN dim_clientes d
    ON s.cliente_id = d.cliente_id AND d.is_current = TRUE
WHERE d.cliente_id IS NULL -- Nuevos clientes
   OR (d.direccion &lt;&gt; s.direccion OR d.categoria &lt;&gt; s.categoria); -- Clientes con cambios

```

---

## 🏋️‍♂️ Ejercicio Práctico Hands-On: Simulación de SCD 2 en PostgreSQL

Crea el archivo `scd2_pipeline.sql` para probar la evolución histórica de un cliente:

```
-- 1. Crear la tabla de dimensión SCD Tipo 2
CREATE TABLE IF NOT EXISTS dim_empleados_scd2 (
    employee_sk SERIAL PRIMARY KEY,      -- Surrogate Key
    employee_id INT NOT NULL,            -- Natural / Business Key
    nombre VARCHAR(100),
    departamento VARCHAR(50),
    salario NUMERIC(10,2),
    is_current BOOLEAN DEFAULT TRUE,
    valid_from TIMESTAMP NOT NULL,
    valid_to TIMESTAMP DEFAULT '9999-12-31 23:59:59'
);

-- 2. Estado Inicial (Día 1): Carlos ingresa a 'Ventas'
INSERT INTO dim_empleados_scd2 (employee_id, nombre, departamento, salario, is_current, valid_from)
VALUES (101, 'Carlos Gómez', 'Ventas', 50000.00, TRUE, '2026-01-01 00:00:00');

-- 3. Transición (Día 30): Carlos es promovido a 'Gerencia' con aumento de sueldo
-- A. Inactivar registro anterior
UPDATE dim_empleados_scd2
SET is_current = FALSE,
    valid_to = '2026-01-30 00:00:00'
WHERE employee_id = 101 AND is_current = TRUE;

-- B. Insertar nueva versión activa
INSERT INTO dim_empleados_scd2 (employee_id, nombre, departamento, salario, is_current, valid_from)
VALUES (101, 'Carlos Gómez', 'Gerencia', 75000.00, TRUE, '2026-01-30 00:00:00');

-- 4. Consulta de Análisis Histórico a la fecha 2026-01-15 (Debe traer la versión de Ventas)
SELECT *
FROM dim_empleados_scd2
WHERE employee_id = 101
  AND '2026-01-15 00:00:00' BETWEEN valid_from AND valid_to;

-- 5. Consulta de Estado Actual (Debe traer la versión de Gerencia)
SELECT *
FROM dim_empleados_scd2
WHERE employee_id = 101 AND is_current = TRUE;

```

---

## 🧠 Checkpoint de Autoevaluación

1. ¿Por qué el uso de claves naturales (*Business Keys*) es insuficiente para implementar SCD Tipo 2 y requerimos una clave subrogada (*Surrogate Key*)?
2. ¿Cuál es el caso de uso ideal para implementar SCD Tipo 4 (Mini-Dimensiones) en lugar de SCD Tipo 2?
3. Explica la diferencia operativa y de análisis entre aplicar SCD Tipo 1 vs. SCD Tipo 2 ante la corrección de un error tipográfico en el nombre de un cliente.
4. ¿Qué combinación de tipos forma la estrategia SCD Tipo 6 y por qué se denomina "híbrida"?