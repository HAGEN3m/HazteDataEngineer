# 🐘 Lección 02: Algoritmos Internos de JOIN a Bajo Nivel (Nested Loop, Hash Join, Merge Join) y Complejidad $O(N)$

En el procesamiento de datos analíticos, las operaciones de cruce (JOINs) representan la mayor carga computacional en memoria y CPU. Cuando escribís `FROM ventas v JOIN clientes c ON v.cliente_id = c.id`, el motor de la base de datos no aplica una receta mágica única: el Optimizador de Consultas analiza el tamaño de las tablas, los índices disponibles y la memoria RAM reservada (`work_mem` en PostgreSQL) para seleccionar uno de los tres algoritmos físicos de cruce.

Como Data Engineer Ssr, conocer estos tres algoritmos a bajo nivel te permite entender por qué una consulta tarda 2 milisegundos o se cuelga durante 20 minutos, y cómo ajustar tus índices o estructuras para forzar el algoritmo óptimo.

---

## 1. Nested Loop Join (Bucle Anidado)

Es el algoritmo más intuitivo y equivale a un bucle `for` anidado en Python.

### ¿Cómo funciona?
* Toma una tabla como externa (**Outer Table / Driving Table**).
* Para cada fila de la tabla externa, escanea la tabla interna (**Inner Table**) buscando coincidencias.

```text
FOR cada fila R1 en Tabla_Externa (M filas):
    FOR cada fila R2 en Tabla_Interna (N filas):
        IF R1.clave == R2.clave:
            EMITIR_FILA(R1, R2)
```

### Complejidad Computacional y Rendimiento:
* **Sin Índice:** Complejidad $\mathcal{O}(M \times N)$. Si tenés 10,000 filas en ambas tablas, realizará 100,000,000 comparaciones.
* **Con Índice B-Tree en la Tabla Interna:** Complejidad $\mathcal{O}(M \log N)$. Para cada fila de la tabla externa, realiza una búsqueda logarítmica ultra rápida en el índice de la tabla interna.

### ¿Cuándo lo elige el motor?
* Una de las tablas es muy pequeña (ej. menos de 100 filas) y la otra tabla tiene un índice B-Tree en la clave del JOIN.
* **Consumo de Memoria:** Mínimo $\mathcal{O}(1)$.

---

## 2. Hash Join (Unión por Hash)

Es el caballo de batalla del procesamiento de datos en Data Warehouses (OLAP) y consultas analíticas masivas.

### ¿Cómo funciona? Consta de 2 fases estrictas:
* **Fase 1: Construcción (Build Phase):** El motor lee la tabla más pequeña (Build Input), aplica una función hash sobre la clave del JOIN y construye una Tabla Hash en memoria RAM (`work_mem`).
* **Fase 2: Sondeo (Probe Phase):** El motor lee la tabla más grande (Probe Input) fila por fila, calcula el valor hash de la clave y busca instantáneamente en tiempo constante $\mathcal{O}(1)$ si existe coincidencia en la Tabla Hash.

```text
FASE BUILD (En RAM):
    FOR cada fila R1 en Tabla_Pequenia:
        hash_bucket = HASH(R1.clave)
        INSERTAR_EN_HASH_TABLE(hash_bucket, R1)

FASE PROBE:
    FOR cada fila R2 en Tabla_Grande:
        hash_bucket = HASH(R2.clave)
        IF BUSCAR_EN_HASH_TABLE(hash_bucket):
            EMITIR_FILA(R1, R2)
```

### Complejidad Computacional y Riesgos:
* **Complejidad temporal:** $\mathcal{O}(M + N)$ (Lineal).
* **Consumo de Memoria:** $\mathcal{O}(M)$ (Requiere cargar toda la tabla pequeña en RAM).
* 🚨 **Riesgo de Disk Spilling:** Si la Tabla Hash supera el límite de memoria asignado (`work_mem`), PostgreSQL divide la tabla hash en lotes y los escribe en disco (*Batches / Spill to Disk*), lo que degrada drásticamente el rendimiento por la latencia de I/O de disco.

---

## 3. Merge Join (Unión por Mezcla)

Es el algoritmo más eficiente cuando los datos ya se encuentran previamente ordenados por la clave del JOIN.

### ¿Cómo funciona?
* Requiere que ambas tablas estén ordenadas por la clave de cruce.
* Mantiene dos punteros paralelos y avanza sobre ambas tablas en una sola pasada, de menor a mayor.

```text
p1 = inicio(Tabla_A_Ordenada)
p2 = inicio(Tabla_B_Ordenada)

WHILE p1 != fin AND p2 != fin:
    IF p1.clave == p2.clave:
        EMITIR_FILA(p1, p2)
        AVANZAR(p1)
    ELSE IF p1.clave < p2.clave:
        AVANZAR(p1)
    ELSE:
        AVANZAR(p2)
```

### Complejidad Computacional y Rendimiento:
* **Si los datos YA están ordenados (por índice B-Tree o ORDER BY previo):** Complejidad $\mathcal{O}(M + N)$. Es el JOIN más rápido posible.
* **Si NO están ordenados (Sort Merge Join):** Debe ordenar ambas tablas primero, resultando en $\mathcal{O}(M \log M + N \log N)$.
* **Consumo de Memoria:** Muy bajo.

---

## 📊 Matriz Comparativa de Algoritmos de JOIN

| Criterio | Nested Loop Join | Hash Join | Merge Join |
| :--- | :--- | :--- | :--- |
| **Requisito de Orden** | Ninguno | Ninguno | Obligatorio por clave de JOIN |
| **Uso de Memoria RAM** | Casi nulo $\mathcal{O}(1)$ | Alto (Satura si falta `work_mem`) | Bajo |
| **Complejidad Temporal** | $\mathcal{O}(M \times N)$ o $\mathcal{O}(M \log N)$ | $\mathcal{O}(M + N)$ | $\mathcal{O}(M + N)$ (si está ordenado) |
| **Caso de Uso Ideal** | Filtros OLTP que traen pocos registros con índice | Tablas grandes no ordenadas en OLAP / DW | Tablas masivas con índices B-Tree o ya ordenadas |

---

## 🏋️‍♂️ Práctica de la Lección 02

1. Ubicate en la carpeta `practica/modulo_02/` de tu repositorio local.
2. Creá el archivo `ej_02_join_algorithms.sql`.
3. Escribí un script SQL (compatible con PostgreSQL) que simule la creación de dos tablas de prueba y evalúe la estrategia de JOIN:

```sql
-- 1. Crear tabla de Dimension Clientes (pequeña)
CREATE TABLE dim_clientes (
    cliente_id INT PRIMARY KEY,
    nombre VARCHAR(50),
    pais VARCHAR(10)
);

-- 2. Crear tabla de Hechos Ventas (grande)
CREATE TABLE fact_ventas (
    transaccion_id BIGINT,
    cliente_id INT,
    monto DECIMAL(10,2),
    fecha DATE
);

-- 3. Consulta de Cruce Analítico
SELECT c.pais, SUM(v.monto) AS total_pais
FROM fact_ventas v
JOIN dim_clientes c ON v.cliente_id = c.cliente_id
GROUP BY c.pais;
```

4. Agregá comentarios explicativos en el archivo SQL respondiendo:
   * **Pregunta A:** Si `dim_clientes` tiene 1,000 filas y `fact_ventas` tiene 10,000,000 de filas sin índices en `v.cliente_id`, ¿cuál de los 3 algoritmos seleccionará PostgreSQL por defecto y por qué?
   * **Pregunta B:** ¿Qué ocurriría si `dim_clientes` crece a 5,000,000 de filas y la RAM asignada (`work_mem`) es de solo 4 MB? ¿Qué efecto de degradación de rendimiento (*Disk Spilling*) se producirá?