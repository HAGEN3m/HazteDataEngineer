# 🐘 Lección 08: Funciones de Ventana II — Desplazamientos (LAG, LEAD), Valores Extremos (FIRST_VALUE, LAST_VALUE) y Marcos de Ventana (ROWS/RANGE BETWEEN)

En la Lección 07 aprendimos las funciones de ranking (`ROW_NUMBER`, `RANK`, `DENSE_RANK`, `NTILE`) para numerar y deduplicar registros dentro de particiones.

En esta segunda parte de Funciones de Ventana exploraremos cómo navegar entre filas sin realizar autocruces (`SELF JOIN`s) costosos mediante `LAG` y `LEAD`, cómo capturar el primer o último valor con `FIRST_VALUE` y `LAST_VALUE`, y cómo acotar dinámicamente el alcance del cálculo utilizando **Marcos de Ventana (Window Frames)** para construir métricas como promedios móviles o crecimiento intermensual (MoM Growth).

---

## 1. Funciones de Desplazamiento: LAG y LEAD

En análisis de series temporales (*Time-Series*) es muy común comparar la fila actual con el registro anterior o posterior (por ejemplo: medir la variación de ventas respecto al mes anterior o calcular el tiempo transcurrido entre dos eventos de usuario).

Antes de las funciones de ventana, esto requería hacer un `JOIN` de la tabla consigo misma sobre una condición de fecha, lo cual era lento y complejo. `LAG` y `LEAD` resuelven esto con complejidad $\mathcal{O}(N)$:

* `LAG(columna, offset, default)`: Accede al valor de una fila ubicada $N$ posiciones atrás en el orden de la ventana.
* `LEAD(columna, offset, default)`: Accede al valor de una fila ubicada $N$ posiciones adelante en el orden de la ventana.

```sql
SELECT 
    fecha,
    monto,
    -- Obtiene el monto del día anterior (offset = 1 por defecto). Si no existe, asigna 0.0
    LAG(monto, 1, 0.0) OVER (ORDER BY fecha ASC) AS monto_dia_anterior,
    
    -- Calcula la diferencia absoluta respecto al día anterior
    monto - LAG(monto, 1, monto) OVER (ORDER BY fecha ASC) AS diferencia_diaria
FROM ventas_diarias;
```

---

## 2. Funciones de Valores Extremos: FIRST_VALUE y LAST_VALUE

* `FIRST_VALUE(columna)`: Devuelve el primer valor evaluado dentro de la ventana según el `ORDER BY`.
* `LAST_VALUE(columna)`: Devuelve el último valor evaluado dentro del marco de la ventana.

### 🚨 La "Trampa" de LAST_VALUE y el Marco por Defecto

Muchos desarrolladores se sorprenden al notar que `LAST_VALUE(columna)` a veces devuelve el valor de la fila actual en lugar del último registro real de la ventana.

Esto ocurre porque, si no se especifica el marco explícitamente, PostgreSQL aplica un marco por defecto: `RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW` (desde el inicio hasta la fila actual). Por lo tanto, para la fila evaluada en ese instante, el "último valor" visto hasta ese punto es ella misma.

---

## 3. Marcos de Ventana (Window Frames): ROWS vs. RANGE

Para solucionar la trampa de `LAST_VALUE` y poder calcular agregaciones móviles (como un promedio móvil de 7 días), debemos definir explícitamente el marco (*Frame Specification*):

```sql
{ ROWS | RANGE } BETWEEN limite_inferior AND limite_superior
```

### Opciones de Límite:
* `UNBOUNDED PRECEDING`: Desde el primer registro de la partición.
* `N PRECEDING`: $N$ filas hacia atrás desde la fila actual.
* `CURRENT ROW`: La fila actual.
* `N FOLLOWING`: $N$ filas hacia adelante.
* `UNBOUNDED FOLLOWING`: Hasta la última fila de la partición.

### Diferencia entre ROWS y RANGE:
* **`ROWS`**: Cuenta filas físicas estrictas sin importar si existen valores duplicados en el `ORDER BY`.
* **`RANGE`**: Agrupa rangos lógicos de valores iguales según la clave de ordenamiento.

```sql
-- 🟢 Promedio Móvil de 7 Días (La fila actual + 6 días anteriores)
SELECT 
    fecha,
    monto,
    AVG(monto) OVER (
        ORDER BY fecha ASC
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS promedio_movil_7d
FROM ventas_diarias;

-- 🟢 Solución correcta para LAST_VALUE (Abarca toda la ventana completa)
SELECT 
    cliente_id,
    fecha_transaccion,
    monto,
    LAST_VALUE(monto) OVER (
        PARTITION BY cliente_id
        ORDER BY fecha_transaccion ASC
        ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
    ) AS ultimo_monto_historico
FROM fact_ventas;
```

---

## 4. Patrón de Analytics Engineering: Cálculo de Crecimiento MoM (Month-over-Month)

A continuación se muestra cómo combinar `LAG` con expresiones para calcular el porcentaje de variación intermensual:

```sql
WITH ventas_mensuales AS (
    SELECT 
        DATE_TRUNC('month', fecha) AS mes,
        SUM(monto) AS total_mes
    FROM fact_ventas
    GROUP BY DATE_TRUNC('month', fecha)
)
SELECT 
    mes,
    total_mes,
    LAG(total_mes) OVER (ORDER BY mes ASC) AS total_mes_anterior,
    ROUND(
        ((total_mes - LAG(total_mes) OVER (ORDER BY mes ASC)) / 
        NULLIF(LAG(total_mes) OVER (ORDER BY mes ASC), 0)) * 100, 2
    ) AS crecimiento_pct_mom
FROM ventas_mensuales;
```

---

## 🏋️‍♂️ Práctica de la Lección 08

1. Ubicate en la carpeta `practica/modulo_02/` de tu repositorio local.
2. Creá el archivo `ej_08_window_functions_offset.sql`.
3. Escribí un script SQL (compatible con PostgreSQL, DuckDB o SQLite) sobre una tabla sintética de métricas diarias de un servidor:

```sql
-- 1. Crear tabla de telemetría diaria
CREATE TABLE telemetria_servidor (
    fecha DATE PRIMARY KEY,
    latencia_ms INT,
    solicitudes_totales INT
);

-- 2. Insertar registros sintéticos de 10 días
INSERT INTO telemetria_servidor VALUES
('2026-01-01', 120, 1000),
('2026-01-02', 115, 1200),
('2026-01-03', 130, 1100),
('2026-01-04', 180, 1500),
('2026-01-05', 200, 1800),
('2026