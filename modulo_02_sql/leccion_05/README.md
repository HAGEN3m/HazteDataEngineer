# 🐘 Lección 05: Particionamiento Físico de Tablas (`Range`, `List`, `Hash`) y Poda de Particiones (*Partition Pruning*)

En la **Lección 04** aprendimos a optimizar búsquedas locales mediante estructuras de índices (`B-Tree`, `GIN`, `BRIN`). Sin embargo, cuando una tabla de hechos (*Fact Table*) en un Data Warehouse alcanza cientos de millones o miles de millones de registros (cientos de Gigabytes o Terabytes), los índices individuales vuelven a inflarse, saturan la RAM y ralentizan las escrituras.

En esta lección analizaremos el **Particionamiento Físico Declarativo**, una técnica de arquitectura que divide una tabla gigante (*Tabla Padre*) en múltiples archivos físicos independientes en disco (*Tablas Hijas / Particiones*), permitiendo al motor SQL omitir archivos enteros durante las consultas (**Partition Pruning**).

---

## 1\. Particionamiento Físico vs. Indexación

| Criterio                             | Indexación (`CREATE INDEX`)                                                 | Particionamiento (`PARTITION BY`)                                                        |
| ------------------------------------ | --------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| **Mecanismo**                        | Crea una estructura de datos secundaria que apunta a las filas de la tabla. | Divide físicamente el archivo de la tabla en múltiples archivos independientes en disco. |
| **Costo de Almacenamiento**          | Adicional (el índice ocupa disco y RAM extra).                              | Cero sobrecarga (los datos se distribuyen entre las particiones).                        |
| **Borrado Masivo (** **Purga** **)** | Lento (`DELETE FROM` genera registros en el WAL y fragmenta el disco).      | Instantáneo (`DROP TABLE particion_2023` elimina el archivo físico en milisegundos).     |
| **Mantenimiento**                    | Requiere reconstruir índices (`REINDEX`).                                   | Permite aislar el mantenimiento por partición activa.                                    |

---

## 2\. Estrategias de Particionamiento Declarativo en PostgreSQL

Desde PostgreSQL 10+, el particionamiento es **declarativo**: la tabla principal actúa como un esquema lógico (*Routing Layer*) y PostgreSQL enruta automáticamente cada `INSERT` o `SELECT` a la partición correspondiente.

Existen 3 estrategias principales:

### A. Particionamiento por Rango (`RANGE`)

Es la estrategia más utilizada en Ingeniería de Datos para series temporales (*Time-Series*) o rangos numéricos continuos.

```
-- 1. Crear la Tabla Padre (sin almacenamiento directo)
CREATE TABLE fact_ventas_part (
    transaccion_id BIGINT GENERATED ALWAYS AS IDENTITY,
    fecha_transaccion DATE NOT NULL,
    cliente_id INT,
    monto DECIMAL(12,2)
) PARTITION BY RANGE (fecha_transaccion);

-- 2. Crear las Particiones Hijas (archivos físicos en disco)
CREATE TABLE fact_ventas_2026_q1 PARTITION OF fact_ventas_part
    FOR VALUES FROM ('2026-01-01') TO ('2026-04-01');

CREATE TABLE fact_ventas_2026_q2 PARTITION OF fact_ventas_part
    FOR VALUES FROM ('2026-04-01') TO ('2026-07-01');

```

### B. Particionamiento por Lista (`LIST`)

Ideal cuando los datos se agrupan por valores discretos y conocidos (ej. países, regiones o unidades de negocio).

```
CREATE TABLE dim_clientes_region (
    cliente_id INT,
    pais VARCHAR(10) NOT NULL,
    nombre VARCHAR(100)
) PARTITION BY LIST (pais);

CREATE TABLE clientes_latam PARTITION OF dim_clientes_region
    FOR VALUES IN ('AR', 'CL', 'BR', 'UY');

CREATE TABLE clientes_europa PARTITION OF dim_clientes_region
    FOR VALUES IN ('ES', 'FR', 'DE', 'IT');

```

### C. Particionamiento por Hash (`HASH`)

Utiliza una función hash sobre la clave para distribuir de manera uniforme los registros entre N particiones fijas. Se utiliza para balancear carga de I/O o evitar puntos calientes (*Hotspots*) en escrituras masivas.

```
CREATE TABLE logs_ingesta (
    log_id UUID NOT NULL,
    payload TEXT
) PARTITION BY HASH (log_id);

-- Crear 4 particiones de peso equilibrado
CREATE TABLE logs_ingesta_p0 PARTITION OF logs_ingesta FOR VALUES WITH (MODULUS 4, REMAINDER 0);
CREATE TABLE logs_ingesta_p1 PARTITION OF logs_ingesta FOR VALUES WITH (MODULUS 4, REMAINDER 1);
CREATE TABLE logs_ingesta_p2 PARTITION OF logs_ingesta FOR VALUES WITH (MODULUS 4, REMAINDER 2);
CREATE TABLE logs_ingesta_p3 PARTITION OF logs_ingesta FOR VALUES WITH (MODULUS 4, REMAINDER 3);

```

---

## 3\. Poda de Particiones (*Partition Pruning*) y Performance

El verdadero beneficio analítico del particionamiento ocurre cuando el optimizador aplica **Partition Pruning**. Al ejecutar una consulta con un filtro en la cláusula `WHERE` sobre la columna de particionamiento, el motor analiza el plan de ejecución e **ignora por completo las particiones que no contienen datos relevantes**.

```
-- Si consultamos datos del primer trimestre de 2026:
EXPLAIN (ANALYZE, BUFFERS)
SELECT SUM(monto) 
FROM fact_ventas_part 
WHERE fecha_transaccion = '2026-02-15';

```

### Salida del Plan de Ejecución:

```
Aggregate  (cost=12.50..12.51 rows=1 width=8)
  -&gt;  Seq Scan on fact_ventas_2026_q1  (cost=0.00..12.25 rows=100 width=6)
-- ⚡ ¡PostgreSQL NI SIQUIERA ABRIÓ el archivo de fact_ventas_2026_q2 ni otras particiones!

```

---

## 4\. Gestión del Ciclo de Vida de los Datos (*Data Lifecycle &amp; Retention*)

En Data Lakes y Data Warehouses, las políticas de retención de datos exigen eliminar o archivar información antigua (ejemplo: eliminar datos de más de 5 años).

* ❌ **En tabla plana no particionada**: `DELETE FROM fact_ventas WHERE fecha &lt; '2021-01-01'`
  * Tarda horas, genera gigabytes de registros en el log WAL y deja espacio libre fragmentado (*Bloat*) en las páginas de disco.
* 🟢 **En tabla particionada**: `DROP TABLE fact_ventas_2020`
  * La operación se ejecuta en **milisegundos**, liberando instantáneamente el espacio en disco a nivel de sistema operativo.

---

## 🏋️‍♂️ Práctica de la Lección 05

1. Ubicate en la carpeta `practica/modulo_02/` de tu repositorio local.
2. Creá el archivo `ej_05_particionamiento.sql`.
3. Escribí un script SQL para PostgreSQL que configure una tabla particionada por rango anual:

```
-- 1. Crear tabla padre particionada por RANGE sobre la columna 'anio'
CREATE TABLE fact_telemetria (
    dispositivo_id INT NOT NULL,
    fecha_registro DATE NOT NULL,
    lectura DECIMAL(8,2),
    anio INT NOT NULL
) PARTITION BY RANGE (anio);

-- 2. Crear las particiones para los años 2025, 2026 y una partición DEFAULT
CREATE TABLE fact_telemetria_2025 PARTITION OF fact_telemetria
    FOR VALUES FROM (2025) TO (2026);

CREATE TABLE fact_telemetria_2026 PARTITION OF fact_telemetria
    FOR VALUES FROM (2026) TO (2027);

CREATE TABLE fact_telemetria_default PARTITION OF fact_telemetria DEFAULT;

-- 3. Insertar registros sintéticos de prueba
INSERT INTO fact_telemetria (dispositivo_id, fecha_registro, lectura, anio) VALUES
(101, '2025-05-10', 45.2, 2025),
(102, '2026-01-20', 88.1, 2026),
(103, '2024-11-05', 12.0, 2024); -- Cae en la partición DEFAULT

```

1. Verificá el comportamiento de **Partition Pruning**:
  * Escribí una consulta que filtre únicamente por `anio = 2026`.
  * Ejecutá `EXPLAIN (ANALYZE, BUFFERS)` y confirmá en el plan de ejecución que solo la tabla `fact_telemetria_2026` fue escaneada.
  * Escribí el comando SQL que eliminaría instantáneamente toda la información del año 2025 sin usar `DELETE`.