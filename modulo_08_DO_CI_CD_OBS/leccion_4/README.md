# 🚀 Lección 04: Observabilidad de Datos: Métricas de Frescura, Volumen, Esquema y Linaje

En la Lección 03 aprendimos a implementar **Data Quality Gates** in-pipeline y a monitorear el **Data Drift** (deriva estadística) mediante métricas como el *Z-Score* para evitar que lotes anómalos contaminen las capas analíticas.

Sin embargo, a medida que una plataforma de datos crece y administra cientos de pipelines, tablas y modelos de dbt, surge un interrogante operativo clave: **¿Cómo sabemos si todo el ecosistema de datos está "sano" en tiempo real sin tener que revisar cada pipeline de forma individual?**

En esta lección aprenderemos sobre la **Observabilidad de Datos (*Data Observability*)**, la disciplina que nos permite monitorear de forma pasiva e inteligente la salud de la plataforma basándonos en sus 5 pilares fundamentales.

---

## 1. Monitoreo Tradicional vs. Observabilidad de Datos

En el pasado, los equipos de operaciones solo monitoreaban la infraestructura física:

```text
MONITOREO TRADICIONAL DE INFRAESTRUCTURA:
[ CPU Usage: 25% ]  ──  [ Memory RAM: 4GB / 16GB ]  ──  [ Status: RUNNING (200 OK) ]
```

El servidor está encendido y Airflow muestra todas sus tareas en verde (`SUCCESS`). Sin embargo, los datos dentro de las tablas pueden estar vacíos, desactualizados desde hace 3 días o con esquemas corruptos.

La Observabilidad de Datos va más allá de saber si un script corrió; utiliza telemetría avanzada para responder preguntas críticas de negocio:
* ¿Los datos de la junta directiva de esta mañana están actualizados?
* ¿Por qué la tabla de hechos recibió la mitad de las filas habituales hoy?
* Si modifico la columna `cliente_id` en la capa Silver, ¿qué tableros de PowerBI o modelos de ML colapsarán?

---

## 2. Los 5 Pilares de la Observabilidad de Datos

La industria ha estandarizado la salud de los datos en 5 pilares interactivos:

```text
                         LOS 5 PILARES DE LA OBSERVABILIDAD
                                         │
    ┌────────────────┬───────────────────┼───────────────────┬────────────────┐
    ▼                ▼                   ▼                   ▼                ▼
1. FRESCURA      2. VOLUMEN          3. ESQUEMA          4. CALIDAD       5. LINAJE
(Freshness)       (Volume)            (Schema)            (Quality)        (Lineage)
¿Cuándo se       ¿Cuántos            ¿Cambiaron          ¿Los datos       ¿De dónde vienen
actualizó el     registros llegaron  las columnas o      son válidos      y a dónde van
dato por última  respecto a la       tipos respecto al   estadística-     estos datos?
vez?             media histórica?    contrato?           mente?
```

### 1. Frescura (*Data Freshness / Latency*)
Mide la antigüedad de los datos en relación con las expectativas de negocio (SLAs).
* **Indicador:** `NOW() - MAX(fecha_transaccion)`
* **Escenario de Falla:** Un pipeline silencioso de Airflow no falló, pero la API de origen no entregó datos nuevos. La tabla `fact_ventas` lleva 24 horas sin actualizarse.

### 2. Volumen (*Data Volume / Completeness*)
Monitorea si la cantidad de registros procesados en cada carga se encuentra dentro de los límites estadísticos esperados según la tendencia histórica.
* **Indicador:** Ratio de volumen actual vs. promedio de los últimos 30 días.
* **Escenario de Falla:** Normalmente cargamos 100,000 transacciones diarias. Hoy se cargaron solo 1,200 filas debido a un filtro incorrecto en la extracción.

### 3. Esquema (*Schema Drift & Integrity*)
Rastrea en tiempo real cualquier cambio en la estructura técnica de las tablas o archivos (columnas agregadas, eliminadas, renombradas o cambios en tipos de datos).
* **Indicador:** Auditoría contra el catálogo de metadatos o Data Contract.
* **Escenario de Falla:** Una columna `monto` cambió de `FLOAT` a `VARCHAR` en la base OLTP de origen.

### 4. Calidad y Distribución (*Data Quality & Drift*)
Monitorea el porcentaje de nulos, valores duplicados y la deriva estadística de las variables numéricas y categóricas (como vimos en la Lección 03 con *Z-Score*).

### 5. Linaje (*Data Lineage*)
Mapea la cadena de dependencias completa desde el sistema de origen (API/OLTP), pasando por las capas Medallón (Bronze $\rightarrow$ Silver $\rightarrow$ Gold), hasta el reporte o modelo consumido por el usuario final.
* **Utilidad:** Análisis de impacto (*Impact Analysis*) y rastreo de causa raíz (*Root Cause Analysis*).

---

## 3. Acuerdos de Nivel de Servicio de Datos (SLAs y SLOs)

Un equipo de datos Ssr/Senior no gestiona la observabilidad a "ojo"; define métricas formales con el negocio:

* **SLA (*Service Level Agreement*):** El compromiso contractual formal con los usuarios de negocio.
  * *Ejemplo:* "La tabla `gold_ventas_diarias` estará disponible todos los días antes de las 07:00 AM con datos del día anterior."
* **SLO (*Service Level Objective*):** La meta técnica interna que el equipo de datos establece para no violar el SLA.
  * *Ejemplo:* "El 99.5% de los días, la frescura de la tabla `gold_ventas_diarias` debe ser menor a 4 horas."

---

## 4. Implementación en Python: Monitor de Observabilidad de Datos

A continuación se muestra un script que actúa como un Colector de Observabilidad (*Data Observability Engine*) que audita la frescura, el volumen y la integridad del esquema sobre una base de datos:

```python
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

class DataObservabilityEngine:
    def __init__(self, expected_schema: dict, expected_avg_volume: int):
        self.expected_schema = expected_schema
        self.expected_avg_volume = expected_avg_volume

    def audit_table(self, df: pd.DataFrame, timestamp_col: str) -> dict:
        telemetry = {
            "timestamp_check": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "freshness_status": "OK",
            "volume_status": "OK",
            "schema_status": "OK",
            "details": []
        }

        # 1. PILAR FRESCURA (Max Timestamp)
        if not df.empty and timestamp_col in df.columns:
            max_date = pd.to_datetime(df[timestamp_col]).max()
            hours_lag = (datetime.now() - max_date).total_seconds() / 3600.0
            
            if hours_lag > 24.0:  # SLA: Máximo 24 horas de antigüedad
                telemetry["freshness_status"] = "SLA_VIOLATED"
                telemetry["details"].append(f"🚨 FRESCURA: Datos desactualizados por {hours_lag:.1f} horas.")

        # 2. PILAR VOLUMEN (Anomalía en cantidad de filas)
        current_volume = len(df)
        volume_ratio = current_volume / float(self.expected_avg_volume) if self.expected_avg_volume > 0 else 1.0
        
        # Alerta si el volumen es menor al 50% o mayor al 200% del promedio esperado
        if volume_ratio < 0.5 or volume_ratio > 2.0:
            telemetry["volume_status"] = "ANOMALY_DETECTED"
            telemetry["details"].append(
                f"🚨 VOLUMEN: Caída/Spike anómalo. Filas: {current_volume} (Esperado ~{self.expected_avg_volume})."
            )

        # 3. PILAR ESQUEMA (Auditoría de columnas)
        current_cols = set(df.columns)
        expected_cols = set(self.expected_schema.keys())

        missing_cols = expected_cols - current_cols
        unexpected_cols = current_cols - expected_cols

        if missing_cols or unexpected_cols:
            telemetry["schema_status"] = "SCHEMA_DRIFT"
            if missing_cols:
                telemetry["details"].append(f"🚨 ESQUEMA: Faltan columnas requeridas: {missing_cols}")
            if unexpected_cols:
                telemetry["details"].append(f"⚠️ ESQUEMA: Se detectaron columnas no documentadas: {unexpected_cols}")

        return telemetry
```

---

## 🏋️‍♂️ Práctica de la Lección 04

1. Ubicate en la carpeta `practica/modulo_08/` de tu repositorio local.
2. Creá el archivo `ej_04_observabilidad_datos.py`.
3. Escribí un script Python que simule el Monitoreo de Observabilidad de Datos sobre tres tablas de la Capa Gold:

```python
from datetime import datetime, timedelta
import pandas as pd

# Esquema de Referencia Esperado (Capa Gold)
EXPECTED_SCHEMA_GOLD = {
    "venta_id": "int",
    "cliente_id": "str",
    "monto_usd": "float",
    "fecha_transaccion": "datetime"
}

AVERAGE_HISTORICAL_VOLUME = 5000  # Promedio de 5,000 registros diarios

class ObservabilityCollectorSimulator:
    def __init__(self, schema: dict, avg_volume: int):
        self.schema = schema
        self.avg_volume = avg_volume

    def check_observability_health(self, df: pd.DataFrame, table_name: str):
        print("==================================================")
        print(f"📡 AUDITANDO OBSERVABILIDAD: TABLA '{table_name}'")
        print("==================================================")
        
        # 1. Chequeo de Frescura
        max_ts = pd.to_datetime(df["fecha_transaccion"]).max() if "fecha_transaccion" in df.columns else None
        now = datetime.now()
        freshness_hours = (now - max_ts).total_seconds() / 3600.0 if max_ts else 999
        
        freshness_flag = "✅ OK" if freshness_hours <= 24.0 else f"🚨 SLA VIOLATED ({freshness_hours:.1f} hrs desactualizado)"

        # 2. Chequeo de Volumen
        rows = len(df)
        ratio = rows / self.avg_volume
        volume_flag = "✅ OK" if 0.5 <= ratio <= 2.0 else f"🚨 ANOMALÍA DE VOLUMEN ({rows} filas vs ~{self.avg_volume} esperadas)"

        # 3. Chequeo de Esquema
        missing = set(self.schema.keys()) - set(df.columns)
        schema_flag = "✅ OK" if not missing else f"🚨 ESQUEMA CORRUPTO (Faltan: {missing})"

        print(f"  • Frescura: {freshness_flag}")
        print(f"  • Volumen:  {volume_flag}")
        print(f"  • Esquema:  {schema_flag}\n")

# Simulador de Tablas
simulator = ObservabilityCollectorSimulator(EXPECTED_SCHEMA_GOLD, AVERAGE_HISTORICAL_VOLUME)

# Tabla 1: Totalmente Sana
df_sana = pd.DataFrame({
    "venta_id": range(1, 4801),
    "cliente_id": ["C1"] * 4800,
    "monto_usd": [100.0] * 4800,
    "fecha_transaccion": [datetime.now() - timedelta(hours=2)] * 4800
})

# Tabla 2: Caída Anómala de Volumen y Desactualizada
df_corrupta = pd.DataFrame({
    "venta_id": range(1, 150),  # Solo 149 filas (Caída > 90%)
    "monto_usd": [100.0] * 149,
    "fecha_transaccion": [datetime.now() - timedelta(days=3)] * 149  # 3 días desactualizado
    # Falta 'cliente_id' (Falla de esquema)
})

# Ejecución de Auditoría
simulator.check_observability_health(df_sana, "gold_fact_ventas_hoy")
simulator.check_observability_health(df_corrupta, "gold_fact_ventas_legacy")
```

4. Agregá comentarios al final del archivo respondiendo:
   * **Consigna A:** Explica por qué una tarea de orquestación que finalice con estado `SUCCESS` (código 0) no garantiza que los datos consumidos por los usuarios de negocio estén actualizados (*Freshness SLA*).
   * **Consigna B:** En una arquitectura Lakehouse con cientos de tablas interconectadas, ¿por qué el Linaje de Datos (*Data Lineage*) es un pilar fundamental para realizar un Análisis de Impacto (*Impact Analysis*) antes de modificar una tabla fuente?