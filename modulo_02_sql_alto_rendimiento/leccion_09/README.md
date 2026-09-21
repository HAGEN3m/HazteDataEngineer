# 🐘 Lección 09: Estructuración Modular de Código SQL — Expresiones de Tabla Comunes (`WITH` / CTEs) Encadenadas y CTEs Recursivas

Con esta lección cerramos el **Bloque 3: Consultas Analíticas Complejas y Funciones de Ventana**.

En las lecciones 07 y 08 exploramos las Funciones de Ventana para calcular rankings, desplazamientos (`LAG`/`LEAD`) y promedios móviles. A medida que las consultas analíticas crecen en complejidad, escribir todo en un único bloque monolítico con subconsultas anidadas (*Subqueries*) vuelve al código ilegible, frágil e imposible de testear o mantener.

En esta lección aprenderemos a modularizar pipelines SQL complejos con **CTEs (** **Common Table Expressions** **) Encadenadas** y a procesar estructuras de datos jerárquicas o en forma de grafo mediante **CTEs Recursivas (** **WITH RECURSIVE** **)**.

---

## 1\. Subconsultas Anidadas vs. CTEs (`WITH`)

Una **CTE (Common Table Expression)** es un conjunto de resultados temporal con nombre que existe únicamente durante el alcance de la ejecución de la consulta.

### El Anti-Patrón: Subconsultas Anidadas ("Código Spaghetto")

```
-- ❌ INEFICIENTE E ILEGIBLE: Difícil de depurar y rastrear el flujo de datos
SELECT cliente_id, total_monto
FROM (
    SELECT cliente_id, SUM(monto) AS total_monto
    FROM (
        SELECT * FROM fact_ventas WHERE estado = 'COMPLETADA'
    ) AS ventas_ok
    GROUP BY cliente_id
) AS resumen
WHERE total_monto &gt; 5000;

```

### El Patrón Profesional: CTEs Encadenadas

Las CTEs permiten leer la consulta de arriba hacia abajo como un **pipeline de transformación lineal**:

```
-- 🟢 ELEGANTE Y MODULAR: Cada paso tiene una única responsabilidad
WITH ventas_filtradas AS (
    SELECT transaccion_id, cliente_id, monto
    FROM fact_ventas
    WHERE estado = 'COMPLETADA'
),
resumen_clientes AS (
    SELECT 
        cliente_id, 
        SUM(monto) AS total_monto
    FROM ventas_filtradas
    GROUP BY cliente_id
)
SELECT cliente_id, total_monto
FROM resumen_clientes
WHERE total_monto &gt; 5000;

```

---

## 2\. Optimización y Materialización de CTEs (`MATERIALIZED` vs `NOT MATERIALIZED`)

A nivel de motor de base de datos (PostgreSQL 12+):

* **Inlining por defecto (** **NOT MATERIALIZED** **)**: Por defecto, el optimizador de PostgreSQL "fusiona" la CTE dentro de la consulta principal. Si filtrás la consulta final, ese filtro se "empuja" (*Predicate Pushdown*) hacia dentro de la CTE.
* **Materialización Forzada (** **WITH ... AS MATERIALIZED** **)**: Obliga al motor a ejecutar la CTE de forma aislada, guardando el resultado temporal en memoria/disco. Útil cuando una CTE pesada es leída **múltiples veces** dentro del mismo script.

```
-- Forzar la evaluación única de una sub-consulta muy costosa
WITH datos_pesados AS MATERIALIZED (
    SELECT cliente_id, SUM(monto) AS total
    FROM fact_ventas_historico
    GROUP BY cliente_id
)
SELECT * FROM datos_pesados d1 
JOIN datos_pesados d2 ON d1.cliente_id = d2.cliente_id;

```

---

## 3\. CTEs Recursivas (`WITH RECURSIVE`): Jerarquías y Grafos

Una **CTE Recursiva** es una consulta que se referencia a sí misma repetidamente hasta cumplir una condición de parada. Es la herramienta imprescindible en SQL para procesar estructuras de árbol o grafos (organigramas, categorías anidadas de e-commerce, linaje de datos o rutas).

### Anatomía de una CTE Recursiva

Consta de 3 partes obligatorias unidas por un **UNION ALL**:

```
WITH RECURSIVE nombre_cte AS (
    -- 1. CASO BASE / ANCLA (Anchor Member):
    -- Se ejecuta una sola vez para obtener el punto de partida.
    SELECT id, padre_id, nombre, 1 AS nivel
    FROM tabla_jerarquica
    WHERE padre_id IS NULL  -- Ej: El CEO o la categoría raíz
    
    UNION ALL
    
    -- 2. PASO RECURSIVO (Recursive Member):
    -- Se ejecuta iterativamente uniendo la tabla original con la propia CTE.
    SELECT t.id, t.padre_id, t.nombre, c.nivel + 1
    FROM tabla_jerarquica t
    JOIN nombre_cte c ON t.padre_id = c.id -- Conecta hijos con sus padres
)
-- 3. CONSULTA FINAL
SELECT * FROM nombre_cte;

```

---

## 4\. Ejemplo Práctico: Descomposición de la Cadena de Mando (Organigrama)

Supongamos la siguiente jerarquía de empleados:

```
       [1] Carlos (CEO)
            /        \
    [2] Ana (VP)    [3] Pedro (VP)
        /
  [4] Sofia (Dev)

```

```
WITH RECURSIVE organigrama AS (
    -- Anchor Member: Selecciona el nodo raíz (CEO)
    SELECT 
        empleado_id, 
        nombre, 
        manager_id, 
        1 AS nivel,
        nombre::TEXT AS ruta_jerarquica
    FROM empleados
    WHERE manager_id IS NULL
    
    UNION ALL
    
    -- Recursive Member: Busca los empleados supervisados por el nivel anterior
    SELECT 
        e.empleado_id, 
        e.nombre, 
        e.manager_id, 
        o.nivel + 1,
        o.ruta_jerarquica || ' -&gt; ' || e.nombre
    FROM empleados e
    JOIN organigrama o ON e.manager_id = o.empleado_id
)
SELECT 
    empleado_id, 
    nombre, 
    nivel, 
    ruta_jerarquica
FROM organigrama
ORDER BY nivel, empleado_id;

```

### Resultado:

| empleado\_id | nombre | nivel | ruta\_jerarquica       |
| ------------ | ------ | ----- | ---------------------- |
| **1**        | Carlos | 1     | Carlos                 |
| **2**        | Ana    | 2     | Carlos -&gt; Ana          |
| **3**        | Pedro  | 2     | Carlos -&gt; Pedro        |
| **4**        | Sofia  | 3     | Carlos -&gt; Ana -&gt; Sofia |

---

## 🏋️‍♂️ Práctica de la Lección 09

1. Ubicate en la carpeta `practica/modulo_02/` de tu repositorio local.
2. Creá el archivo `ej_09_ctes_recursivas.sql`.
3. Escribí un script SQL (compatible con PostgreSQL, DuckDB o SQLite) que resuelva la navegación de una estructura jerárquica de categorías de e-commerce:

```
-- 1. Crear tabla de categorías
CREATE TABLE categorias_ecommerce (
    categoria_id INT PRIMARY KEY,
    nombre VARCHAR(50),
    categoria_padre_id INT
);

-- 2. Insertar jerarquía de productos
INSERT INTO categorias_ecommerce VALUES
(1, 'Electrónica', NULL),
(2, 'Computación', 1),
(3, 'Laptops', 2),
(4, 'Laptops Gamer', 3),
(5, 'Hogar', NULL),
(6, 'Muebles', 5);

```

1. Completá el script construyendo una **CTE Recursiva** que devuelva:
  * `categoria_id`, `nombre`, `nivel_profundidad`.
  * **camino\_miga\_pan** **(** **Breadcrumb Path** **)**: Una cadena de texto que muestre el árbol completo, por ejemplo: `'Electrónica &gt; Computación &gt; Laptops &gt; Laptops Gamer'`.
  * Ordená los resultados por la profundidad y el ID.