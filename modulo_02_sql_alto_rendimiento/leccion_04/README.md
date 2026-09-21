# 🐘 Lección 04: Indexación Avanzada en PostgreSQL (`B-Tree`, `Hash`, `GIN`, `BRIN`), Índices Compuestos e Índices Parciales

En la **Lección 03** aprendimos a diagnosticar la lectura de datos con `EXPLAIN ANALYZE` y vimos que un `Seq Scan` (escaneo secuencial completo) sobre tablas gigantes es el enemigo principal del rendimiento.

Crear índices a ciegas (`CREATE INDEX` en cada columna) es un error común que penaliza severamente las escrituras (`INSERT`, `UPDATE`, `DELETE`) y satura el uso de disco. Un **Data Engineer Ssr** debe seleccionar la **estructura de datos interna** adecuada para cada tipo de columna y patrón de consulta.

En esta lección analizaremos los 4 tipos de índices principales en PostgreSQL, las reglas de índices compuestos y la optimización extrema con índices parciales.

---

## 1\. Tipos de Índices en PostgreSQL y sus Estructuras Internas

### A. `B-Tree` (Balanced Tree — El Índice Por Defecto)

Es una estructura en árbol auto-balanceado que mantiene los datos ordenados.

* **Operadores compatibles**: `=`, `&lt;`, `&lt;=`, `&gt;`, `&gt;=`, `BETWEEN`, `IN`, `LIKE 'prefijo%'`.
* **Ventajas**: Sirve para búsquedas puntuales, rangos y satisface la cláusula `ORDER BY` sin necesidad de un nodo `Sort` en memoria RAM.
* **Caso de Uso**: Claves primarias, claves foráneas, columnas numéricas y fechas en tablas OLTP/OLAP tradicionales.

### B. `Hash`

Construye una tabla hash interna mapeando la clave al puntero físico de la fila (`TID`).

* **Operadores compatibles**: Únicamente igualdad pura (`=`).
* **Ventajas**: Ocupa ligeramente menos espacio que un B-Tree para cadenas de texto muy largas cuando solo se busca igualdad exacta.
* **Limitación**: No sirve para búsquedas por rango (`&lt;`, `&gt;`), ni para `ORDER BY`, ni para `LIKE`.

### C. `GIN` (Generalized Inverted Index — Índice Invertido Generalizado)

Mapea elementos internos (*sub-elementos*) hacia las filas que los contienen. En lugar de indexar la fila completa, indexa cada componente individual.

* **Operadores compatibles**: `@&gt;` (contiene), `?` (existe clave), `@@` (búsqueda de texto completo).
* **Caso de Uso**: Columnas tipo **JSONB**, arrays (`INT[]`, `TEXT[]`) y búsqueda de texto (*Full Text Search* / `tsvector`).

```
-- Ejemplo: Índice GIN sobre un documento JSONB
CREATE INDEX idx_ventas_payload_gin ON fact_ventas USING GIN (payload_jsonb);

-- Consulta que aprovecha el índice GIN al buscar dentro del JSON:
SELECT * FROM fact_ventas 
WHERE payload_jsonb @&gt; '{"cliente": {"tipo": "VIP"}}';

```

### D. `BRIN` (Block Range Index — Índice de Rango de Bloques)

Guarda únicamente los valores **mínimo y máximo** de una columna por cada bloque físico de páginas en disco (por defecto, rangos de 128 páginas = 1 MB).

* **Ventajas**: **Ocupa un 99% menos espacio que un B-Tree**. Un índice B-Tree de 1 GB puede reducirse a apenas unos pocos Kilobytes con BRIN.
* **Requisito Crítico**: Los datos en disco **deben estar físicamente ordenados** o altamente correlacionados con la columna (ej. tablas de eventos *append-only* ordenadas por `fecha_registro` o IDs autoincrementales).

```
-- Ejemplo: Índice BRIN sobre 500 millones de logs de auditoría por fecha
CREATE INDEX idx_logs_fecha_brin ON logs_servidor USING BRIN (fecha_evento);

```

---

## 2\. Índices Compuestos (Multicolumna) y la Regla del Prefijo Izquierdo

Un índice compuesto agrupa múltiples columnas dentro de una misma estructura B-Tree:

```
CREATE INDEX idx_ventas_region_fecha ON fact_ventas (region, fecha_transaccion);

```

### 🚨 La Regla del Prefijo Izquierdo (*Leftmost Prefix Rule*)

El orden de las columnas en el índice define cómo se puede navegar la estructura:

* 🟢 **Usa el índice**: `WHERE region = 'NORTE' AND fecha_transaccion = '2026-01-15'`
* 🟢 **Usa el índice**: `WHERE region = 'NORTE'` (es el prefijo izquierdo).
* 🔴 **NO usa el índice**: `WHERE fecha_transaccion = '2026-01-15'` (la primera columna `region` fue omitida).

---

## 3\. Índices Parciales (*Partial Indexes*)

En arquitecturas analíticas es común tener columnas donde el 95% de los datos corresponden a un estado final (ejemplo: `estado = 'PROCESADO'`) y solo un 5% a estados activos o anómalos (`estado = 'PENDIENTE'` o `estado = 'ERROR'`).

Indexar el 100% de la tabla para buscar solo el 5% es un desperdicio masivo de RAM y disco. Un **Índice Parcial** incluye una cláusula `WHERE` dentro de su propia definición:

```
-- Crea un índice extremadamente pequeño que solo indexa los registros con errores
CREATE INDEX idx_ventas_pendientes 
ON fact_ventas (fecha_transaccion) 
WHERE estado = 'PENDIENTE_REINTENTO';

-- La consulta aprovechará el índice solo si coincide la condición exacta del WHERE
SELECT * FROM fact_ventas 
WHERE estado = 'PENDIENTE_REINTENTO' 
  AND fecha_transaccion &gt;= '2026-01-01';

```

---

## 📊 Matriz Comparativa de Tipos de Índices

| Tipo de Índice | Estructura       | Tamaño en Disco          | Búsqueda por Rango | Caso de Uso Principal                                    |
| -------------- | ---------------- | ------------------------ | ------------------ | -------------------------------------------------------- |
| **B-Tree**     | Árbol balanceado | Medio / Alto             | 🟢 Sí              | Claves primarias, IDs, fechas, columnas generales.       |
| **Hash**       | Tabla Hash       | Medio                    | 🔴 No              | Igualdad exacta en cadenas de texto muy largas.          |
| **GIN**        | Índice Invertido | Alto                     | 🔴 No              | `JSONB`, Arrays, Búsqueda de texto (*Search*).           |
| **BRIN**       | Rangos Min/Max   | **Ultra Pequeño** (&lt; 1%) | 🟢 Sí              | Tablas append-only ordenadas por tiempo (*Time-Series*). |

---

## 🏋️‍♂️ Práctica de la Lección 04

1. Ubicate en la carpeta `practica/modulo_02/` de tu repositorio local.
2. Creá el archivo `ej_04_indexacion_avanzada.sql`.
3. Escribí un script SQL para PostgreSQL que evalúe y compare estrategias de indexación sobre un dataset sintético:

```
-- 1. Crear tabla de eventos con payload JSONB y fecha
CREATE TABLE eventos_plataforma (
    id BIGSERIAL PRIMARY KEY,
    fecha_evento TIMESTAMP NOT NULL,
    estado VARCHAR(20) NOT NULL,
    metadata JSONB
);

-- 2. Insertar 100,000 eventos de prueba
INSERT INTO eventos_plataforma (fecha_evento, estado, metadata)
SELECT 
    NOW() - (i || ' minutes')::INTERVAL,
    CASE WHEN i % 100 = 0 THEN 'ERROR' ELSE 'OK' END,
    jsonb_build_object('dispositivo', CASE WHEN i % 2 = 0 THEN 'MOBILE' ELSE 'DESKTOP' END, 'version', '2.4.1')
FROM generate_series(1, 100000) AS i;

```

1. Completá el script implementando y diagnosticando con `EXPLAIN (ANALYZE, BUFFERS)`:
  * **Caso A (Índice GIN)**: Creá un índice GIN sobre la columna `metadata` y escribí una consulta que busque eventos realizados desde dispositivos `'MOBILE'`.
  * **Caso B (Índice Parcial)**: Creá un índice parcial sobre `fecha_evento` que indexe **únicamente** las filas donde `estado = 'ERROR'`.
  * **Consigna**: Diagnosticá la diferencia en tamaño en disco de ambos índices usando la función `pg_size_pretty(pg_relation_size('nombre_indice'))`.