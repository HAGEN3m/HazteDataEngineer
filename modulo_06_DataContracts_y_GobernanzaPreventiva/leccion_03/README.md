# 📜 Lección 03: Validación Automática de Esquemas con Python/Pydantic y Great Expectations

En la Lección 02 aprendimos a estructurar un Data Contract estandarizado en YAML utilizando la especificación **ODCS (Open Data Contract Standard)**, definiendo metadatos, esquemas técnicos, reglas de calidad y SLAs.

Sin embargo, tener un contrato escrito en YAML es solo el primer paso. El contrato por sí solo no detiene los datos corruptos; necesitamos **motores de ejecución (*Contract Enforcement Engines*)** que lean la especificación YAML en tiempo real y validen programáticamente cada registro o dataset antes de permitir su ingreso a los pipelines de analítica.

En esta lección aprenderemos a implementar la validación automática de contratos utilizando dos herramientas estándar de la industria:
* **Pydantic:** Para validación en tiempo de ejecución de eventos individuales, streaming o payloads de APIs (Microservicios).
* **Great Expectations:** Para validación masiva por lotes (*Batch*) sobre Data Lakes, Data Warehouses y archivos Parquet/CSV.

---

## 1. Validación en Tiempo de Ejecución con Pydantic

Pydantic es la librería de validación de tipos y estructuras de datos más utilizada en el ecosistema de Python. Transforma diccionarios o JSONs desestructurados en objetos de Python fuertemente tipados.

### ¿Cuándo usar Pydantic para Data Contracts?
* **Ingesta por Streaming:** Procesamiento de eventos en tiempo real desde Kafka, RabbitMQ o AWS Kinesis.
* **APIs y Webhooks:** Módulos de ingesta donde un microservicio recibe payloads JSON de terceros o aplicaciones móviles.
* **Micro-lotes (*Micro-batches*):** Validación de registros individuales en funciones Serverless (AWS Lambda, GCP Cloud Functions).

### Ejemplo: Modelo de Pydantic con Validadores de Contrato

```python
from pydantic import BaseModel, Field, field_validator, EmailStr
from typing import Literal
from datetime import datetime

# Definición del Contrato en Pydantic (BaseModel)
class ContratoOrdenCompra(BaseModel):
    orden_id: int = Field(..., gt=0, description="Clave primaria entero positivo")
    cliente_id: str = Field(..., min_length=5, description="UUID o código del cliente")
    email_contacto: EmailStr
    monto_total_usd: float = Field(..., gt=0.0, description="Monto cobrado positivo")
    estado: Literal["PENDIENTE", "APROBADO", "CANCELADO"]
    fecha_transaccion: datetime

    # Validador personalizado (Custom Rule)
    @field_validator("monto_total_usd")
    @classmethod
    def validar_monto_razonable(cls, v: float) -> float:
        if v > 100000.0:
            raise ValueError("El monto supera el límite máximo permitido por transacción ($100,000 USD).")
        return round(v, 2)
```

Si un payload JSON llega con un email inválido (`email_contacto="juan-sin-arroba"`), un monto negativo (`monto_total_usd=-50`) o un estado no soportado (`estado="COMPLETADO"`), Pydantic lanza una excepción `ValidationError` de forma instantánea antes de que el registro ingrese al pipeline de ingesta.

---

## 2. Validación Masiva por Lotes con Great Expectations

Cuando trabajamos con datasets masivos (millones de filas en archivos Parquet, CSVs o tablas de PostgreSQL/Snowflake), validar fila por fila con Pydantic resulta ineficiente.

**Great Expectations (GE)** es el framework líder para la validación declarativa de datos en procesamiento por lotes (*Batch Data Validation*).

```text
               FLUJO DE VALIDACIÓN EN GREAT EXPECTATIONS
┌────────────────────────┐      ┌────────────────────────┐      ┌────────────────────────┐
│  Dataset de Entrada    │ ──►  │   Expectation Suite    │ ──►  │    Data Docs Report    │
│ (DF Polars/Pandas/SQL) │      │  (Reglas del Contrato) │      │  (HTML de Aprobación)  │
└────────────────────────┘      └────────────────────────┘      └────────────────────────┘
```

### Conceptos Clave de Great Expectations:
* **Expectation:** Una afirmación declarativa sobre los datos. Ejemplos:
  * `expect_column_values_to_not_be_null(column="orden_id")`
  * `expect_column_values_to_be_between(column="monto_total_usd", min_value=0.01)`
  * `expect_column_values_to_be_in_set(column="estado", value_set=["PENDIENTE", "APROBADO"])`
* **Expectation Suite:** Colección de expectativas que representan el Data Contract de una tabla completa.
* **Validation Result:** Objeto JSON y reporte HTML interactivo (*Data Docs*) que indica si el dataset pasó o falló el contrato, detallando exactamente qué filas violaron las reglas.

---

## 📊 Matriz Comparativa: Pydantic vs. Great Expectations

| Criterio | Pydantic | Great Expectations |
| :--- | :--- | :--- |
| **Arquitectura de Ingesta** | Streaming / Eventos Registro por Registro | Batch / Lotes Masivos (Archivos / Tablas) |
| **Motor de Cómputo** | Python Native (RAM de la app) | Pandas, Spark, SQL Directo in-Warehouse |
| **Punto de Ejecución** | Microservicios, APIs, AWS Lambda | Pipelines ETL/ELT, dbt, Airflow, CI/CD |
| **Salida de Validación** | Excepción `ValidationError` inmediata | Reportes detallados JSON/HTML (Data Docs) |
| **Performance** | Ultra rápida para 1 a 1,000 registros | Altamente optimizada para Terabytes de datos |

---

## 🏋️‍♂️ Práctica de la Lección 03

1. Ubicate en la carpeta `practica/modulo_06/` de tu repositorio local.
2. Creá el archivo `ej_03_validacion_pydantic_ge.py`.
3. Escribí un script Python que combine ambas estrategias: Pydantic para validar streaming y una simulación ligera de Expectations para datasets tabulares:

```python
import pandas as pd
from pydantic import BaseModel, Field, ValidationError
from typing import Literal

# ============================================================
# PARTE 1: VALIDACIÓN INDIVIDUAL EN TIEMPO DE EJECUCIÓN (Pydantic)
# ============================================================
class EventoOrdenContract(BaseModel):
    orden_id: int = Field(..., gt=0)
    cliente_id: str = Field(..., min_length=3)
    monto: float = Field(..., gt=0.0)
    estado: Literal["PENDIENTE", "APROBADO", "CANCELADO"]

def procesar_evento_streaming(raw_json: dict):
    try:
        evento_valido = EventoOrdenContract(**raw_json)
        print(f"✅ [Pydantic Streaming] Evento {evento_valido.orden_id} aprobado con éxito.")
        return True
    except ValidationError as e:
        print(f"❌ [Pydantic Streaming] Evento RECHAZADO por violación de contrato:\n{e.errors()[0]['msg']}")
        return False

# ============================================================
# PARTE 2: VALIDACIÓN MASIVA POR LOTES (Batch Simulator GE)
# ============================================================
class GreatExpectationsBatchSimulator:
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.results = []

    def expect_column_values_to_not_be_null(self, column: str):
        null_count = self.df[column].isnull().sum()
        passed = null_count == 0
        self.results.append({
            "check": f"expect_column_values_to_not_be_null({column})",
            "success": passed,
            "unexpected_count": int(null_count)
        })

    def expect_column_values_to_be_in_set(self, column: str, value_set: list):
        invalid_count = (~self.df[column].isin(value_set)).sum()
        passed = invalid_count == 0
        self.results.append({
            "check": f"expect_column_values_to_be_in_set({column})",
            "success": passed,
            "unexpected_count": int(invalid_count)
        })

    def validate(self) -> bool:
        all_passed = True
        print("\n--- [Great Expectations Batch Report] ---")
        for res in self.results:
            status = "✅ PASSED" if res["success"] else "❌ FAILED"
            print(f"{status} | {res['check']} | Valores anómalos: {res['unexpected_count']}")
            if not res["success"]:
                all_passed = False
        return all_passed

# ------------------------------------------------------------
# EJECUCIÓN DE PRUEBAS
# ------------------------------------------------------------
print("=== PRUEBA 1: STREAMING CON PYDANTIC ===")
procesar_evento_streaming({"orden_id": 101, "cliente_id": "CLI-55", "monto": 250.0, "estado": "APROBADO"})
procesar_evento_streaming({"orden_id": -5, "cliente_id": "CLI-55", "monto": -10.0, "estado": "INVALIDO"}) # Falla

print("\n=== PRUEBA 2: BATCH CON SIMULADOR GREAT EXPECTATIONS ===")
batch_data = pd.DataFrame([
    {"orden_id": 1, "monto": 100.0, "estado": "APROBADO"},
    {"orden_id": 2, "monto": 150.0, "estado": "PENDIENTE"},
    {"orden_id": None, "monto": 200.0, "estado": "DESCONOCIDO"} # Falla nulo y estado
])

ge_sim = GreatExpectationsBatchSimulator(batch_data)
ge_sim.expect_column_values_to_not_be_null("orden_id")
ge_sim.expect_column_values_to_be_in_set("estado", ["PENDIENTE", "APROBADO", "CANCELADO"])
ge_sim.validate()
```

4. Agregá comentarios al final del archivo respondiendo:
   * **Consigna A:** ¿En qué escenario técnico preferirías utilizar Pydantic por sobre Great Expectations para hacer cumplir un Data Contract?
   * **Consigna B:** Si un lote de 1,000,000 de filas en formato Parquet debe ser validado antes de ser cargado a la capa Silver de un Data Lakehouse, ¿cuál de las dos herramientas escala mejor sin saturar la memoria RAM del servidor de ingesta?