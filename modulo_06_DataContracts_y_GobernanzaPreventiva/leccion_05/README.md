# 📜 Lección 05: Cierre del Módulo 06 — Proyecto Integrador de Contratos de Datos

¡Llegamos al hito final del **Módulo 06: Data Contracts y Gobernanza Preventiva**!

A lo largo de este módulo hemos transformado la manera en que encaramos la estabilidad de los pipelines analíticos:

* **Lección 01:** Adoptamos el paradigma **Shift-Left**, moviendo la responsabilidad de la calidad de datos a la fuente de origen (*Data-as-a-Product*).
* **Lección 02:** Estructuramos contratos de datos declarativos usando el estándar internacional **ODCS (Open Data Contract Standard)** en formato YAML (Esquema, Semántica y SLAs).
* **Lección 03:** Implementamos motores de ejecución (*Contract Enforcement*) con **Pydantic** (para eventos streaming/microservicios) y **Great Expectations** (para lotes masivos).
* **Lección 04:** Integramos la validación preventiva en workflows de **GitHub Actions (CI/CD)** para bloquear *Breaking Changes* antes de fusionar el código a producción.

En esta lección integradora combinaremos todas estas piezas en un **Proyecto Integrador Capstone de Gobernanza Preventiva**, construyendo un motor de contratos completo en Python.

---

## 1. Escenario de Negocio: Microservicio de Pagos y Pipeline de Ingesta

Imaginemos que lideramos la gobernanza de datos para la plataforma de Checkout de un e-commerce.

El equipo de software emite eventos de pago en formato JSON hacia nuestro Data Lakehouse. Nuestra misión es construir un **Motor de Contratos de Datos Integrado** que:

* Cargue el contrato oficial ODCS YAML desde el repositorio.
* Audite las Pull Requests de los ingenieros backend para detectar y bloquear *Breaking Changes* (cambios incompatibles hacia atrás).
* Actúe como guardián en tiempo de ejecución, validando los eventos entrantes y derivando los datos inválidos a un **Dead Letter Queue (DLQ)** para no detener el pipeline ni contaminar la capa Silver.

---

## 2. Diagrama del Sistema de Gobernanza Integrado

```text
  [ CÓDIGO / DESARROLLO ]                 [ INGESTA EN TIEMPO REAL ]
┌─────────────────────────┐             ┌─────────────────────────┐
│ Pull Request (Backend)  │             │ Eventos JSON Ingressing │
└────────────┬────────────┘             └────────────┬────────────┘
             │                                       │
             ▼ (Etapa 1: CI/CD Check)                ▼ (Etapa 2: Enforcement Engine)
┌─────────────────────────┐             ┌─────────────────────────┐
│  ODCS Breaking Change   │             │  Validador Pydantic /   │
│         Auditor         │             │  Contract Enforcement   │
└────────────┬────────────┘             └────────────┬────────────┘
             │                                       │
     ┌───────┴───────┐                       ┌───────┴───────┐
     ▼               ▼                       ▼               ▼
 ❌ Bloquea      ✅ Permite              ✅ Aceptado      ❌ Rechazado
     PR             Merge                (Capa Silver)   (DLQ / Alerta)
```

---

## 3. Script Python Completo del Proyecto Integrador

```python
import yaml
from pydantic import BaseModel, Field, ValidationError
from typing import Literal, Optional

# ============================================================================
# PASO 1: CONTRATO DE DATOS VIGENTE (Especificación ODCS en YAML)
# ============================================================================
ODCS_CONTRACT_YAML = """
dataContractSpecification: 0.9.2
id: contract-checkout-pagos
dataset: transacciones_pago
version: 1.0.0
owner:
  team: "Backend Checkout Team"
  email: "checkout-devs@empresa.com"

schema:
  - name: transaccion_id
    type: integer
    required: true
  - name: cliente_id
    type: string
    required: true
  - name: monto_usd
    type: float
    required: true
  - name: estado
    type: string
    required: true

quality:
  - column: monto_usd
    min_value: 0.01
  - column: estado
    allowed_values: ['PENDIENTE', 'APROBADO', 'RECHAZADO']
"""

# ============================================================================
# PASO 2: COMPONENTE DE CI/CD - DETECTOR DE BREAKING CHANGES
# ============================================================================
class DataContractCIAuditor:
    @staticmethod
    def audit_schema_changes(main_yaml: str, pr_yaml: str) -> bool:
        contract_main = yaml.safe_load(main_yaml)
        contract_pr = yaml.safe_load(pr_yaml)

        main_cols = {col["name"]: col for col in contract_main["schema"]}
        pr_cols = {col["name"]: col for col in contract_pr["schema"]}

        breaking_errors = []

        # 1. Detectar columnas eliminadas
        for col_name, info in main_cols.items():
            if col_name not in pr_cols:
                breaking_errors.append(f"Columna requerida '{col_name}' fue ELIMINADA.")
            else:
                # 2. Detectar cambios de tipo de dato
                if info["type"] != pr_cols[col_name]["type"]:
                    breaking_errors.append(
                        f"Incompatibilidad de tipo en '{col_name}': {info['type']} ➔ {pr_cols[col_name]['type']}"
                    )

        if breaking_errors:
            print("❌ [CI/CD Pipeline] DETECTADOS BREAKING CHANGES - Merge Bloqueado:")
            for err in breaking_errors:
                print(f"   • {err}")
            return False

        print("✅ [CI/CD Pipeline] Contrato Compatible. Cambio aprobado.")
        return True

# ============================================================================
# PASO 3: ENFORCEMENT ENGINE EN TIEMPO DE EJECUCIÓN (Pydantic Validator)
# ============================================================================
class EventoPagoModel(BaseModel):
    transaccion_id: int = Field(..., gt=0)
    cliente_id: str = Field(..., min_length=3)
    monto_usd: float = Field(..., gt=0.0)
    estado: Literal["PENDIENTE", "APROBADO", "RECHAZADO"]

class StreamIngestionPipeline:
    def __init__(self):
        self.silver_layer = []
        self.dead_letter_queue = []

    def consume_event(self, raw_event: dict):
        try:
            # Validar contra el contrato Pydantic
            valid_event = EventoPagoModel(**raw_event)
            self.silver_layer.append(valid_event.model_dump())
            print(f"✅ Evento {valid_event.