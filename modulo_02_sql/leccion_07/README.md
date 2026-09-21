# 🐘 Lección 07: Funciones de Ventana I (`ROW_NUMBER`, `RANK`, `DENSE_RANK`, `NTILE` y `PARTITION BY`)

Damos inicio al **Bloque 3: Consultas Analíticas Complejas y Funciones de Ventana**.

En la **Lección 06** analizamos la diferencia entre motores de procesamiento fila por fila (OLTP) y motores columnares vectorizados (OLAP). Ahora profundizaremos en una de las herramientas más potentes del lenguaje SQL para Analytics &amp; Data Engineering: las **Funciones de Ventana (** **Window Functions** **)**.

---

## 1\. `GROUP BY` vs. Funciones de Ventana (*Window Functions*)

Para entender la diferencia conceptual:

* **GROUP BY** **(Agregación Colapsada)**: Agrupa múltiples filas en una sola fila de salida por cada grupo. Pierde el detalle individual de los registros.
* **Funciones de Ventana (** **OVER (...)** **)**: Realizan cálculos sobre un conjunto de filas relacionadas (*la ventana*), pero **conservan el 100% de las filas individuales intactas** en el resultado final.

```
Entrada (4 filas):       GROUP BY (1 fila por grupo):     WINDOW FUNCTION (4 filas intactas):
[100, Region A]  ───┐                                     [100, Region A, Avg: 150]
[200, Region A]  ───┼──&gt;  [Region A, Total: 300]   ───&gt;   [200, Region A, Avg: 150]
[300, Region B]  ───┤                                     [300, Region B, Avg: 350]
[400, Region B]  ───┘                                     [400, Region B, Avg: 350]

```

---

## 2\. Anatomía de la Cláusula `OVER()`

La sintaxis básica de una función de ventana consta de tres componentes:

```
FUNCION() OVER (
    PARTITION BY columna_grupo   -- 1. ¿Cómo dividimos los datos en ventanas independientes?
    ORDER BY columna_orden DESC  -- 2. ¿Cómo ordenamos los registros dentro de cada ventana?
) AS nombre_alias

```

1. **PARTITION BY**: Es el equivalente al `GROUP BY` dentro de la ventana. Si se omite, toda la tabla se trata como una única ventana gigante.
2. **ORDER BY**: Define la secuencia en la que se evalúan los registros dentro de cada partición. Es obligatorio para funciones de ranking.

---

## 3\. Funciones de Ranking: Diferencias Cruciales

Al ordenar registros dentro de una ventana, existen 4 funciones principales para asignar posiciones. La diferencia entre ellas radica en cómo manejan los **empates (valores idénticos)**:

| Función           | Comportamiento ante Empates                                                              | Ejemplo de Secuencia            |
| ----------------- | ---------------------------------------------------------------------------------------- | ------------------------------- |
| **ROW\_NUMBER()** | Asigna un número secuencial único e incremental. No repite números.                      | `1, 2, 3, 4, 5`                 |
| **RANK()**        | Asigna el mismo rango a valores iguales, pero **deja huecos** en la secuencia posterior. | `1, 2, 2, 4, 5` *(Salteó el 3)* |
| **DENSE\_RANK()** | Asigna el mismo rango a valores iguales **sin dejar huecos** en la secuencia.            | `1, 2, 2, 3, 4`                 |
| **NTILE(N)**      | Divide la partición en **N grupos/cuantiles** lo más equitativos posible.                | `1, 1, 2, 2, 3, 3` *(Para N=3)* |

```
SELECT 
    vendedor,
    monto,
    ROW_NUMBER() OVER (ORDER BY monto DESC) AS posicion_row_num,
    RANK()       OVER (ORDER BY monto DESC) AS posicion_rank,
    DENSE_RANK() OVER (ORDER BY monto DESC) AS posicion_dense,
    NTILE(4)     OVER (ORDER BY monto DESC) AS cuartil
FROM ventas;

```

---

## 4\. Patron de Data Engineering: Deduplicación Avanzada

En pipelines de datos (*ETL/ELT*), es habitual recibir registros duplicados desde sistemas de origen por reintentos de ingesta o fallos en la API.

El patrón estándar de la industria para **eliminar duplicados manteniendo solo el registro más reciente** consiste en combinar `ROW_NUMBER()` con una **CTE**:

```
-- Deduplicación Atómica: Obtener la última transacción por cada cliente
WITH transacciones_numeradas AS (
    SELECT 
        transaccion_id,
        cliente_id,
        monto,
        fecha_evento,
        ROW_NUMBER() OVER (
            PARTITION BY cliente_id 
            ORDER BY fecha_evento DESC, transaccion_id DESC
        ) AS rn
    FROM staging_transacciones
)
SELECT 
    transaccion_id,
    cliente_id,
    monto,
    fecha_evento
FROM transacciones_numeradas
WHERE rn = 1; -- ⚡ Se queda únicamente con la fila más reciente de cada cliente

```

---

## 🏋️‍♂️ Práctica de la Lección 07

1. Ubicate en la carpeta `practica/modulo_02/` de tu repositorio local.
2. Creá el archivo `ej_07_window_functions_ranking.sql`.
3. Escribí un script SQL (compatible con PostgreSQL, DuckDB o SQLite) que resuelva la siguiente necesidad analítica sobre una tabla sintética de salarios por departamento:

```
-- 1. Crear tabla de empleados
CREATE TABLE empleados (
    empleado_id INT,
    departamento VARCHAR(50),
    nombre VARCHAR(50),
    salario DECIMAL(10,2)
);

-- 2. Insertar registros con empates
INSERT INTO empleados VALUES
(101, 'DATA', 'Ana', 95000.00),
(102, 'DATA', 'Pedro', 95000.00),
(103, 'DATA', 'Maria', 80000.00),
(104, 'IT', 'Juan', 70000.00),
(105, 'IT', 'Carlos', 70000.00),
(106, 'IT', 'Sofia', 60000.00);

```

1. Completá el script construyendo una consulta que devuelva:
  * `departamento`, `nombre`, `salario`.
  * Columna `rn`: Calculada con `ROW_NUMBER()` por departamento ordenado por salario descendente.
  * Columna `rank_salario`: Calculada con `RANK()` por departamento ordenado por salario descendente.
  * Columna `dense_rank_salario`: Calculada con `DENSE_RANK()` por departamento ordenado por salario descendente.
2. Agregá una segunda consulta (usando CTE) que devuelva únicamente los **Top 2 salarios de cada departamento** usando `DENSE_RANK()`.