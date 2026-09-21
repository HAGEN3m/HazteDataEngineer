# 🐘 Lección 03: Análisis de Planes de Ejecución (`EXPLAIN ANALYZE`), Detección de *Disk Spilling* y Evitación de *Full Table Scans*

En las lecciones anteriores exploramos el orden de ejecución lógico de las consultas y los algoritmos internos de los `JOIN`s (`Nested Loop`, `Hash Join`, `Merge Join`).

Cuando una consulta en producción tarda demasiado, un **Data Engineer Ssr** no adivina qué está pasando: utiliza la herramienta de diagnóstico fundamental del motor SQL, el comando **EXPLAIN ANALYZE**.

En esta lección aprenderemos a leer planes de ejecución físicos, identificar lecturas ineficientes en disco (**Seq Scan**), detectar consumo excesivo de memoria y corregir el **Disk Spilling** (desbordamiento de RAM a disco).

---

## 1\. Diferencia entre `EXPLAIN` y `EXPLAIN ANALYZE`

PostgreSQL provee dos formas de inspeccionar la estrategia que usará el optimizador:

* **EXPLAIN** **(Plan Estimado)**: Muestra el plan teórico que el optimizador calcula usando las estadísticas guardadas en la base de datos (`pg_statistic`), **sin ejecutar la consulta**.
* **EXPLAIN (ANALYZE, BUFFERS)** **(Plan Real)**: **Ejecuta la consulta realmente en la base de datos**, mide los tiempos exactos de CPU en milisegundos y reporta cuántas páginas de memoria RAM / Disco fueron leídas (`BUFFERS`).

```
-- Sintaxis recomendada para diagnóstico en PostgreSQL
EXPLAIN (ANALYZE, BUFFERS, TIMING, COSTS)
SELECT c.pais, SUM(v.monto) AS total
FROM fact_ventas v
JOIN dim_clientes c ON v.cliente_id = c.cliente_id
WHERE v.fecha &gt;= '2026-01-01'
GROUP BY c.pais;

```

&gt; ⚠️ **Advertencia de Producción**: Dado que `EXPLAIN ANALYZE` ejecuta la consulta de verdad, **nunca ejecutes** **EXPLAIN ANALYZE** **sobre sentencias** **DELETE** **o** **UPDATE** en bases de datos de producción a menos que estés dentro de una transacción que vayas a revertir (`ROLLBACK`).

---

## 2\. Cómo Leer un Plan de Ejecución

Los planes de ejecución en PostgreSQL se estructuran como un **árbol de nodos de abajo hacia arriba y de adentro hacia afuera**. Los nodos más internos son los primeros en procesarse y le entregan sus filas a los nodos superiores.

### Ejemplo de Salida de `EXPLAIN ANALYZE`:

```
HashAggregate  (cost=1850.00..1852.00 rows=200 width=40) (actual time=12.450..12.480 rows=15 loops=1)
  Group Key: c.pais
  Buffers: shared hit=320 read=15
  -&gt;  Hash Join  (cost=12.50..1700.00 rows=30000 width=12) (actual time=0.120..8.300 rows=30000 loops=1)
        Hash Cond: (v.cliente_id = c.cliente_id)
        -&gt;  Seq Scan on fact_ventas v  (cost=0.00..1500.00 rows=30000 width=12) (actual time=0.010..4.100 rows=30000 loops=1)
              Filter: (fecha &gt;= '2026-01-01'::date)
        -&gt;  Hash  (cost=10.00..10.00 rows=200 width=8) (actual time=0.080..0.080 rows=200 loops=1)
              Buckets: 1024  Batches: 1  Memory Usage: 17kB
              -&gt;  Seq Scan on dim_clientes c  (cost=0.00..10.00 rows=200 width=8) (actual time=0.005..0.030 rows=200 loops=1)

```

### 📊 Desglose de Métricas Clave:

1. **cost=12.50..1700.00**:
  * **Costo inicial (** **12.50** **)**: Unidades de I/O estimadas antes de devolver la primera fila.
  * **Costo total (** **1700.00** **)**: Unidades de I/O estimadas para devolver todas las filas.
2. **actual time=0.120..8.300**: Tiempo real transcurrido en milisegundos (Inicio..Fin del nodo).
3. **rows=30000** **vs** **actual rows=30000**:
  * Si la estimación teórica (`rows=X`) difiere por órdenes de magnitud del valor real (`actual rows=Y`), significa que las estadísticas de PostgreSQL están desactualizadas (requiere ejecutar `ANALYZE tabla`).
4. **Buffers: shared hit=320 read=15**:
  * `hit=320`: 320 páginas de 8KB fueron leídas directamente de la memoria caché (RAM).
  * `read=15`: 15 páginas tuvieron que leerse físicamente del disco.

---

## 3\. Tipos de Escaneo de Datos (*Access Methods*)

El primer punto de optimización es revisar cómo el nodo hoja lee los datos desde el almacenamiento:

| Método de Lectura                                 | Descripción                                                                                                                                | Evaluación de Performance                                                    |
| ------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------- |
| **Seq Scan** **(Sequential Scan)**                | Lee el 100% de los bloques del archivo de la tabla en disco de principio a fin.                                                            | 🔴 Pésimo para tablas grandes cuando se busca una fracción pequeña de filas. |
| **Index Scan**                                    | Recorre la estructura B-Tree del índice para encontrar las direcciones físicas (`TID`) y luego lee las filas correspondientes de la tabla. | 🟢 Excelente para alta selectividad (filtros que traen &lt; 5% de los datos).   |
| **Bitmap Index Scan** **\+** **Bitmap Heap Scan** | Escanea el índice, crea un mapa de bits de las páginas a leer, las ordena por ubicación física en disco y lee las páginas en un solo pase. | 🟡 Ideal cuando el filtro retorna entre 5% y 20% de los datos.               |
| **Index Only Scan**                               | Trae todos los datos requeridos directamente desde el índice sin siquiera tocar el archivo de la tabla.                                    | 🚀 El método de lectura más rápido posible.                                  |

---

## 4\. Detección y Solución de *Disk Spilling* (Uso de Disco Temporal)

Cuando una consulta requiere ordenar datos (`ORDER BY`), agrupar (`GROUP BY`) o construir una tabla Hash (`Hash Join`), intenta realizar la operación en la memoria RAM asignada por la variable **work\_mem** (que por defecto en PostgreSQL suele ser de tan solo `4MB`).

Si la cantidad de datos supera esa memoria RAM, el motor se ve obligado a escribir archivos temporales en el disco rígido (**Disk Spilling**), degradando el tiempo de respuesta hasta 100 veces.

### ¿Cómo identificarlo en el plan?

Buscá líneas como esta dentro del nodo `Sort` o `Hash`:

```
Sort Method: external merge  Disk: 18450kB  &lt;-- 🔴 Disk Spilling detectado
-- En lugar de:
Sort Method: quicksort  Memory: 1250kB     &lt;-- 🟢 Procesamiento 100% en RAM

```

### Solución en sesión de Data Engineering:

Podés incrementar temporalmente el espacio de memoria RAM permitido para la sesión activa antes de ejecutar la consulta pesada:

```
-- Aumenta la memoria de trabajo a 64 MB para la sesión actual
SET work_mem = '64MB';

-- Ejecutamos la consulta pesada
SELECT * FROM fact_ventas ORDER BY monto DESC LIMIT 1000;

-- Restablecemos la memoria
RESET work_mem;

```

---

## 🏋️‍♂️ Práctica de la Lección 03

1. Ubicate en la carpeta `practica/modulo_02/` de tu repositorio local.
2. Creá el archivo `ej_03_explain_analyze.sql`.
3. Escribí un script SQL para PostgreSQL que simule la creación y diagnóstico de una tabla no indexada:

```
-- 1. Crear tabla de logs sintética
CREATE TABLE logs_auditoria (
    id SERIAL PRIMARY KEY,
    usuario_id INT,
    accion VARCHAR(50),
    fecha_evento TIMESTAMP
);

-- 2. Insertar 100,000 registros sintéticos
INSERT INTO logs_auditoria (usuario_id, accion, fecha_evento)
SELECT 
    (random() * 1000)::INT,
    CASE WHEN random() &gt; 0.5 THEN 'LOGIN' ELSE 'LOGOUT' END,
    NOW() - (random() * interval '30 days')
FROM generate_series(1, 100000);

-- 3. Diagnóstico 1: Consulta sin índice
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM logs_auditoria 
WHERE usuario_id = 500 AND fecha_evento &gt;= NOW() - interval '1 day';

```

1. Agregá comentarios en el script respondiendo:
  * **Consigna A**: ¿Qué tipo de nodo de lectura (`Seq Scan` o `Index Scan`) utilizó PostgreSQL en la Consulta 1 y por qué?
  * **Consigna B**: Escribí la sentencia `CREATE INDEX` para optimizar esa consulta específica.
  * **Consigna C**: Volvé a ejecutar `EXPLAIN (ANALYZE, BUFFERS)` tras crear el índice y anotá la diferencia en milisegundos (`actual time`) y bloques leídos (`BUFFERS`).