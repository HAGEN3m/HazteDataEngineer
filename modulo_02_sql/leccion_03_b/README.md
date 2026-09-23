# 🐘 Lección 03.B: Database Internals — Storage Engines, Buffer Pool, WAL y MVCC

&gt; **Propósito**: Comprender la arquitectura física interna de los motores de bases de datos relacionales (CPUs, discos, páginas de memoria, almacenamiento WAL y control de concurrencia multiversión) para diagnosticar bloqueos, optimizar el uso de RAM/disco y prevenir degradaciones por *table bloat*.

---

## 📌 1\. Anatomía Física de una Base de Datos Relacional

A nivel de sistema operativo, una base de datos no es una "hoja de cálculo gigante"; es un conjunto de archivos organizados en bloques discretos de memoria llamados **Páginas** (usualmente de 8 KB en PostgreSQL).

```
         MEMORIA RAM (Buffer Pool)                   DISCO RÍGIDO (Storage)
   ┌──────────────────────────────────┐        ┌──────────────────────────────┐
   │ Páginas Calientes (Hot Pages)    │ &lt;----&gt; │ Páginas de Datos (8 KB)      │
   │ [ P1 ]  [ P2 ]  [ P3 ]  [ P4 ]   │        │ [ Archivo Heap de la Tabla ] │
   └──────────────────────────────────┘        └──────────────────────────────┘
                    │
                    ▼ (Modificaciones)
   ┌──────────────────────────────────┐        ┌──────────────────────────────┐
   │ WAL Buffer (Transacciones)       │ ----&gt;  │ WAL Logs (write-ahead log)   │
   └──────────────────────────────────┘        └──────────────────────────────┘

```

### Conceptos Clave de Almacenamiento:

1. **Archivo Heap (Heap File)**: Archivo sin orden explícito donde el motor inserta las filas (*tuples*) a medida que llegan en las páginas disponibles.
2. **Página de Datos (Page / Block)**: Estructura fija de 8 KB que contiene metadatos de encabezado (*Page Header*), un arreglo de punteros a filas (*Line Pointers*) y el contenido de las tuplas.
3. **Overhead de Tupla (*Tuple Overhead*)**: Cada fila almacenada contiene metadatos ocultos (`xmin`, `xmax`, `ctid`). En PostgreSQL, esto añade cerca de 23 bytes por fila.

---

## 🔬 2\. El Buffer Pool y Gestión de Caché de Disco

Leer datos directamente desde un disco SSD o HDD es entre **100 y 1.000 veces más lento** que leer desde la memoria RAM. Para mitigar esta latencia, los motores utilizan el **Buffer Pool**.

* **Buffer Hit**: La página de 8 KB requerida por la consulta SQL ya se encuentra en la RAM.
* **Buffer Miss**: La página no está en RAM. El motor realiza una lectura I/O de disco, la carga en el Buffer Pool y luego devuelve la fila.

### Algoritmo de Reemplazo (Clock / LRU):

Cuando el Buffer Pool se llena, el motor aplica un algoritmo (*Least Recently Used*) para expulsar las páginas "frías" (menos usadas) a disco y liberar espacio para las nuevas consultas.

---

## ⚡ 3\. Garantía ACID y Write-Ahead Logging (WAL)

Para cumplir con la propiedad de **Durabilidad** del acrónimo ACID (*Atomicity, Consistency, Isolation, Durability*), la base de datos debe asegurar que una transacción confirmada (`COMMIT`) no se pierda incluso si hay un corte de luz repentino.

### ¿Cómo funciona el WAL (Write-Ahead Log)?

Escribir de nuevo toda una página de 8 KB en el archivo Heap por cada pequeña modificación es demasiado costoso en I/O.

En su lugar, el motor aplica la **regla sagrada de las bases de datos**:

&gt; *"El registro de la modificación debe escribirse secuencialmente en el log de transacciones (WAL) en disco ANTES de que la página modificada en RAM sea marcada como confirmada."*

```
1. UPDATE usuario SET saldo = 500  ──&gt; 2. Escribir en WAL Log (Disco)  ──&gt; 3. Responder 'COMMIT OK' al cliente
                                                                             │
                                                                             ▼ (En segundo plano)
                                                                   4. Flush de la página a Heap

```

Si el servidor colapsa, al reiniciar, el motor lee el archivo WAL y reejecuta (*Redo*) cualquier cambio confirmado que no haya llegado a guardarse físicamente en el archivo Heap de la tabla.

---

## 🛠️ 4\. Concurrencia Multiversión (MVCC) y el Problema del Table Bloat

Para permitir que cientos de usuarios lean y escriban simultáneamente sin bloquearse entre sí (*"Los lectores no bloquean a los escritores y los escritores no bloquean a los lectores"*), motores como PostgreSQL utilizan **MVCC (Multi-Version Concurrency Control)**.

### Mecanismo Interno de MVCC:

Cuando ejecutas un `UPDATE` o `DELETE`, el motor **no borra ni sobreescribe** la fila físicamente en la página:

* **`UPDATE`**: Inserta una nueva versión de la tupla y marca la versión anterior como caducada fijando su campo invisible `xmax`.
* **`DELETE`**: Marca la tupla existente como muerta fijando su `xmax`.

```
Estado de la Página tras varios UPDATEs:
┌───────────────────────────────────────────────────────────┐
│ Tupla 1 (v1) [xmin: 100, xmax: 105]  --&gt; 💀 Tupla Muerta   │
│ Tupla 1 (v2) [xmin: 105, xmax: 110]  --&gt; 💀 Tupla Muerta   │
│ Tupla 1 (v3) [xmin: 110, xmax: 0  ]  --&gt; 🟢 Tupla Viva    │
└───────────────────────────────────────────────────────────┘

```

### El Fenómeno del Table Bloat y el Proceso `VACUUM`

Las tuplas muertas ocupan espacio físico en el disco y en las páginas del Buffer Pool, degradando la velocidad de las consultas (`Seq Scan`). Este desperdicio de espacio se conoce como **Table Bloat**.

* **`Autovacuum`**: Proceso en segundo plano que escanea páginas en busca de tuplas muertas y marca el espacio como "reutilizable" para futuros `INSERT`.
* **`VACUUM FULL`**: Reescribe físicamente toda la tabla compactándola en un nuevo archivo de disco (requiere un bloqueo exclusivo de la tabla).

---

## 🏋️‍♂️ Ejercicio Práctico Hands-On: Inspección de Páginas y Tuplas Muertas

Crea un script en PostgreSQL para medir la cantidad de espacio desperdiciado por tuplas muertas tras ejecuciones masivas de `UPDATE`:

```
-- 1. Crear extensión para inspeccionar estadísticas internas
CREATE EXTENSION IF NOT EXISTS pgstattuple;

-- 2. Crear tabla sintética de prueba
CREATE TABLE test_bloat (
    id SERIAL PRIMARY KEY,
    payload TEXT,
    contador INT
);

-- 3. Insertar 100,000 filas
INSERT INTO test_bloat (payload, contador)
SELECT 'Dato de prueba ' || i, i
FROM generate_series(1, 100000) AS i;

-- 4. Simular carga de producción: 5 updates sobre todo el dataset
UPDATE test_bloat SET contador = contador + 1;
UPDATE test_bloat SET contador = contador + 1;
UPDATE test_bloat SET contador = contador + 1;

-- 5. Medir el estado de bloat y tuplas muertas
SELECT
    table_len AS tamaño_total_bytes,
    tuple_count AS tuplas_vivas,
    dead_tuple_count AS tuplas_muertas,
    ROUND(dead_tuple_percent, 2) AS porcentaje_muerto
FROM pgstattuple('test_bloat');

-- 6. Limpieza atómica del espacio marcado
VACUUM test_bloat;

```

---

## 🧠 Checkpoint de Autoevaluación

1. ¿Cuál es el tamaño de página estándar por defecto en PostgreSQL y qué información contiene su encabezado?
2. ¿Por qué el principio de Write-Ahead Logging (WAL) permite confirmar transacciones de forma segura sin escribir inmediatamente todo el archivo Heap en disco?
3. ¿Cómo gestiona el motor MVCC los `UPDATE` y `DELETE` internamente y qué consecuencia tiene sobre el consumo de almacenamiento (*Table Bloat*)?
4. ¿Cuál es la diferencia operativa entre ejecutar un `VACUUM` ordinario y un `VACUUM FULL` en una base de datos de producción?