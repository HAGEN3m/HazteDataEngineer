# 🐘 Lección 10: Patrones Analíticos Avanzados en SQL — Problemas de Gaps & Islands, Análisis de Cohortes y Generación de Series Temporales (`generate_series`)

Damos inicio al **Bloque 4: Patrones Avanzados de Data Engineering, Data Quality y Cierre del Módulo 02**.

En las lecciones anteriores dominamos el orden de ejecución lógico, la arquitectura física de índices y particiones, el almacenamiento columnar (DuckDB) y las Funciones de Ventana (`ROW_NUMBER`, `LAG`, `LEAD`).

En esta lección abordaremos tres de los patrones analíticos más exigidos en pruebas técnicas y arquitecturas de datos en producción: **generación de series continuas**, resolución del problema clásico de **Gaps & Islands (Huecos e Islas)** y **Análisis de Cohortes (Retención)**.

---

## 1. Generación de Series Temporales Continuas (`generate_series`)

En los Data Warehouses y Data Marts analíticos ocurre un fenómeno muy común: si un día no hubo ventas o eventos, esa fecha no existe en la tabla transaccional.

Si calculás métricas diarias directamente sobre la tabla de hechos, las fechas sin actividad desaparecen del reporte en lugar de mostrar `$0.00` o `0` eventos, lo que rompe los gráficos de paneles BI (PowerBI, Tableau, Looker) o distorsiona los promedios móviles.

Para resolver esto de forma elegante, PostgreSQL y DuckDB proveen la función `generate_series()`, que genera una tabla temporal al vuelo con todas las fechas continuas del periodo deseado:

```sql
-- Generar un rango diario continuo completo para el mes de Enero 2026
WITH calendario AS (
    SELECT generate_series(
        '2026-01-01'::DATE,
        '2026-01-31'::DATE,
        '1 day'::INTERVAL
    )::DATE AS fecha
)
SELECT 
    c.fecha,
    COALESCE(SUM(v.monto), 0.0) AS total_ventas -- ⚡ Reemplaza NULLs por 0.0 en días sin ventas
FROM calendario c
LEFT JOIN fact_ventas v ON c.fecha = v.fecha_transaccion
GROUP BY c.fecha
ORDER BY c.fecha ASC;
```

---

## 2. El Patrón Gaps & Islands (Huecos e Islas)

El problema de **Gaps & Islands** es un clásico de la Ingeniería de Datos. Ocurre cuando tenés una secuencia de eventos o fechas y necesitás identificar:

* **Islas (*Islands*):** Rangos contiguos de fechas o valores consecutivos (ejemplo: determinar cuántos días seguidos un usuario estuvo activo / *streaks*).
* **Huecos (*Gaps*):** Periodos de inactividad o valores faltantes en la secuencia.

### ¿Cómo se resuelve el patrón Islands en SQL?

La clave reside en restar una secuencia matemática continua (`ROW_NUMBER()`) a la fecha de la transacción. Si las fechas son consecutivas, la diferencia entre la fecha y el número de fila permanece constante, generando un identificador único para cada "isla":

```sql
WITH eventos_ordenados AS (
    -- 1. Deduplicamos fechas de actividad por usuario
    SELECT DISTINCT 
        usuario_id, 
        fecha_actividad::DATE AS fecha
    FROM log_actividad
),
grupos_islas AS (
    -- 2. Restamos 'rn' días a la fecha.
    -- Para fechas consecutivas, (fecha - rn) produce SIEMPRE LA MISMA FECHA BASE.
    SELECT 
        usuario_id,
        fecha,
        fecha - (ROW_NUMBER() OVER (PARTITION BY usuario_id ORDER BY fecha)) * INTERVAL '1 day' AS grupo_isla
    FROM eventos_ordenados
)
-- 3. Agrupamos por el 'grupo_isla' para medir la racha (streak)
SELECT 
    usuario_id,
    MIN(fecha) AS inicio_racha,
    MAX(fecha) AS fin_racha,
    COUNT(*) AS dias_consecutivos_activos
FROM grupos_islas
GROUP BY usuario_id, grupo_isla
HAVING COUNT(*) >= 3 -- Filtramos rachas de al menos 3 días seguidos
ORDER BY usuario_id, inicio_racha;
```

---

## 3. Análisis de Cohortes (Cohort Analysis & Retention)

El **Análisis de Cohortes** agrupa a los usuarios según su fecha de adquisición (primera compra o registro) y rastrea su comportamiento y tasa de retención a lo largo de los meses subsiguientes ($M_0, M_1, M_2, \dots$).

Es el patrón por excelencia para medir el *churn* (pérdida de clientes) y la salud financiera de productos digitales.

```sql
WITH primera_compra AS (
    -- 1. Identificar el mes de la primera compra de cada cliente (Cohorte)
    SELECT 
        cliente_id,
        DATE_TRUNC('month', MIN(fecha_transaccion)) AS mes_cohorte
    FROM fact_ventas
    GROUP BY cliente_id
),
actividad_clientes AS (
    -- 2. Calcular el desfase de meses (Index) entre compras posteriores y la cohorte
    SELECT 
        v.cliente_id,
        p.mes_cohorte,
        EXTRACT(YEAR FROM AGE(DATE_TRUNC('month', v.fecha_transaccion), p.mes_cohorte)) * 12 + 
        EXTRACT(MONTH FROM AGE(DATE_TRUNC('month', v.fecha_transaccion), p.mes_cohorte)) AS indice_mes
    FROM fact_ventas v
    JOIN primera_compra p ON v.cliente_id = p.cliente_id
)
-- 3. Generar la matriz de retención de clientes por cohorte
SELECT 
    mes_cohorte,
    COUNT(DISTINCT CASE WHEN indice_mes = 0 THEN cliente_id END) AS mes_0_base,
    COUNT(DISTINCT CASE WHEN indice_mes = 1 THEN cliente_id END) AS mes_1_retencion,
    COUNT(DISTINCT CASE WHEN indice_mes = 2 THEN cliente_id END) AS mes_2_retencion,
    ROUND(
        (COUNT(DISTINCT CASE WHEN indice_mes = 1 THEN cliente_id END)::DECIMAL / 
        NULLIF(COUNT(DISTINCT CASE WHEN indice_mes = 0 THEN cliente_id END), 0)) * 100, 2
    ) AS pct_retencion_m1
FROM actividad_clientes
GROUP BY mes_cohorte
ORDER BY mes_cohorte;
```

---

## 🏋️‍♂️ Práctica de la Lección 10

1. Ubicate en la carpeta `practica/modulo_02/` de tu repositorio local.
2. Creá el archivo `ej_10_patrones_avanzados.sql`.
3. Escribí un script SQL (compatible con PostgreSQL o DuckDB) que resuelva la detección de rachas de inicios de sesión (*Gaps & Islands*):

```sql
-- 1. Crear tabla de accesos a la plataforma
CREATE TABLE logins_usuarios (
    usuario_id INT,
    fecha_login DATE
);

-- 2. Insertar historial de logins con secuencias y saltos
INSERT INTO logins_usuarios VALUES 
(101, '2026-01-01'),
(101, '2026-01-02'),
(101, '2026-01-03'), -- Isla 1 de Usuario 101: 3 días seguidos
(101, '2026-01-06'),
(101, '2026-01-07'), -- Isla 2 de Usuario 101: 2 días seguidos
(102, '2026-01-01'),
(102, '2026-01-05'); -- Días aislados de Usuario 102
```

4. Completá el script escribiendo una consulta usando la técnica de `ROW_NUMBER()` que devuelva:
   * `usuario_id`
   * `fecha_inicio_racha`
   * `fecha_fin_racha`
   * `dias_consecutivos`
   * Filtrá los resultados para mostrar únicamente aquellas rachas que sean de 2 o más días consecutivos.