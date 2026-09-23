# 🛡️ Lección 11.B: Transacciones Atómicas, Niveles de Aislamiento e Idempotencia con MERGE / UPSERT

&gt; **Propósito**: Dominar el control de transacciones en motores relacionales y Data Lakes, comprendiendo las propiedades ACID a bajo nivel, los fenómenos de concurrencia, el bloqueo de filas (`FOR UPDATE / SKIP LOCKED`) y la implementación de patrones de ingesta **idempotentes** mediante `UPSERT` y `MERGE INTO`.

---

## 📌 1\. Las Propiedades ACID a Bajo Nivel

En sistemas de producción, una transacción es una unidad lógica de trabajo compuesta por una o varias sentencias SQL que deben ejecutarse bajo las garantías **ACID**:

```
           [ INICIO DE TRANSACCIÓN: BEGIN / START TRANSACTION ]
                                    │
    ┌───────────────────────────────┼───────────────────────────────┐
    ▼                               ▼                               ▼
[ Atomisidad ]              [ Consistencia ]                [ Durabilidad ]
Todo o nada.                Estado válido antes             Cambios persistentes
WAL / Rollback.             y después de la tx.             vía fsync en disco.
    └───────────────────────────────┬───────────────────────────────┘
                                    ▼
                             [ Aislamiento ]
                 Visibilidad de cambios concurrentes
                 gestionada por MVCC o Locks.

```

1. **Atomisidad (Atomicity)**: Si falla la sentencia 99 de 100, las 98 anteriores se revierten por completo (*Rollback*) gracias al **Write-Ahead Log (WAL)** o *Undo Log*.
2. **Consistencia (Consistency)**: La base de datos no permite violar reglas de integridad (claves primarias, reglas `CHECK`, *Foreign Keys*).
3. **Aislamiento (Isolation)**: Controla cómo y cuándo los cambios realizados por una transacción son visibles para otras transacciones simultáneas.
4. **Durabilidad (Durability)**: Una vez ejecutado el `COMMIT`, los datos están garantizados en almacenamiento no volátil (disco/SSD) mediante llamadas `fsync()`.

---

## 🔬 2\. Fenómenos de Concurrencia y Niveles de Aislamiento

Cuando múltiples pipelines o servicios escriben y leen de la misma tabla simultáneamente, ocurren cuatro fenómenos indeseados:

* **Dirty Read (Lectura Sucia)**: Leer datos modificados por otra transacción que **aún no ha hecho COMMIT** (y que podría hacer ROLLBACK).
* **Non-Repeatable Read (Lectura No Repetible)**: Leer una fila, que otra transacción la modifique y haga COMMIT, y al re-leer la misma fila obtener valores distintos.
* **Phantom Read (Lectura Fantasma)**: Ejecutar una consulta por rango (ej. `WHERE edad &gt; 30`), que otra transacción inserte nuevas filas en ese rango y haga COMMIT, y al re-ejecutar la consulta obtener más filas.
* **Serialization Anomaly**: El resultado de ejecutar transacciones en paralelo difiere de cualquier orden secuencial de las mismas.

### Tabla de Niveles de Aislamiento (Estándar ANSI SQL)

| Nivel de Aislamiento                           | Dirty Read    | Non-Repeatable Read | Phantom Read    | Serialization Anomaly |
| ---------------------------------------------- | ------------- | ------------------- | --------------- | --------------------- |
| **Read Uncommitted**                           | ⚠️ Posible    | ⚠️ Posible          | ⚠️ Posible      | ⚠️ Posible            |
| **Read Committed** *(Default Postgres/Oracle)* | 🛡️ Protegido | ⚠️ Posible          | ⚠️ Posible      | ⚠️ Posible            |
| **Repeatable Read** *(Default MySQL InnoDB)*   | 🛡️ Protegido | 🛡️ Protegido       | 🛡️ Protegido\* | ⚠️ Posible            |
| **Serializable**                               | 🛡️ Protegido | 🛡️ Protegido       | 🛡️ Protegido   | 🛡️ Protegido         |

&gt; *\*Nota: En PostgreSQL, Repeatable Read también previene Phantom Reads utilizando snapshots de MVCC.*

---

## 🛠️ 3\. Control de Concurrencia Avanzado: `FOR UPDATE` y `SKIP LOCKED`

Cuando construimos workers o pipelines distribuídos que procesan filas de una misma tabla de tareas, debemos evitar que dos nodos tomen el mismo registro (*Race Condition*).

### El Patrón de Cola de Trabajo Idempotente con `SKIP LOCKED`

```
-- Cada worker ejecuta esta sentencia para tomar 10 registros sin bloquear a los demás workers
BEGIN;

WITH tareas_disponibles AS (
    SELECT id
    FROM cola_procesamiento
    WHERE estado = 'PENDIENTE'
    ORDER BY fecha_creacion ASC
    LIMIT 10
    FOR UPDATE SKIP LOCKED  -- Bloquea las 10 filas e ignora las que ya estén bloqueadas por otros workers
)
UPDATE cola_procesamiento
SET estado = 'EN_PROCESO',
    worker_id = 'worker_node_01',
    fecha_inicio = NOW()
WHERE id IN (SELECT id FROM tareas_disponibles)
RETURNING id, payload;

COMMIT;

```

---

## ⚡ 4\. Idempotencia en Data Engineering: `UPSERT` y `MERGE INTO`

### ¿Qué es la Idempotencia?

Un pipeline o proceso es **idempotente** si ejecutarlo 1 vez o 100 veces consecutivas con los mismos datos de entrada produce exactamente el mismo estado final en la base de datos, sin duplicar ni corromper registros.

### A. Patrón `UPSERT` (PostgreSQL / SQLite)

Utiliza la cláusula `ON CONFLICT` sobre una clave única o restricción clave.

```
INSERT INTO dim_clientes (cliente_id, nombre, email, fecha_actualizacion)
VALUES (101, 'Ana López', 'ana.lopez@email.com', NOW())
ON CONFLICT (cliente_id) 
DO UPDATE SET
    nombre = EXCLUDED.nombre,
    email = EXCLUDED.email,
    fecha_actualizacion = EXCLUDED.fecha_actualizacion;

```

### B. Patrón `MERGE INTO` (ANSI SQL / Databricks / Snowflake / BigQuery / Postgres 15+)

Permite realizar `INSERT`, `UPDATE` y `DELETE` en una sola operación atómica comparando una tabla staging contra la tabla destino.

```
MERGE INTO target_ventas AS t
USING staging_ventas AS s
ON t.venta_id = s.venta_id
WHEN MATCHED AND s.fecha_modificacion &gt; t.fecha_modificacion THEN
    UPDATE SET 
        t.monto = s.monto,
        t.estado = s.estado,
        t.fecha_modificacion = s.fecha_modificacion
WHEN NOT MATCHED THEN
    INSERT (venta_id, cliente_id, monto, estado, fecha_modificacion)
    VALUES (s.venta_id, s.cliente_id, s.monto, s.estado, s.fecha_modificacion);

```

---

## 🏋️‍♂️ Ejercicio Práctico Hands-On: Ingesta Idempotente con Manejo de Conflictos

Crea el archivo `ingesta_idempotente.sql` para simular la carga incremental de ventas evitando duplicados:

```
-- 1. Crear tabla destino con restricción UNIQUE
CREATE TABLE IF NOT EXISTS fact_ventas_idempotente (
    venta_id INT PRIMARY KEY,
    cliente_id INT NOT NULL,
    monto NUMERIC(10,2) NOT NULL,
    version INT DEFAULT 1,
    actualizado_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Ingesta inicial (Primera ejecución)
INSERT INTO fact_ventas_idempotente (venta_id, cliente_id, monto)
VALUES 
    (1, 10, 150.00),
    (2, 20, 200.00)
ON CONFLICT (venta_id) DO UPDATE SET
    monto = EXCLUDED.monto,
    version = fact_ventas_idempotente.version + 1,
    actualizado_at = NOW();

-- 3. Re-ejecución con datos actualizados y un nuevo registro (Segunda ejecución)
-- La venta_id = 1 actualiza su monto; la venta_id = 3 se inserta; la venta_id = 2 queda intacta.
INSERT INTO fact_ventas_idempotente (venta_id, cliente_id, monto)
VALUES 
    (1, 10, 180.00), -- Cambio de monto
    (2, 20, 200.00), -- Mismo monto (idempotente)
    (3, 30, 350.00)  -- Nueva venta
ON CONFLICT (venta_id) DO UPDATE SET
    monto = EXCLUDED.monto,
    version = CASE 
                WHEN fact_ventas_idempotente.monto &lt;&gt; EXCLUDED.monto THEN fact_ventas_idempotente.version + 1
                ELSE fact_ventas_idempotente.version
              END,
    actualizado_at = NOW();

-- Verificar el resultado final
SELECT * FROM fact_ventas_idempotente ORDER BY venta_id;

```

---

## 🧠 Checkpoint de Autoevaluación

1. Explica la diferencia entre el fenómeno *Non-Repeatable Read* y *Phantom Read*.
2. ¿Por qué el uso de `FOR UPDATE SKIP LOCKED` es esencial para construir sistemas de colas de trabajo highly concurrentes en una base de datos relacional?
3. ¿Por qué es crítico que las tareas de un pipeline de ingesta incremental de datos sean **idempotentes**?
4. ¿Qué ventaja ofrece la sentencia `MERGE INTO` frente a ejecutar un `UPDATE` seguido de un `INSERT` en transacciones separadas?