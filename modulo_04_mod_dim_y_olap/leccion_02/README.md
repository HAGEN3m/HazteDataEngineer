# 📊 Lección 02: Tipos de Dimensiones Avanzadas (`SCD Type 1`, `Type 2` y `Type 3` — *Slowly Changing Dimensions*)

En la **Lección 01** aprendimos los fundamentos de la Metodología Kimball: la diferencia entre OLTP y OLAP, el concepto del **Grano** y la separación entre **Tablas de Hechos** (`fact_`) y **Tablas de Dimensiones** (`dim_`).

Sin embargo, los atributos de las entidades del mundo real **no son estáticos**:

* Un cliente que vivía en Argentina se muda a España.
* Un producto cambia de categoría o precio de lista.
* Un empleado es promovido y cambia de departamento o puesto.

Si sobreescribimos a la ciega los atributos en nuestras tablas de dimensión, **destruimos la verdad histórica**. Por ejemplo, si el cliente se mudó a España en 2026, pero recalculamos las ventas de 2024, atribuiríamos erróneamente esas compras pasadas a España en lugar de a Argentina.

Para resolver esto, Ralph Kimball definió las estrategias de **Dimensiones de Cambio Lento** (**SCD** — *Slowly Changing Dimensions*). En esta lección aprenderemos a implementar las tres estrategias principales (**Type 1**, **Type 2** y **Type 3**) con nivel de diseño de producción.

---

## 1\. Estrategias de Manejo de Cambios (SCD Types)

### A. SCD Type 1: Sobreescritura (Sin Historial)

Reemplaza el valor viejo por el nuevo directamente en la fila existente. Perdemos completamente el estado anterior.

* **Caso de Uso**: Corrección de errores tipográficos o datos donde el historial no tiene valor analítico (ej. corregir la ortografía de un nombre de cliente o actualizar un número de teléfono).
* **Ventaja**: Operación ultra simple que no incrementa el tamaño de la tabla.
* **Desventaja**: Destruye la trazabilidad histórica.

```
ANTES DEL CAMBIO:
cliente_key | cliente_id | nombre       | pais
101         | C-500      | Juan Gomez   | Argentina

DESPUÉS DEL CAMBIO (SCD Type 1 - Sobreescribe 'pais'):
cliente_key | cliente_id | nombre       | pais
101         | C-500      | Juan Gomez   | España   &lt;-- Se perdió el registro de Argentina

```

---

### B. SCD Type 2: Adición de Fila (Preservación Histórica Completa) — 🏆 El Estándar de la Industria

Crea una **nueva fila** en la tabla de dimensión para representar el nuevo estado, manteniendo la fila anterior intacta para preservar el historial.

Para diferenciar la versión activa de las versiones caducadas, se agregan columnas de control temporal:

* **fecha\_inicio** (*Effective Date*): Cuándo comenzó a ser válido este registro.
* **fecha\_fin** (*Expiration Date*): Cuándo dejó de ser válido (se usa `NULL` o `'9999-12-31'` para la versión activa).
* **es\_actual** (*Is Current Flag*): Booleano (`TRUE` / `FALSE`) que identifica rápidamente el registro vigente.

&gt; 🚨 **Requisito Indispensable**: SCD Type 2 **requiere obligatoriamente el uso de Claves Sustitutas (** **Surrogate Keys** **)**. La clave primaria natural del sistema origen (`cliente_id`) se repetirá en múltiples filas; por lo tanto, la clave primaria de la dimensión debe ser la clave sustituta autogenerada (`cliente_key`).

```
ANTES DEL CAMBIO:
cliente_key | cliente_id | nombre     | pais      | fecha_inicio | fecha_fin  | es_actual
101         | C-500      | Juan Gomez | Argentina | 2024-01-01   | NULL       | TRUE

DESPUÉS DEL CAMBIO (SCD Type 2 - Inserción + Cierre de Versión Anterior):
cliente_key | cliente_id | nombre     | pais      | fecha_inicio | fecha_fin  | es_actual
101         | C-500      | Juan Gomez | Argentina | 2024-01-01   | 2026-03-15 | FALSE
102         | C-500      | Juan Gomez | España    | 2026-03-15   | NULL       | TRUE

```

#### ¿Cómo interactúa con la Tabla de Hechos?

* Las ventas realizadas entre 2024 y marzo de 2026 se registraron apuntando a `cliente_key = 101` (Argentina).
* Las ventas realizadas a partir del 15 de marzo de 2026 se registrarán apuntando a `cliente_key = 102` (España).
* **Resultado**: Al ejecutar un reporte histórico de ventas por país, las compras de 2024 suman correctamente para Argentina y las de 2026 para España.

---

### C. SCD Type 3: Adición de Columna (Historial Limitado)

Mantiene la fila única del registro, pero agrega una columna adicional para guardar el valor inmediatamente anterior (`pais_anterior`).

* **Caso de Uso**: Cuando solo interesa comparar el valor actual contra el valor previo, sin necesidad de guardar un historial multi-versión.
* **Desventaja**: Solo retiene 1 nivel de historial. Si el dato cambia una tercera vez, el primer valor se pierde.

```
DESPUÉS DEL CAMBIO (SCD Type 3 - Columna Adicional):
cliente_key | cliente_id | nombre     | pais_actual | pais_anterior | fecha_cambio
101         | C-500      | Juan Gomez | España      | Argentina     | 2026-03-15

```

---

## 📊 Matriz Comparativa: SCD Type 1 vs Type 2 vs Type 3

| Criterio                   | SCD Type 1               | SCD Type 2                                            | SCD Type 3                     |
| -------------------------- | ------------------------ | ----------------------------------------------------- | ------------------------------ |
| **Mecanismo**              | Sobreescribe el registro | **Inserta una nueva fila**                            | Agrega una columna `_anterior` |
| **Preservación Histórica** | Nula (0%)                | **Completa (100%)**                                   | Limitada al último cambio      |
| **Uso de Memoria/Disco**   | Bajo (Filas fijas)       | Crece proporcionalmente a los cambios                 | Bajo                           |
| **Complejidad de Ingesta** | Baja (`UPDATE`)          | **Media / Alta (** **UPDATE** **\+** **INSERT** **)** | Baja (`UPDATE`)                |
| **Requisito de Clave**     | Clave Natural            | **Clave Sustituta (** **Surrogate Key** **)**         | Clave Natural                  |

---

## 🛠️ Patrón de Ingesta SQL para SCD Type 2

Cuando ingresa una actualización desde el sistema origen (ej. `cliente_id = 'C-500'` cambió su país a `'España'`), el proceso ETL/ELT debe ejecutar dos pasos dentro de una **transacción atómica**:

```
BEGIN TRANSACTION;

-- Paso 1: "Cerrar" la versión vigente actual marcando su fecha de fin y flag es_actual
UPDATE dim_cliente
SET 
    fecha_fin = CURRENT_DATE,
    es_actual = FALSE
WHERE cliente_id_origen = 'C-500' 
  AND es_actual = TRUE;

-- Paso 2: "Insertar" el nuevo registro con una nueva Surrogate Key
INSERT INTO dim_cliente (
    cliente_id_origen, nombre, email, pais, fecha_inicio, fecha_fin, es_actual
) VALUES (
    'C-500', 'Juan Gomez', 'juan@email.com', 'España', CURRENT_DATE, NULL, TRUE
);

COMMIT;

```

---

## 🏋️‍♂️ Práctica de la Lección 02

1. Ubicate en la carpeta `practica/modulo_04/` de tu repositorio local.
2. Creá el archivo `ej_02_scd_types.sql`.
3. Escribí un script SQL (compatible con PostgreSQL o DuckDB) que demuestre el comportamiento de **SCD Type 2**:

```
-- 1. Crear tabla de dimensión con soporte para SCD Type 2
CREATE TABLE dim_cliente_scd2 (
    cliente_key SERIAL PRIMARY KEY,      -- Surrogate Key
    cliente_id_origen VARCHAR(20) NOT NULL, -- Natural Key
    nombre VARCHAR(100) NOT NULL,
    pais VARCHAR(50) NOT NULL,
    segmento VARCHAR(20) NOT NULL,
    
    -- Control de Versiones SCD Type 2
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE,
    es_actual BOOLEAN NOT NULL DEFAULT TRUE
);

-- 2. Inserción Inicial: El cliente 'C-101' se registra originalmente en Argentina
INSERT INTO dim_cliente_scd2 (cliente_id_origen, nombre, pais, segmento, fecha_inicio, fecha_fin, es_actual)
VALUES ('C-101', 'Laura Martinez', 'Argentina', 'STANDARD', '2025-01-01', NULL, TRUE);

-- 3. Simular el cambio de residencia a España el 2026-03-15 (Aplicando el patrón SCD Type 2)
UPDATE dim_cliente_scd2
SET fecha_fin = '2026-03-15', es_actual = FALSE
WHERE cliente_id_origen = 'C-101' AND es_actual = TRUE;

INSERT INTO dim_cliente_scd2 (cliente_id_origen, nombre, pais, segmento, fecha_inicio, fecha_fin, es_actual)
VALUES ('C-101', 'Laura Martinez', 'España', 'VIP', '2026-03-15', NULL, TRUE);

-- 4. Consulta de verificación
SELECT cliente_key, cliente_id_origen, nombre, pais, segmento, fecha_inicio, fecha_fin, es_actual
FROM dim_cliente_scd2
WHERE cliente_id_origen = 'C-101'
ORDER BY cliente_key ASC;

```

1. Agregá comentarios al final del script respondiendo:
  * **Consigna A**: ¿Qué ocurriría con el reporte de ventas históricas de 2025 si hubiésemos aplicado `SCD Type 1` en lugar de `SCD Type 2` al momento de la mudanza de Laura?
  * **Consigna B**: Escribí una consulta `SELECT` que traiga únicamente la versión **actualmente vigente** de todos los clientes en la dimensión.