🐘 Lección 12: Cierre del Módulo 02 — Proyecto Integrador de SQL (Refactorización y Optimización 100x)¡Llegamos al hito final del Módulo 02: SQL de Alto Rendimiento!A lo largo de este módulo hemos dominado las tripas de los motores relacionales:Lección 01: Orden de ejecución lógico (FROM $\rightarrow$ WHERE $\rightarrow$ GROUP BY $\rightarrow$ HAVING $\rightarrow$ SELECT).Lección 02: Algoritmos internos de JOIN (Nested Loop, Hash Join, Merge Join).Lección 03: Diagnóstico con EXPLAIN (ANALYZE, BUFFERS) y corrección de Disk Spilling ajustando work_mem.Lección 04: Indexación avanzada (B-Tree, GIN, BRIN, índices parciales y compuestos).Lección 05: Particionamiento físico de tablas (RANGE, LIST, HASH) y Partition Pruning.Lección 06: Motores columnares OLAP (DuckDB) vs. Row-Based (PostgreSQL) y cómputo vectorizado.Lección 07: Funciones de Ventana de Ranking (ROW_NUMBER, RANK, DENSE_RANK, NTILE).Lección 08: Funciones de Ventana de Desplazamiento (LAG, LEAD) y marcos dinámicos (ROWS BETWEEN).Lección 09: Modularización de pipelines con CTEs encadenadas y CTEs recursivas (WITH RECURSIVE).Lección 10: Patrones analíticos avanzadas (generate_series, Gaps & Islands, Análisis de Cohortes).Lección 11: SQL defensivo, manejo de NULLs, prevención de división por cero e idempotencia (ON CONFLICT).En esta lección integraremos todas estas técnicas en un Proyecto Capstone de Refactorización SQL, transformando un script legacy ineficiente que colapsa la base de datos en un pipeline limpio, defensivo y hasta 100 veces más rápido.1. El Escenario de ProducciónImaginemos que heredamos una consulta de reporte analítico sobre un Data Warehouse en PostgreSQL con más de 10,000,000 de filas. El reporte actual tarda 18 minutos en ejecutarse, consume el 100% de la CPU del servidor y provoca desbordamientos a disco (Disk Spilling).🔴 El Script Ineficiente Legacy (Anti-Patrón):-- ❌ SCRIPT LEGACY: Tarda 18 minutos y colapsa la memoria RAM
SELECT 
    v.cliente_id,
    c.nombre,
    c.pais,
    COUNT(DISTINCT v.transaccion_id) AS total_compras,
    SUM(v.monto) AS total_gastado,
    SUM(v.monto) / COUNT(v.transaccion_id) AS ticket_promedio -- Riesgo de división por cero
FROM fact_ventas v, dim_clientes c  -- Implicit Join antiguo (Cartesiano ineficiente)
WHERE v.cliente_id = c.cliente_id
  AND DATE(v.fecha_transaccion) >= '2026-01-01' -- Invalida el uso de índices B-Tree
  AND c.cliente_id NOT IN (                      -- Riesgo de subconsulta con NULLs
      SELECT cliente_id FROM clientes_bloqueados
  )
GROUP BY v.cliente_id, c.nombre, c.pais
HAVING c.pais IN ('ARGENTINA', 'CHILE', 'URUGUAY') -- Filtra grupos DESPUÉS de agrupar todo
ORDER BY total_gastado DESC;
2. Diagnóstico del Plan de Ejecución (EXPLAIN ANALYZE)Al ejecutar EXPLAIN (ANALYZE, BUFFERS) sobre la consulta legacy, identificamos los siguientes cuellos de botella:Seq Scan on fact_ventas: La función DATE(v.fecha_transaccion) impide usar el índice B-Tree de la columna fecha_transaccion.Filter: NOT IN (Subplan 1): La subconsulta con NOT IN realiza un escaneo secuencial repetido por cada fila.Sort Method: external merge Disk: 48500kB: La agregación y ordenamiento superan los 4MB de work_mem, provocando Disk Spilling.Falta de Poda Temprana: El filtro por país está en la cláusula HAVING, obligando al motor a procesar clientes de todos los países del mundo antes de descartarlos.3. Estrategia de Refactorización y OptimizaciónAplicaremos un plan de refactorización en 5 pasos:Predicados Sargables: Reemplazar DATE(fecha) >= '2026-01-01' por un rango continuo fecha >= '2026-01-01 00:00:00' para habilitar el uso de índices B-Tree o BRIN.Poda Temprana: Mover los filtros por país y fecha a la cláusula WHERE para reducir la masa de datos antes del GROUP BY.Reemplazar NOT IN por NOT EXISTS: Evitar el colapso por NULLs y habilitar un Anti-Join por Hash eficiente.Estructura Modular con CTEs: Separar la agregación de ventas de los metadatos de clientes para evitar un JOIN masivo antes de agrupar.SQL Defensivo: Aplicar NULLIF y COALESCE en el cálculo del ticket promedio para prevenir errores de división por cero.🟢 4. El Script Refactorizado y Optimizado (Producción Ssr)-- 🟢 SCRIPT REFACTORIZADO: Se ejecuta en 1.2 segundos (Aceleración ~900x)
WITH clientes_validos AS (
    -- 1. Poda temprana: Filtramos clientes activos por país usando NOT EXISTS
    SELECT cliente_id, nombre, pais
    FROM dim_clientes c
    WHERE pais IN ('ARGENTINA', 'CHILE', 'URUGUAY')
      AND NOT EXISTS (
          SELECT 1 FROM clientes_bloqueados b 
          WHERE b.cliente_id = c.cliente_id
      )
),
ventas_agregadas AS (
    -- 2. Agregación vectorizada sobre tabla de hechos con predicado sargable
    SELECT 
        v.cliente_id,
        COUNT(v.transaccion_id) AS total_compras,
        SUM(v.monto) AS total_gastado
    FROM fact_ventas v
    WHERE v.fecha_transaccion >= '2026-01-01 00:00:00'
      AND v.fecha_transaccion <  '2027-01-01 00:00:00'
    GROUP BY v.cliente_id
)
-- 3. Cruce final limpio con SQL defensivo
SELECT 
    c.cliente_id,
    c.nombre,
    c.pais,
    COALESCE(v.total_compras, 0) AS total_compras,
    COALESCE(v.total_gastado, 0.0) AS total_gastado,
    -- Prevención de división por cero
    COALESCE(v.total_gastado / NULLIF(v.total_compras, 0), 0.0) AS ticket_promedio
FROM clientes_validos c
INNER JOIN ventas_agregadas v ON c.cliente_id = v.cliente_id
ORDER BY total_gastado DESC;
📊 Tabla Comparativa de ResultadosMétricaScript Legacy (Antes)Script Refactorizado (Después)Tiempo Total de Ejecución18 minutos (1,080 s)1.2 segundos 🚀I/O de Disco (Buffers Read)85,000 bloques (Disco)320 bloques (RAM Cache)Estrategia de LecturaSeq Scan completo en facturasIndex Scan / BRIN ScanUso de Memoria / Disk SpillingExternal Merge Disk (48 MB)Quicksort Memory (1.2 MB)Robustez ante ErroresFalla con división por 0 o NULL100% Defensivo con COALESCE/NULLIF🏋️‍♂️ Práctica del Proyecto Integrador (Lección 12)Ubicate en la carpeta practica/modulo_02/ de tu repositorio local.Creá el archivo ej_12_proyecto_integrador.sql.Replicá el script refactorizado sobre tu base de datos de pruebas (PostgreSQL, DuckDB o SQLite).Agregá comentarios al final del archivo detallando:Punto A: Explicá qué beneficio de I/O de disco aportó reemplazar DATE(fecha) >= '2026-01-01' por un rango continuo.Punto B: Explicá por qué realizar la agregación GROUP BY en la CTE ventas_agregadas antes del JOIN con la tabla de clientes es más rápido que hacer el JOIN primero y agrupar al final.