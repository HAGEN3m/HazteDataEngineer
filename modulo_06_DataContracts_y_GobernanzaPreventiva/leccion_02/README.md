# 📜 Lección 02: Especificación ODCS (Open Data Contract Standard) en YAML (Esquema, Semántica y SLAs)

En la Lección 01 comprendimos el cambio cultural del paradigma **Shift-Left**: en lugar de apagar incendios a las 3 AM cuando una base de datos de origen cambia silenciosamente un tipo de dato, los equipos de desarrollo de software asumen la responsabilidad de emitir datos limpios mediante **Data Contracts (Contratos de Datos)**.

Sin embargo, para que un contrato sea comprensible tanto por humanos (desarrolladores, analistas) como por máquinas (pipelines de CI/CD, validadores automáticos), necesita un formato estandarizado e independiente del proveedor.

En esta lección aprenderemos a escribir Data Contracts profesionales utilizando la especificación estándar de la industria **ODCS (Open Data Contract Standard)** expresada en archivos YAML.

---

## 1. ¿Qué es ODCS y por qué necesitamos un Estándar Abierto?

Así como la especificación **OpenAPI (Swagger)** revolucionó el desarrollo de software estandarizando cómo se documentan y validan las APIs REST, el ecosistema de datos adoptó **ODCS (Open Data Contract Standard)**.

```text
  DESARROLLO DE SOFTWARE                          INGENIERÍA DE DATOS
┌─────────────────────────┐                     ┌─────────────────────────┐
│       OpenAPI           │                     │          ODCS           │
│   (Swagger - YAML)      │                     │ (Data Contract - YAML)  │
├─────────────────────────┤                     ├─────────────────────────┤
│ Estándar para consumo   │                     │ Estándar para emisión y │
│ y validación de APIs    │                     │ gobernanza de Datasets  │
└─────────────────────────┘                     └─────────────────────────┘
```

### Ventajas de utilizar ODCS:
* **Formato Declarativo Human-Readable:** Escrito en YAML plano, legible tanto por ingenieros backend como por analistas de negocio.
* **Interoperabilidad Total:** Puede ser consumido por linters de CI/CD, herramientas de calidad (Great Expectations, Soda), dbt o generadores automáticos de código.
* **Versionado Semántico (SemVer):** Permite gestionar la evolución del esquema mediante versiones formales (`v1.0.0` $\rightarrow$ `v1.1.0` $\rightarrow$ `v2.0.0`).

---

## 2. Anatomía de un Data Contract en ODCS (Secciones Principales)

Un contrato ODCS profesional se organiza en 4 secciones fundamentales:

```text
┌─────────────────────────────────────────────────────────────────┐
│ 1. METADATOS Y PROPIEDAD (dataset, version, owner, domain)      │
├─────────────────────────────────────────────────────────────────┤
│ 2. ESQUEMA TÉCNICO Y MODELO (columns, data_types, nullability)  │
├─────────────────────────────────────────────────────────────────┤
│ 3. REGLAS DE CALIDAD Y SEMÁNTICA (custom quality checks)        │
├─────────────────────────────────────────────────────────────────┤
│ 4. SLAs Y NIVELES DE SERVICIO (freshness, availability, support)│
└─────────────────────────────────────────────────────────────────┘
```

### Sección 1: Metadatos y Propiedad (Header & Ownership)
Identifica el dataset, quién es el equipo emisor responsable (*Owner*) y la versión del contrato.

```yaml
dataContractSpecification: 0.9.2
id: contract-ordenes-compra
dataset: ordenes_compra
version: 1.2.0
status: active
domain: checkout_ecommerce
owner:
  team: "Backend Checkout Team"
  channel: "#help-checkout-data"
  email: "checkout-devs@empresa.com"
```

### Sección 2: Esquema Técnico (Schema Definition)
Describe cada campo que compone el dataset, su tipo de dato técnico, si admite nulos y una descripción clara de su significado de negocio.

```yaml
schema:
  - name: orden_id
    type: integer
    primary_key: true
    required: true
    description: "Identificador único de la orden de compra."

  - name: cliente_id
    type: string
    required: true
    description: "Código de identificación del cliente en la base OLTP."

  - name: monto_total_usd
    type: decimal
    precision: 10
    scale: 2
    required: true
    description: "Monto cobrado en dólares luego de aplicar descuentos."

  - name: estado_orden
    type: string
    required: true
    description: "Estado operativo actual de la orden."
```

### Sección 3: Reglas de Calidad y Semántica (Quality Rules)
Define las restricciones de negocio que el dataset debe cumplir estrictamente en origen.

```yaml
quality:
  - type: custom
    name: check_monto_positivo
    column: monto_total_usd
    rule: "monto_total_usd > 0.0"
    engine: sql

  - type: enum
    column: estado_orden
    allowed_values: ['PENDIENTE', 'APROBADO', 'DESPACHADO', 'CANCELADO']

  - type: row_count
    rule: "> 0" # Garantiza que la emisión no llegue vacía
```

### Sección 4: Acuerdos de Nivel de Servicio (SLAs & Operational Metadata)
Especifica los compromisos operativos de disponibilidad, latencia y frescura del dato (*Data Freshness*).

```yaml
servicelevels:
  freshness:
    max_lag_minutes: 15
    description: "El dataset debe actualizarse con una latencia máxima de 15 minutos."
  availability:
    uptime_percentage: 99.9
  retention:
    period_days: 730 # 2 años de historial disponible
```

---

## 3. Archivo YAML ODCS Completo: `contrato_ordenes_compra.yaml`

A continuación integramos las 4 secciones en un contrato listo para producción:

```yaml
dataContractSpecification: 0.9.2
id: contract-checkout-ordenes
dataset: ordenes_compra
version: 1.0.0
status: active
domain: checkout
owner:
  team: "Backend Checkout"
  contact: "checkout-team@empresa.com"

schema:
  - name: orden_id
    type: integer
    primary_key: true
    required: true
    description: "Clave primaria atómica de la transacción."

  - name: cliente_id
    type: string
    required: true
    description: "UUID del cliente que realizó la compra."

  - name: monto_total_usd
    type: decimal
    required: true
    description: "Monto neto en USD."

  - name: estado_orden
    type: string
    required: true
    description: "Estado del ciclo de vida de la orden."

quality:
  - type: range
    column: monto_total_usd
    min: 0.01
  - type: enum
    column: estado_orden
    allowed_values: ['PENDIENTE', 'APROBADO', 'CANCELADO']

servicelevels:
  freshness:
    max_lag_minutes: 30
```

---

## 🛠️ Parsing y Validación del Contrato en Python

Para usar este contrato dentro de un pipeline de ingesta o prueba de CI/CD, podemos parsear el YAML en Python y validar datos entrantes de forma programática:

```python
import yaml

def cargar_contrato_odcs(path_yaml: str) -> dict:
    with open(path_yaml, 'r', encoding='utf-8') as f:
        contrato = yaml.safe_load(f)
    return contrato

# Extraer el esquema requerido del contrato
def obtener_columnas_requeridas(contrato: dict) -> list:
    return [
        col["name"] 
        for col in contrato.get("schema", []) 
        if col.get("required")
    ]
```

---

## 🏋️‍♂️ Práctica de la Lección 02

1. Ubicate en la carpeta `practica/modulo_06/` de tu repositorio local.
2. Creá el archivo `ej_02_especificacion_odcs.py`.
3. Escribí un script Python que parsee un string YAML en formato ODCS y valide un lote de registros entrantes:

```python
import yaml

# Contrato ODCS en formato YAML
ODCS_YAML_CONTRACT = """
dataContractSpecification: 0.9.2
id: contract-telemetria-sensores
dataset: mediciones_sensores
version: 1.0.0
owner:
  team: "IoT Hardware Team"

schema:
  - name: sensor_id
    type: int
    required: true
  - name: temperatura
    type: float
    required: true
  - name: ubicacion
    type: str
    required: false

quality:
  - column: temperatura
    min_val: -50.0
    max_val: 100.0
"""

class ODCSValidator:
    def __init__(self, yaml_str: str):
        self.contract = yaml.safe_load(yaml_str)
        self.schema = {col["name"]: col for col in self.contract["schema"]}
        self.quality = self.contract.get("quality", [])

    def validate_batch(self, batch: list[dict]) -> list[str]:
        errors = []
        for idx, record in enumerate(batch):
            # 1. Validar Campos Requeridos
            for col_name, rules in self.schema.items():
                if rules.get("required") and col_name not in record:
                    errors.append(f"Fila {idx}: Campo requerido '{col_name}' ausente.")

            # 2. Validar Reglas de Calidad (Rango de temperatura)
            if "temperatura" in record:
                temp = record["temperatura"]
                for q in self.quality:
                    if q.get("column") == "temperatura":
                        if temp < q["min_val"] or temp > q["max_val"]:
                            errors.append(
                                f"Fila {idx}: Temperatura {temp}°C fuera de rango [{q['min_val']}, {q['max_val']}]."
                            )
        return errors

# Datos de Prueba
lote_datos = [
    {"sensor_id": 101, "temperatura": 25.4, "ubicacion": "Planta 1"},
    {"temperatura": 150.0, "ubicacion": "Planta 2"}, # Error: Falta sensor_id y temp fuera de rango
    {"sensor_id": 103, "temperatura": -10.0}
]

validator = ODCSValidator(ODCS_YAML_CONTRACT)
errores_encontrados = validator.validate_batch(lote_datos)

print("--- RESULTADO DE VALIDACIÓN ODCS ---")
if errores_encontrados:
    for err in errores_encontrados:
        print(f"❌ {err}")
else:
    print("✅ Lote 100% Válido según el Contrato ODCS.")
```

4. Agregá comentarios al final del archivo respondiendo:
   * **Consigna A:** ¿Qué beneficio aporta declarar la sección `servicelevels` (SLAs) dentro del archivo YAML del contrato en lugar de tener las expectativas de latencia documentadas en un Confluence?
   * **Consigna B:** Si un equipo emisor quiere lanzar la versión `2.0.0` de un contrato eliminando una columna existente, ¿por qué el versionado semántico (SemVer) alerta al equipo de datos sobre un *Breaking Change*?