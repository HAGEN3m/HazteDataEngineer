# 🐘 Lección 01: Orden de Ejecución Lógico vs. Físico en Motores SQL y Poda de Datos

En la programación tradicional en Python (como vimos en el Módulo 01), el código es **imperativo**: le decís a la computadora *paso a paso cómo* debe procesar los datos.

En cambio, **SQL es un lenguaje declarativo**: le decís a la base de datos *qué resultados querés obtener*, y el **Optimizador de Consultas (** **Query Optimizer** **)** decide la forma más eficiente de calcularlo.

Para escribir consultas de alto rendimiento, un Data Engineer Ssr debe entender la diferencia entre cómo **escribimos** el código SQL y cómo el motor relacional **procesa lógicamente** la consulta a bajo nivel.

---

## 1\. El Orden Sintáctico (Cómo escribimos la query)

Escribimos la consulta en este orden por convención humana:

```
SELECT region, SUM(monto) AS total_ventas  -- 5. ¿Qué columnas devolvemos?
FROM fact_ventas                            -- 1. ¿De dónde sacamos los datos?
WHERE estado = 'COMPLETADA'                 -- 2. ¿Qué filas filtramos?
GROUP BY region                             -- 3. ¿Cómo agrupamos?
HAVING SUM(monto) &gt; 10000                   -- 4. ¿Qué grupos filtramos?
ORDER BY total_ventas DESC                  -- 6. ¿Cómo ordenamos?
LIMIT 10;                                   -- 7. ¿Cuántos registros mostramos?

```

---

## 2\. El Orden de Ejecución Lógico (Cómo procesa el motor)

El motor relacional (como PostgreSQL) procesa los datos en un orden completamente diferente. Comprender esta secuencia evita los errores más comunes de desarrollo:

```
┌────────────────────────────────────────────────────────┐
│ 1. FROM &amp; JOINs     ---&gt; Carga las tablas e identifica las filas. │
├────────────────────────────────────────────────────────┤
│ 2. WHERE            ---&gt; Filtra filas INDIVIDUALES (antes de agrupar). │
├────────────────────────────────────────────────────────┤
│ 3. GROUP BY         ---&gt; Colapsa filas en grupos únicos.          │
├────────────────────────────────────────────────────────┤
│ 4. HAVING           ---&gt; Filtra GRUPOS enteros (después de agrupar).│
├────────────────────────────────────────────────────────┤
│ 5. SELECT           ---&gt; Calcula expresiones y asigna ALIAS.      │
├────────────────────────────────────────────────────────┤
│ 6. DISTINCT         ---&gt; Elimina registros duplicados.            │
├────────────────────────────────────────────────────────┤
│ 7. ORDER BY         ---&gt; Ordena los resultados finales.           │
├────────────────────────────────────────────────────────┤
│ 8. LIMIT / OFFSET   ---&gt; Poda la cantidad de filas a retornar.    │
└────────────────────────────────────────────────────────┘

```

### 💡 Lecciones críticas derivadas del orden lógico:

1. **¿Por qué no podés usar un alias de** **SELECT** **en el** **WHERE** **?** Porque `WHERE` (Paso 2) se ejecuta **mucho antes** de que el `SELECT` (Paso 5) evalúe la columna o le asigne un alias.
  * ❌ *Incorrecto*: `SELECT monto * 1.21 AS total FROM ventas WHERE total &gt; 100`
  * 🟢 *Correcto*: `SELECT monto * 1.21 AS total FROM ventas WHERE (monto * 1.21) &gt; 100` (o usar una CTE).
2. **Diferencia fundamental entre** **WHERE** **y** **HAVING** **(Poda Temprana)**:
  * **WHERE**: Filtra filas **antes** de realizar la agregación. Reduce la cantidad de datos que deben cargarse en memoria RAM para el `GROUP BY`.
  * **HAVING**: Filtra grupos **después** de realizar la agregación.
  * **Regla de Performance**: Siempre que sea posible, filtrá con `WHERE` para achicar la masa de datos antes de agrupar.

```
-- ❌ INEFICIENTE: Filtra categorías recién DESPUÉS de agrupar todo el dataset
SELECT categoria, SUM(monto)
FROM ventas
GROUP BY categoria
HAVING categoria IN ('ELECTRONICA', 'HOGAR');

-- 🟢 OPTIMIZADO: Poda las filas ANTES de realizar el proceso de agregación
SELECT categoria, SUM(monto)
FROM ventas
WHERE categoria IN ('ELECTRONICA', 'HOGAR')
GROUP BY categoria;

```

---

## 3\. Poda de Datos (*Predicate Pushdown* en SQL)

Al igual que aprendimos en Polars con `scan_parquet()` en la Lección 38, el optimizador de PostgreSQL intenta aplicar **Predicate Pushdown**: mover los filtros del `WHERE` lo más cerca posible de la lectura inicial del disco para evitar leer bloques inútiles.

```
-- Buenas Prácticas de Poda:
-- Evitá envolver columnas indexadas en funciones dentro del WHERE, 
-- ya que esto anula la poda por índice:

-- ❌ Desactiva el uso de índices sobre la columna 'fecha'
WHERE DATE(fecha_transaccion) = '2026-01-15'

-- 🟢 Preserva la capacidad del motor de usar un índice (Sargable Query)
WHERE fecha_transaccion &gt;= '2026-01-15 00:00:00' 
  AND fecha_transaccion &lt; '2026-01-16 00:00:00'

```

---

## 🏋️‍♂️ Práctica de la Lección 01

1. Creá la carpeta `practica/modulo_02/` en tu repositorio.
2. Creá el archivo `ej_01_orden_ejecucion.sql`.
3. Escribí un script SQL (compatible con PostgreSQL o SQLite) que arme la siguiente consulta de auditoría financiera sobre una tabla hipotética `transacciones(id, cliente_id, monto, estado, fecha)`:
  * **Requerimiento**:
    * Seleccionar los 5 clientes (`cliente_id`) que hayan acumulado el mayor monto total de ventas durante el año 2026.
    * Considerar **únicamente** transacciones en estado `'COMPLETADA'`.
    * Incluir solo aquellos clientes cuyo acumulado supere los `$50,000`.
    * Retornar las columnas `cliente_id`, `monto_total` y `monto_promedio_por_ticket`.
  * **Desafío técnico**:
    * Asegurate de aplicar los filtros individuales en la etapa correcta (`WHERE`) y los filtros grupales en (`HAVING`).
    * Comentá al lado de cada cláusula (`FROM`, `WHERE`, `GROUP BY`, `HAVING`, `SELECT`, `ORDER BY`, `LIMIT`) el **número de orden de ejecución lógico** (del 1 al 7).