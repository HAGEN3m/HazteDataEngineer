# 🐘 Lección 05.B: Partitioning Avanzado, Sharding y Salting en SQL: Manejo de Data Skew

&gt; **Propósito**: Dominar las técnicas avanzadas de particionamiento físico (*Declarative Partitioning*), distribución de datos en clústeres y mitigación del sesgo de datos (*Data Skew*) mediante la técnica de *Salting*, para garantizar consultas de alto rendimiento y evitar nodos calientes (*hotspots*) en sistemas relacionales y Data Lakes.

---

## 📌 1\. ¿Qué es Data Skew y por qué destruye el rendimiento?

En bases de datos a gran escala y motores analíticos (PostgreSQL, Snowflake, BigQuery, Spark), el **Data Skew** ocurre cuando la distribución de los datos a través de las particiones físicas no es uniforme.

```
Distribución Uniforme (Ideal):
[Partición 1: 25%]  [Partición 2: 25%]  [Partición 3: 25%]  [Partición 4: 25%]

Data Skew (Sesgo severo / Hotspot):
[Partición 1: 90%]  [Partición 2: 3%]   [Partición 3: 4%]   [Partición 4: 3%]

```

### Consecuencias de Data Skew:

1. **Efecto Straggler (Nodo Colgado)**: El tiempo total de una consulta paralela queda determinado por la partición más lenta.
2. **Out Of Memory (OOM)**: El nodo que procesa la partición sesgada agota la RAM durante operaciones de `JOIN` o `GROUP BY`.

---

## 🔬 2\. Estrategias de Particionamiento Físico en SQL

Existen tres formas principales de dividir físicamente las tablas grandes:

1. **Particionamiento por Rango (Range Partitioning)**:
  * Ideal para series temporales (ej. particionar por `fecha_created`).
2. **Particionamiento por Lista (List Partitioning)**:
  * Agrupa datos según valores discretos (ej. `pais_codigo IN ('AR', 'BR', 'MX')`).
3. **Particionamiento por Hash (Hash Partitioning)**:
  * Aplica una función hash a una clave para distribuir las filas equitativamente entre N particiones.

---

## 🛠️ 3\. La Técnica de "Salting" para Eliminar Hotspots

Cuando una clave de agrupación o JOIN tiene un sesgo extremo (por ejemplo, el 80% de los eventos provienen del mismo `cliente_id = 9999`), el particionamiento tradicional por Hash o Lista falla.

### ¿Cómo funciona el Salting?

El **Salting** consiste en concatenar un valor aleatorio (un "sal") dentro de un rango fijo (ej. 0 a N-1) a la clave problemática antes de agrupar o reparticionar.

```
Clave Original Sesgada:   cliente_id = 9999 (10,000,000 registros)

Con Salting (N=4):       cliente_id_salted = "9999_0"  (2,500,000 registros)
                         cliente_id_salted = "9999_1"  (2,500,000 registros)
                         cliente_id_salted = "9999_2"  (2,500,000 registros)
                         cliente_id_salted = "9999_3"  (2,500,000 registros)

```

---

## ⚡ 4\. Implementación en SQL: Declarative Partitioning en PostgreSQL

```
-- 1. Crear tabla madre particionada por Rango (Fechas)
CREATE TABLE fact_ventas (
    venta_id BIGINT,
    cliente_id INT,
    fecha_venta DATE NOT NULL,
    monto NUMERIC(12,2)
) PARTITION BY RANGE (fecha_venta);

-- 2. Crear particiones físicas por mes
CREATE TABLE fact_ventas_2026_01 PARTITION OF fact_ventas
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');

CREATE TABLE fact_ventas_2026_02 PARTITION OF fact_ventas
    FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');

-- 3. Partition Pruning en acción
EXPLAIN ANALYZE
SELECT SUM(monto)
FROM fact_ventas
WHERE fecha_venta &gt;= '2026-01-15' AND fecha_venta &lt; '2026-01-20';
-- El Query Planner elimina (prunes) la partición de febrero sin tocar su disco.

```

---

## 🏋️‍♂️ Ejercicio Práctico Hands-On: Agrupación con Salting para Eliminar Data Skew

Crea el archivo `salting_demo.sql` para ver cómo resolver una agregación sesgada en SQL:

```
-- Caso: Un cliente "id_9999" genera el 90% de las transacciones
-- Paso 1: Agregar la columna "salt" aleatoria (de 0 a 3)
WITH transacciones_salted AS (
    SELECT 
        cliente_id,
        monto,
        -- Genera un valor entero aleatorio entre 0 y 3
        CONCAT(cliente_id, '_', FLOOR(RANDOM() * 4)) AS cliente_salt
    FROM fact_transacciones
),

-- Paso 2: Agregación en paralelo por la clave salted (distribuye la carga)
agregacion_parcial AS (
    SELECT 
        cliente_salt,
        SPLIT_PART(cliente_salt, '_', 1) AS cliente_id_real,
        SUM(monto) AS total_monto_parcial,
        COUNT(*) AS cantidad_parcial
    FROM transacciones_salted
    GROUP BY cliente_salt
)

-- Paso 3: Agregación final para consolidar los resultados salados
SELECT 
    cliente_id_real,
    SUM(total_monto_parcial) AS total_monto,
    SUM(cantidad_parcial) AS total_transacciones
FROM agregacion_parcial
GROUP BY cliente_id_real;

```

---

## 🧠 Checkpoint de Autoevaluación

1. ¿Qué es el fenómeno de *Partition Pruning* y cómo beneficia el tiempo de respuesta de las consultas?
2. ¿Por qué el particionamiento tradicional falla cuando existe un sesgo extremo en los datos (*Data Skew*)?
3. Explica el mecanismo de la técnica de *Salting* y cómo redistribuye la carga de procesamiento en un clúster.
4. ¿En qué se diferencia el particionamiento por Rango del particionamiento por Hash en un motor relacional o Data Lake?