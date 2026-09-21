# 📊 Lección 03: Diseños de Esquemas Analíticos — Esquema Estrella (Star Schema) vs. Copo de Nieve (Snowflake Schema)

En la Lección 02 aprendimos a gestionar la evolución temporal de los datos mediante Dimensiones de Cambio Lento (SCD Type 1, Type 2 y Type 3).

Ahora analizaremos la topología de la base de datos analítica: cómo se conectan físicamente la tabla de hechos y las tablas de dimensiones dentro del Data Warehouse. La elección entre un **Esquema Estrella (Star Schema)** y un **Esquema Copo de Nieve (Snowflake Schema)** impacta directamente en la velocidad de las consultas SQL, la simplicidad de uso para las herramientas de Business Intelligence (PowerBI, Tableau) y el esfuerzo de mantenimiento del pipeline de datos.

---

## 1. Esquema Estrella (Star Schema) — El Estándar Dimensional

El Esquema Estrella es la estructura dimensional clásica promovida por Ralph Kimball. Se caracteriza por tener una **única tabla de hechos central** rodeada de sus tablas de dimensiones completamente **desnormalizadas**.

Se denomina "Estrella" porque cada dimensión se conecta directamente a la tabla de hechos en un modelo radial de un solo nivel.

```text
                     ┌───────────────────────┐
                     │     dim_cliente       │
                     ├───────────────────────┤
                     │ cliente_key (PK)      │
                     │ nombre                │
                     │ pais                  │
                     │ ciudad                │
                     └───────────┬───────────┘
                                 │
                                 │ (1:N)
 ┌──────────────────┐            ▼            ┌──────────────────┐
 │    dim_fecha     │      ┌───────────┐      │   dim_producto   │
 ├──────────────────┤      │fact_ventas│      ├──────────────────┤
 │ fecha_key (PK)   │─────►│───────────│◄─────│ producto_key (PK)│
 │ anio             │ (1:N)│cliente_key│ (1:N)│ nombre_producto  │
 │ mes              │      │fecha_key  │      │ categoria        │
 └──────────────────┘      │prod_key   │      │ subcategoria     │
                           │monto      │      │ marca            │
                           └───────────┘      └──────────────────┘
```

### Características del Esquema Estrella:
* **Un Solo Salto (*One-Hop JOIN*):** Cualquier consulta analítica requiere, como máximo, hacer un `JOIN` entre la tabla de hechos y la dimensión necesaria. Nunca se hacen cruces entre dimensiones.
* **Dimensiones Desnormalizadas:** La jerarquía completa de un producto (`marca` $\rightarrow$ `subcategoria` $\rightarrow$ `categoria`) reside dentro de la misma tabla `dim_producto`, aunque se repitan valores de texto.
* **Optimizado para Motores OLAP:** Los motores columnares (ClickHouse, Snowflake, DuckDB) procesan filtros sobre dimensiones desnormalizadas a velocidad extrema aprovechando compresión por columnas y escaneos vectorizados.

---

## 2. Esquema Copo de Nieve (Snowflake Schema) — Normalización de Dimensiones

El Esquema Copo de Nieve es una variación del Esquema Estrella en la que las tablas de dimensiones están normalizadas (en Segunda o Tercera Forma Normal), dividiendo las jerarquías en múltiples sub-dimensiones secundarias.

```text
                                             ┌───────────────────────┐
                                             │     dim_categoria     │
                                             ├───────────────────────┤
                                             │ categoria_id (PK)     │
                                             │ nombre_categoria      │
                                             └───────────┬───────────┘
                                                         │ (1:N)
                                                         ▼
                                             ┌───────────────────────┐
                                             │   dim_subcategoria    │
                                             ├───────────────────────┤
                                             │ subcategoria_id (PK)  │
                                             │ categoria_id (FK)     │
                                             │ nombre_subcategoria   │
                                             └───────────┬───────────┘
                                                         │ (1:N)
                                                         ▼
                           ┌───────────┐     ┌───────────────────────┐
                           │fact_ventas│◄────│     dim_producto      │
                           └───────────┘     ├───────────────────────┤
                                             │ producto_key (PK)     │
                                             │ subcategoria_id (FK)  │
                                             │ nombre_producto       │
                                             └───────────────────────┘
```

### Características del Esquema Copo de Nieve:
* **Múltiples Saltos de JOIN (*Multi-Hop JOINs*):** Para consultar las ventas por categoría, el motor debe cruzar `fact_ventas` $\rightarrow$ `dim_producto` $\rightarrow$ `dim_subcategoria` $\rightarrow$ `dim_categoria`.
* **Cero Redundancia de Texto:** Las categorías y subcategorías no se repiten como texto; se almacenan en tablas independientes mediante claves foráneas.
* **Mayor Complejidad de Escritura:** Mantiene la integridad referencial estricta en orígenes transaccionales con estructuras jerárquicas complejas.

---

## 📊 Matriz Comparativa: Estrella vs. Copo de Nieve

| Criterio | Esquema Estrella (Star) | Esquema Copo de Nieve (Snowflake) |
| :--- | :--- | :--- |
| **Normalización** | Desnormalizado (Estándar OLAP) | Normalizado (Similar a OLTP) |
| **Cantidad de JOINs** | Baja (1 salto por dimensión) | Alta (Múltiples saltos anidados) |
| **Rendimiento de Consultas** | Máximo (Menor sobrecarga de CPU) | Menor (Mayor tiempo procesando cruces) |
| **Simplicidad para BI** | Muy Alta (Modelos intuitivos y limpios) | Compleja (Requiere crear vistas intermedias) |
| **Espacio en Disco** | Ligeramente mayor (Texto duplicado) | Mínimo (Claves numéricas normalizadas) |
| **Mantenimiento ETL/ELT** | Cargas más simples y directas | Cargas complejas en cascada por dependencias |

> ### 💡 Regla de Arquitectura para el Data Engineer Ssr
>
> **Priorizá SIEMPRE el Esquema Estrella.** En el almacenamiento analítico moderno (donde el costo de disco es sumamente bajo en comparación con el costo de cómputo/CPU), la velocidad de consulta y la simplicidad del modelo superan ampliamente el ahorro marginal de almacenamiento que ofrece la normalización del Copo de Nieve.

---

## 🏋️‍♂️ Práctica de la Lección 03

1. Ubicate en la carpeta `practica/modulo_04/` de tu repositorio local.
2. Creá el archivo `ej_03_esquemas_estrella_snowflake.sql`.
3. Escribí un script SQL (compatible con PostgreSQL o DuckDB) que compare ambos esquemas:

```sql
-- ============================================================
-- PARTE 1: IMPLEMENTACIÓN EN ESQUEMA ESTRELLA (Desnormalizado)
-- ============================================================
CREATE TABLE dim_producto_estrella (
    producto_key INT PRIMARY KEY,
    nombre_producto VARCHAR(100),
    subcategoria VARCHAR(50),
    categoria VARCHAR(50)
);

-- Consulta Estrella: 1 solo JOIN
-- SELECT p.categoria, SUM(v.monto) 
-- FROM fact_ventas v 
-- JOIN dim_producto_estrella p ON v.producto_key = p.producto_key 
-- GROUP BY p.categoria;

-- ============================================================
-- PARTE 2: IMPLEMENTACIÓN EN ESQUEMA COPO DE NIEVE (Normalizado)
-- ============================================================
CREATE TABLE dim_categoria_snowflake (
    categoria_id INT PRIMARY KEY,
    nombre_categoria VARCHAR(50)
);

CREATE TABLE dim_subcategoria_snowflake (
    subcategoria_id INT PRIMARY KEY,
    categoria_id INT REFERENCES dim_categoria_snowflake(categoria_id),
    nombre_subcategoria VARCHAR(50)
);

CREATE TABLE dim_producto_snowflake (
    producto_key INT PRIMARY KEY,
    subcategoria_id INT REFERENCES dim_subcategoria_snowflake(subcategoria_id),
    nombre_producto VARCHAR(100)
);

-- Consulta Copo de Nieve: 3 JOINs en cascada
-- SELECT c.nombre_categoria, SUM(v.monto)
-- FROM fact_ventas v
-- JOIN dim_producto_snowflake p ON v.producto_key = p.producto_key
-- JOIN dim_subcategoria_snowflake s ON p.subcategoria_id = s.subcategoria_id
-- JOIN dim_categoria_snowflake c ON s.categoria_id = c.categoria_id
-- GROUP BY c.nombre_categoria;