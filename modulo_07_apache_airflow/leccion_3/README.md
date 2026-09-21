# 🚀 Lección 03: Idempotencia en Pipelines, Backfilling y Manejo de Fechas de Ejecución (logical_date)

En la Lección 02 aprendimos a construir DAGs defensivos utilizando la TaskFlow API, configurando reintentos con *exponential backoff*, *timeouts* y manejo de saltos elegantes con `AirflowSkipException`.

En esta lección abordaremos la regla de oro de la Ingeniería de Datos en producción: **la Idempotencia**.

Aprenderemos por qué un pipeline que no es idempotente duplica datos y arruina reportes financieros al reejecutarse, cómo gestionar el tiempo en Airflow mediante `logical_date` (evitando el error clásico de usar `datetime.now()`) y cómo realizar re-procesamientos históricos (**Backfilling**) de forma segura.

---

## 1. El Principio de Idempotencia en Pipelines de Datos

### ¿Qué es la Idempotencia?
Un proceso o pipeline de datos es **idempotente** si la ejecución del mismo código una vez o cien veces sobre el mismo conjunto de datos de entrada produce **exactamente el mismo resultado final en la base de datos**, sin duplicar filas ni distorsionar métricas.

```text
               EVALUACIÓN DE IDEMPOTENCIA EN INGESTA
                                   │
         ┌─────────────────────────┴─────────────────────────┐
         ▼                                                   ▼
 ANTI-PATRÓN NO IDEMPOTENTE                          PATRÓN IDEMPOTENTE
 • `INSERT INTO tabla SELECT ...`                   • `DELETE WHERE fecha = 'X' THEN INSERT`
 • Re-ejecutar duplica todos los registros          • `MERGE INTO / ON CONFLICT DO UPDATE`
 • Corrompe métricas en el Data Warehouse           • Re-ejecutar sobreescribe de forma limpia
```

### Anti-Patrón (No Idempotente):
```sql
-- ❌ SI ESTE SCRIPT SE RE-EJECUTA, DUPLICA TODAS LAS FILAS DE LA FECHA
INSERT INTO analytics.fact_ventas
SELECT * FROM raw.ventas_diarias WHERE fecha = '2026-03-15';
```
> Si la tarea falla a mitad de camino o si un ingeniero la vuelve a correr manualmente, la tabla `fact_ventas` tendrá el doble de ingresos para el 15 de marzo de 2026.

### Patrón Correcto (Idempotente):
```sql
-- 🟢 OPCIÓN A: Sobreescritura de Partición (Partition Overwrite / Delete-Insert)
DELETE FROM analytics.fact_ventas WHERE fecha_key = 20260315;
INSERT INTO analytics.fact_ventas 
SELECT * FROM raw.ventas_diarias WHERE fecha = '2026-03-15';

-- 🟢 OPCIÓN B: Upsert / Merge (SQL Nativo)
INSERT INTO analytics.fact_ventas (venta_id, monto, fecha_key)
VALUES (101, 150.00, 20260315)
ON CONFLICT (venta_id)
DO UPDATE SET monto = EXCLUDED.monto;
```

---

## 2. Manejo del Tiempo en Airflow: `logical_date` vs. `datetime.now()`

Un error crítico de principiante en Airflow es filtrar los datos de la fuente utilizando `datetime.now()` dentro del código Python de la tarea:

```python
# ❌ ERROR GRAVE DE ARQUITECTURA: Usa la hora del reloj del servidor
@task()
def extraer_ventas_ayer():
    # Si la tarea corre con retraso o se reejecuta la semana que viene,
    # 'ayer' será la fecha incorrecta y no la fecha analítica del DAG.
    fecha_proceso = datetime.now() - timedelta(days=1)
    consultar_api(fecha=fecha_proceso)
```

### El Concepto de `logical_date` (anteriormente `execution_date`)

Airflow opera sobre intervalos de tiempo cerrados. La `logical_date` representa el inicio del intervalo de datos que el DAG está procesando, **independientemente de la hora del reloj en la que la máquina esté ejecutando la tarea**.

```text
Intervalo de Datos (Data Interval):
┌────────────────────────────────────────────────────────┐
│  2026-03-01 00:00:00  ──────────►  2026-03-02 00:00:00 │
└────────────────────────────────────────────────────────┘
▲                                   ▲
logical_date                        Hora real en la que el
(o data_interval_start)             Scheduler ejecuta la tarea
```

* **`data_interval_start`:** Marca el inicio exacto del período de datos.
* **`data_interval_end`:** Marca el final del período de datos.

> ### 💡 Regla de Oro Ssr
> Toda consulta o extracción filtrada por fecha **DENTRO** de Airflow debe alimentarse de `logical_date` o `data_interval_start`. Nunca del reloj del sistema.

---

## 3. Re-procesamiento Histórico (Backfilling)

El **Backfilling** es la capacidad de ejecutar un DAG para un período de tiempo en el pasado (por ejemplo, re-procesar los últimos 6 meses de datos porque se descubrió un bug en la lógica de cálculo de impuestos).

### ¿Cómo funciona el Backfilling?
* Gracias a que el DAG está parametrizado con `logical_date`, Airflow puede "viajar en el tiempo" ejecutando una instancia de tarea (*Task Instance*) para cada día del pasado.
* Gracias a que las transformaciones son idempotentes, el re-procesamiento sobreescribe las particiones históricas en el Data Warehouse sin duplicar filas.

### Control de Carga Inicial: `catchup`
```python
@dag(
    dag_id='pipeline_ventas_diarias',
    start_date=datetime(2025, 1, 1), # Fecha de inicio histórica
    schedule='@daily',
    catchup=False # ⚠️ False: Descarta el backfill automático al activar el DAG.
                  # True: Ejecutará INMEDIATAMENTE una corrida por cada día desde 2025-01-01.
)
```

### Ejecución de Backfill desde la Terminal CLI:
Si `catchup=False`, podemos disparar un backfill controlado para un rango de fechas específico desde la terminal de Airflow:

```bash
# Ejecuta el DAG para todo el mes de enero de 2026 de forma ordenada
airflow dags backfill \
    --start-date 2026-01-01 \
    --end-date 2026-01-31 \
    pipeline_ventas_diarias
```

---

## 4. Código Completo de un DAG Idempotente con `logical_date`

```python
from datetime import datetime, timedelta
from airflow.decorators import dag, task

default_args = {
    'owner': 'data_engineer_ssr',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

@dag(
    dag_id='dag_idempotente_partition_overwrite_v1',
    default_args=default_args,
    start_date=datetime(2026, 1, 1),
    schedule='@daily',
    catchup=False,
    tags=['idempotency', 'logical_date', 'gold']
)
def pipeline_idempotente():

    # Al recibir ds (YYYY-MM-DD) o data_interval_start, parametrizamos la extracción
    @task(task_id='extraer_particion_diaria')
    def extraer_datos(ds: str = None) -> list[dict]:
        print(f"📅 Extrayendo datos para la fecha lógica del intervalo: {ds}")
        # Simulación de extracción parametrizada por fecha lógica
        return [
            {"venta_id": 801, "monto": 100.0, "fecha": ds},
            {"venta_id": 802, "monto": 250.0, "fecha": ds}
        ]

    # Carga Idempotente aplicando Delete-Insert en la base analítica
    @task(task_id='cargar_particion_idempotente')
    def cargar_data_warehouse(registros: list[dict], ds: str = None):
        fecha_key = ds.replace("-", "")  # Convertir '2026-03-15' en 20260315

        print(f"🧹 Paso 1: Borrando partición previa para fecha_key = {fecha_key} (Garantiza Idempotencia)")
        sql_delete = f"DELETE FROM analytics.fact_ventas WHERE fecha_key = {fecha_key};"
        print(f"   [SQL EXEC]: {sql_delete}")

        print(f"📥 Paso 2: Insertando {len(registros)} registros limpios en la partición...")
        sql_insert = f"INSERT INTO analytics.fact_ventas SELECT * FROM stage_ventas WHERE fecha = '{ds}';"
        print(f"   [SQL EXEC]: {sql_insert}")

    # Flujo de Ejecución enviando la macro de fecha 'ds'
    datos = extraer_datos()
    cargar_data_warehouse(datos)

dag_instance = pipeline_idempotente()
```

---

## 🏋️‍♂️ Práctica de la Lección 03

1. Ubicate en la carpeta `practica/modulo_07/` de tu repositorio local.
2. Creá el archivo `ej_03_idempotencia_backfill.py`.
3. Escribí un script Python que simule el impacto de re-ejecutar un proceso **NO idempotente** vs. un proceso **IDEMPOTENTE** con `logical_date`:

```python
import pandas as pd

# Base de Datos Simulada (Capa Gold / Fact Table)
fact_ventas_db = pd.DataFrame(columns=["venta_id", "monto", "fecha_key"])

# 1. Función NO Idempotente (Append Directo sin borrado ni dedup)
def Ingesta_No_Idempotente(lote: list[dict]):
    global fact_ventas_db
    df_nuevos = pd.DataFrame(lote)
    fact_ventas_db = pd.concat([fact_ventas_db, df_nuevos], ignore_index=True)

# 2. Función IDEMPOTENTE (Partition Overwrite por fecha_key)
def Ingesta_Idempotente(lote: list[dict], fecha_key: int):
    global fact_ventas_db
    # Paso 1: Eliminar la partición si ya existía
    fact_ventas_db = fact_ventas_db[fact_ventas_db["fecha_key"] != fecha_key]

    # Paso 2: Inserción limpia
    df_nuevos = pd.DataFrame(lote)
    fact_ventas_db = pd.concat([fact_ventas_db, df_nuevos], ignore_index=True)

# --- EJECUCIÓN DE PRUEBA ---
lote_dia_15 = [
    {"venta_id": 1, "monto": 100.0, "fecha_key": 20260315},
    {"venta_id": 2, "monto": 200.0, "fecha_key": 20260315}
]

print("=== PRUEBA 1: INGESTA NO IDEMPOTENTE (Se corre 2 veces el mismo día) ===")
Ingesta_No_Idempotente(lote_dia_15)
Ingesta_No_Idempotente(lote_dia_15)  # Re-ejecución por fallo
print(f"Filas en DB (Debería ser 2): {len(fact_ventas_db)}")
print(f"Monto Total en DB (Debería ser $300): ${fact_ventas_db['monto'].sum()}\n")

# Reiniciar DB
fact_ventas_db = pd.DataFrame(columns=["venta_id", "monto", "fecha_key"])

print("=== PRUEBA 2: INGESTA IDEMPOTENTE (Se corre 2 veces el mismo día) ===")
Ingesta_Idempotente(lote_dia_15, fecha_key=20260315)
Ingesta_Idempotente(lote_dia_15, fecha_key=20260315)  # Re-ejecución limpia
print(f"Filas en DB (Correcto): {len(fact_ventas_db)}")
print(f"Monto Total en DB (Correcto): ${fact_ventas_db['monto'].sum()}")
```

4. Agregá comentarios al final del archivo respondiendo:
   * **Consigna A:** ¿Por qué utilizar `datetime.now()` para filtrar la extracción de datos de un pipeline impide realizar un proceso de Backfilling sobre fechas pasadas?
   * **Consigna B:** En una base de datos relacional analítica (ej. PostgreSQL o Snowflake), ¿cuáles son los dos patrones SQL más comunes para lograr idempotencia al cargar datos?