# 🚀 Lección 03: Formatos de Tabla Abiertos (Open Table Formats): Delta Lake / Apache Iceberg (Transacciones ACID en Data Lakes)

En la Lección 02 comprendimos el funcionamiento interno de PySpark: la evaluación perezosa (*Lazy Evaluation*), la diferencia entre transformaciones Narrow y Wide (costo del *Shuffling*) y cómo el Catalyst Optimizer reescribe nuestro código para maximizar el rendimiento.

Sin embargo, cuando guardamos los datos transformados en un Data Lake tradicional utilizando archivos planos (como Parquet, ORC o CSV), tropezamos con limitaciones severas que durante años frustraron a los ingenieros de datos: falta de transacciones ACID, imposibilidad de hacer `UPDATE` o `DELETE` eficientes y fallos catastróficos por lecturas en sucio cuando un proceso escribe mientras otro lee.

En esta lección aprenderemos cómo la industria resolvió estas deficiencias creando la **Arquitectura Data Lakehouse** mediante los **Formatos de Tabla Abiertos (*Open Table Formats*)** como Delta Lake y Apache Iceberg.

---

## 1. El Problema del Data Lake Tradicional (Parquet Crudo)

Históricamente, los Data Lakes almacenaban archivos Parquet organizados en carpetas y particiones de un bucket S3 o HDFS:

```text
s3://my-data-lake/bronze/ventas/
├── año=2026/mes=03/dia=15/
│   ├── part-00001.parquet
│   └── part-00002.parquet
```

### ¿Por qué este modelo colapsa en producción Enterprise?
* **Sin Transacciones ACID:** Si un job de Spark falla escribiendo el archivo `part-00002.parquet` a la mitad, la carpeta queda en estado corrupto con datos parciales.
* **Sin Aislamiento de Lectura/Escritura:** Si un usuario ejecuta una consulta mientras un pipeline está escribiendo en el mismo directorio, la consulta fallará o devolverá datos incompletos (*Dirty Reads*).
* **Alto Costo de Modificación (No soporta `UPDATE` / `DELETE`):** Para modificar un solo registro dentro de un archivo Parquet de 1,000,000 de filas, había que reescribir la partición entera.
* **Degradación por *Small File Problem*:** Miles de pequeños archivos Parquet acumulados ralentizan drásticamente las lecturas debido al overhead del sistema de archivos.

---

## 2. La Revolución del Data Lakehouse y los Open Table Formats

La Arquitectura Data Lakehouse combina lo mejor de dos mundos:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        DATA LAKEHOUSE ARCHITECTURE                     │
├────────────────────────────────────────────────────────────────────────┤
│ 1. FLEXIBILIDAD Y BAJO COSTO DEL DATA LAKE (AWS S3, ADLS, GCP CS)     │
│    Almacena Petabytes de archivos abiertos (Parquet).                  │
├────────────────────────────────────────────────────────────────────────┤
│ 2. CONFIANZA Y CAPACIDADES DEL DATA WAREHOUSE (Garantías ACID)         │
│    Garantizadas por un OPEN TABLE FORMAT (Delta Lake / Apache Iceberg) │
└────────────────────────────────────────────────────────────────────────┘
```

### Los Líderes del Mercado:
* **Delta Lake:** Creado por Databricks, código abierto bajo la Linux Foundation.
* **Apache Iceberg:** Creado por Netflix, ampliamente adoptado por Snowflake, AWS y Cloudera.
* **Apache Hudi:** Creado por Uber, optimizado para ingestas de baja latencia/streaming.

---

## 3. ¿Cómo funciona la Magia de un Table Format? (`_delta_log`)

Los Formatos de Tabla Abiertos no cambian el formato físico de compresión subyacente (siguen usando Parquet), sino que agregan una capa de abstracción y gestión basada en un **Registro de Transacciones (*Transaction Log*)**.

En Delta Lake, esta capa es la carpeta `_delta_log/`:

```text
s3://my-lakehouse/silver/ventas/
├── _delta_log/
│   ├── 00000000000000000000.json  ──► Commit 1: Se crearon archivos A y B
│   ├── 00000000000000000001.json  ──► Commit 2: Se borró archivo A y se creó C
│   └── 00000000000000000001.checkpoint.parquet
├── part-00001-A.parquet (Obsoleto)
├── part-00002-B.parquet (Válido)
└── part-00003-C.parquet (Válido)
```

### Principio Operativo:
* **Control de Concurrencia Optimista (OCC):** Cada operación sobre la tabla genera un commit atómico ordenado en formato JSON (`0000.json`, `0001.json`).
* **Lectura Consistente:** El motor lector (Spark/Trino/Presto) lee primero el `_delta_log` para saber exactamente cuáles archivos Parquet están vigentes e ignora los archivos eliminados o en proceso de escritura.

---

## 4. Capacidades Avanzadas de un Data Lakehouse

### A. Transacciones ACID Atómicas
O bien la escritura de 10,000,000 de filas se completa e incluye al 100% en el `_delta_log`, o bien el job falla y la tabla permanece limpia como si nada se hubiera escrito.

### B. Viaje en el Tiempo (Time Travel)
Dado que los cambios se registran mediante commits atómicos y los archivos viejos no se borran inmediatamente, podés consultar el estado exacto del dataset en cualquier punto del pasado:

```python
# Consultar la tabla exactamente como estaba en la Versión 2
df_version2 = spark.read.format("delta") \
    .option("versionAsOf", 2) \
    .load("s3://my-lakehouse/silver/ventas/")

# Consultar la tabla como estaba en una Fecha/Hora específica
df_historico = spark.read.format("delta") \
    .option("timestampAsOf", "2026-03-01 10:00:00") \
    .load("s3://my-lakehouse/silver/ventas/")
```

### C. Operación DML Nativa: `MERGE INTO` (Upserts)
Permite actualizar registros existentes e insertar nuevos en una sola instrucción atómica:

```sql
MERGE INTO silver.ventas AS target
USING staging.nuevas_ventas AS source
ON target.venta_id = source.venta_id
WHEN MATCHED THEN
  UPDATE SET target.monto = source.monto, target.estado = source.estado
WHEN NOT MATCHED THEN
  INSERT (venta_id, monto, estado) VALUES (source.venta_id, source.monto, source.estado);
```

### D. Mantenimiento del Lakehouse: OPTIMIZE y VACUUM
* **`OPTIMIZE` (Compacción):** Toma miles de archivos Parquet pequeños (*Small Files*) y los combina en archivos grandes de tamaño óptimo (~1 GB).
* **`VACUUM`:** Elimina físicamente del almacenamiento en la nube los archivos Parquet obsoletos que tienen más de $N$ días de antigüedad (por defecto 7 días).

---

## 🏋️‍♂️ Práctica de la Lección 03

1. Ubicate en la carpeta `practica/modulo_09/` de tu repositorio local.
2. Creá el archivo `ej_03_delta_lake_lakehouse.py`.
3. Escribí un script Python que simule el Registro de Transacciones (`_delta_log`), la ejecución de un `MERGE INTO` (Upsert) y la funcionalidad de *Time Travel*:

```python
import json
import time
from typing import List, Dict

class DeltaTableSimulator:
    def __init__(self, table_name: str):
        self.table_name = table_name
        self.version = 0
        self.delta_log = []       # Registro de transacciones JSON
        self.current_state = {}   # Key: venta_id, Value: dict record

    def _commit(self, operation: str, affected_records: int):
        self.version += 1
        commit_entry = {
            "version": self.version,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "operation": operation,
            "records_count": len(self.current_state),
            "state_snapshot": dict(self.current_state)  # Snapshot para Time Travel
        }
        self.delta_log.append(commit_entry)
        print(f"💾 [DELTA LOG] Commit v{self.version} registrado | Op: {operation} | Total Filas: {len(self.current_state)}")

    def insert(self, records: List[Dict]):
        for r in records:
            self.current_state[r["venta_id"]] = r
        self._commit("WRITE / INSERT", len(records))

    def merge_upsert(self, updates: List[Dict]):
        print(f"\n🔄 [MERGE INTO] Ejecutando Upsert de {len(updates)} registros...")
        for u in updates:
            # Si existe actualiza, si no existe inserta
            self.current_state[u["venta_id"]] = u
        self._commit("MERGE (UPSERT)", len(updates))

    def time_travel(self, version: int) -> List[Dict]:
        print(f"\n⏳ [TIME TRAVEL] Consultando '{self.table_name}' en la Versión v{version}...")
        for commit in self.delta_log:
            if commit["version"] == version:
                snapshot = commit["state_snapshot"]
                return list(snapshot.values())
        print(f"❌ Versión v{version} no encontrada en el _delta_log.")
        return []

# --- PRUEBA DE EJECUCIÓN DEL LAKEHOUSE ---
delta_table = DeltaTableSimulator("silver_fact_ventas")

# 1. Carga Inicial (Commit v1)
lote_inicial = [
    {"venta_id": 101, "monto_usd": 150.0, "estado": "PENDIENTE"},
    {"venta_id": 102, "monto_usd": 80.0,  "estado": "APROBADO"}
]
delta_table.insert(lote_inicial)

# 2. Carga con Actualizaciones (Commit v2 via MERGE INTO)
lote_upsert = [
    {"venta_id": 101, "monto_usd": 150.0, "estado": "APROBADO"},  # UPDATE: Cambió estado
    {"venta_id": 103, "monto_usd": 210.0, "estado": "APROBADO"}   # INSERT: Nueva venta
]
delta_table.merge_upsert(lote_upsert)

# 3. Consulta de Estado Actual (v2)
print(f"\n📊 Estado Actual de la Tabla (v2): {list(delta_table.current_state.values())}")

# 4. Viaje en el Tiempo (Time Travel a la v1)
estado_v1 = delta_table.time_travel(version=1)
print(f"📜 Snapshot Recuperado de la v1: {estado_v1}")
```

4. Agregá comentarios al final del archivo respondiendo:
   * **Consigna A:** Explica cómo la carpeta de registro de transacciones (`_delta_log` en Delta Lake o archivos de manifiesto en Apache Iceberg) permite garantizar transacciones ACID e impedir lecturas en sucio sobre almacenamiento de objetos de bajo costo (ej. AWS S3).
   * **Consigna B:** ¿En qué consiste la funcionalidad de Time Travel en un Data Lakehouse y en qué escenarios reales de producción (ej. auditorías, bugs de procesamiento) resulta crítica?