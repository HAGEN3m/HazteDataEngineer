# 📜 Lección 04: Integración de Data Contracts en CI/CD para Prevenir Breaking Changes

En la Lección 03 aprendimos a ejecutar validaciones programáticas de nuestros Data Contracts usando **Pydantic** (para eventos en tiempo real / streaming) y **Great Expectations** (para lotes masivos / batch).

Sin embargo, ejecutar validaciones solo cuando los datos ya se están enviando a la base de datos sigue teniendo un riesgo: si un desarrollador backend hace deploy de una modificación en el código de producción que altera la estructura del evento, el pipeline de ingesta comenzará a rechazar registros en tiempo de ejecución.

Para lograr la verdadera prevención del paradigma **Shift-Left**, debemos mover la validación un paso más atrás: al pipeline de **Integración Continua (CI/CD)** del repositorio de código de la aplicación de origen.

En esta lección aprenderemos a automatizar la verificación de Data Contracts en GitHub Actions para detectar y bloquear cambios destructivos (*Breaking Changes*) antes de que el código del backend se fusione a producción.

---

## 1. El Rol de CI/CD en la Gobernanza Preventiva

El pipeline de CI/CD (*Continuous Integration / Continuous Deployment*) es el "guardián" de código de la organización. Cada vez que un desarrollador abre una Solicitud de Extracción (*Pull Request* o PR) en GitHub o GitLab, el CI/CD ejecuta pruebas automáticas.

Al integrar los Data Contracts en el CI/CD de las aplicaciones de software que generan datos, logramos que ninguna modificación de código que rompa las tablas analíticas pueda ser desplegada a producción.

```text
               FLUJO PREVENTIVO DE DATA CONTRACTS EN CI/CD
[ Software Dev ] ──► Abre Pull Request (PR) modificando el esquema de la App
                           │
                           ▼
              ┌─────────────────────────────────────────┐
              │  WORKFLOW DE GITHUB ACTIONS (CI/CD)     │
              │  1. `datacontract lint` (Sintaxis)      │
              │  2. `datacontract test` (Compatibilidad)│
              └─────────────────────────────────────────┘
                           │
         ┌─────────────────┴─────────────────┐
         ▼                                   ▼
 ❌ DETECTA BREAKING CHANGE           ✅ CAMBIO COMPATIBLE
    • Comentario automático en PR        • CI/CD aprueba el Merge
    • MERGE BLOQUEADO                    • Despliegue seguro
```

---

## 2. Tipos de Cambios en Esquemas: Breaking vs. Non-Breaking Changes

Para que un pipeline de CI/CD pueda evaluar inteligentemente las modificaciones de un contrato, debemos clasificar los cambios en dos categorías según el impacto en las aplicaciones downstream:

```text
                           EVALUACIÓN DE CAMBIOS EN ESQUEMAS
                                         │
                 ┌───────────────────────┴───────────────────────┐
                 ▼                                               ▼
   NON-BREAKING (Compatibles hacia atrás)            BREAKING CHANGES (Destructivos)
   • Agregar una columna OPCIONAL (`required: false`) • Eliminar una columna existente
   • Agregar descripciones o metadatos              • Renombrar una columna (`user_id` ➔ `account_id`)
   • Expandir valores permitidos en un ENUM         • Cambiar tipo de dato (`INT` ➔ `VARCHAR`)
   • Incremento de versión MENOR (v1.0.0 ➔ v1.1.0)  • Volver 'requerida' una columna opcional
                                                    • Incremento de versión MAYOR (v1.0.0 ➔ v2.0.0)
```

### Regla de Control en CI/CD:
* **Non-Breaking Change:** El CI/CD permite el merge automático e incrementa la versión menor del contrato (`v1.1.0`).
* **Breaking Change:** El CI/CD falla y frena la integración, exigiendo que el desarrollador cree una versión mayor (`v2.0.0`) y coordine la migración con el equipo de datos.

---

## 3. Implementación con GitHub Actions (`.github/workflows/data_contract_ci.yml`)

A continuación se muestra una configuración real de GitHub Actions que utiliza la herramienta oficial CLI `datacontract-cli` para auditar el contrato `datacontract.yaml` presente en el repositorio del microservicio backend:

```yaml
name: Data Contract Prevention CI

on:
  pull_request:
    paths:
      - 'datacontract.yaml'
      - 'src/models/**' # Cambios en el código fuente del microservicio

jobs:
  verify-data-contract:
    runs-on: ubuntu-latest
    steps:
      - name: 1. Checkout del código
        uses: actions/checkout@v4

      - name: 2. Configurar Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: 3. Instalar CLI de Data Contracts
        run: |
          pip install datacontract-cli

      - name: 4. Validar Sintaxis y Estándar ODCS (Lint)
        run: |
          datacontract lint datacontract.yaml

      - name: 5. Verificar Cambios Destructivos (Breaking Change Detection)
        run: |
          # Compara el contrato del PR actual contra el contrato de la rama principal (main)
          datacontract test --schema datacontract.yaml
```

---

### 🛠️ Simulación del Algoritmo de Detección de Breaking Changes

A nivel de software, el motor de CI/CD compara el diccionario del contrato vigente en producción (`v1.0.0`) contra el contrato propuesto en el PR.

Si detecta la eliminación de un campo requerido o una alteración de tipo de dato incompatible, genera una lista de infracciones que detiene el flujo de trabajo:

```python
# Lógica interna del motor de CI/CD para comparar esquemas
def detectar_breaking_changes(contrato_main: dict, contrato_pr: dict) -> list[str]:
    breaking_errors = []
    schema_main = {col["name"]: col for col in contrato_main["schema"]}
    schema_pr = {col["name"]: col for col in contrato_pr["schema"]}

    # 1. Chequeo de columnas eliminadas
    for col_name, col_info in schema_main.items():
        if col_name not in schema_pr:
            breaking_errors.append(f"💥 BREAKING CHANGE: La columna '{col_name}' fue ELIMINADA del contrato.")
        else:
            # 2. Chequeo de cambio de tipo de dato
            tipo_main = col_info["type"]
            tipo_pr = schema_pr[col_name]["type"]
            if tipo_main != tipo_pr:
                breaking_errors.append(
                    f"💥 BREAKING CHANGE: La columna '{col_name}' cambió de tipo ({tipo_main} ➔ {tipo_pr})."
                )

    return breaking_errors
```

---

## 🏋️‍♂️ Práctica de la Lección 04

1. Ubicate en la carpeta `practica/modulo_06/` de tu repositorio local.
2. Creá el archivo `ej_04_cicd_breaking_changes.py`.
3. Escribí un script Python que simule el controlador de CI/CD para la validación automática de Pull Requests:

```python
# Contrato de Producción Vigente (Rama main / v1.0.0)
CONTRACT_MAIN = {
    "version": "1.0.0",
    "dataset": "pagos_checkout",
    "schema": [
        {"name": "pago_id", "type": "integer", "required": True},
        {"name": "cliente_id", "type": "string", "required": True},
        {"name": "monto_usd", "type": "decimal", "required": True},
        {"name": "estado", "type": "string", "required": True}
    ]
}

# Propuesta 1 de PR (Non-Breaking Change: Agrega columna opcional)
CONTRACT_PR_COMPATIBLE = {
    "version": "1.1.0",
    "dataset": "pagos_checkout",
    "schema": [
        {"name": "pago_id", "type": "integer", "required": True},
        {"name": "cliente_id", "type": "string", "required": True},
        {"name": "monto_usd", "type": "decimal", "required": True},
        {"name": "estado", "type": "string", "required": True},
        {"name": "ip_origen", "type": "string", "required": False} # Compatible
    ]
}

# Propuesta 2 de PR (Breaking Change: Renombra/elimina columna y altera tipo de dato)
CONTRACT_PR_BREAKING = {
    "version": "1.0.1",
    "dataset": "pagos_checkout",
    "schema": [
        {"name": "pago_id", "type": "integer", "required": True},
        {"name": "cliente_id", "type": "integer", "required": True}, # Breaking: string -> integer
        # Breaking: monto_usd fue eliminada
        {"name": "estado", "type": "string", "required": True}
    ]
}

class CICDContractChecker:
    @staticmethod
    def audit_pull_request(main_contract: dict, pr_contract: dict) -> bool:
        print(f"\n--- Evaluando Pull Request para Dataset: {pr_contract['dataset']} ---")
        breaking_changes = []

        cols_main = {col["name"]: col for col in main_contract["schema"]}
        cols_pr = {col["name"]: col for col in pr_contract["schema"]}

        # Check 1: Columnas eliminadas
        for col_name, info_main in cols_main.items():
            if col_name not in cols_pr:
                breaking_changes.append(f"Eliminación de columna requerida: '{col_name}'")
            else:
                # Check 2: Cambio de tipo
                if info_main["type"] != cols_pr[col_name]["type"]:
                    breaking_changes.append(
                        f"Incompatibilidad de tipo en '{col_name}': {info_main['type']} ➔ {cols_pr[col_name]['type']}"
                    )

        if breaking_changes:
            print("❌ PIPELINE DE CI/CD FALLIDO: Merge Bloqueado por Breaking Changes:")
            for err in breaking_changes:
                print(f"   • {err}")
            return False

        print("✅ PIPELINE DE CI/CD EXITOSO: Cambio compatible. PR aprobado para Merge.")
        return True

# Ejecución del Simulador de CI/CD
checker = CICDContractChecker()

# Test 1: Evaluar PR Compatible
checker.audit_pull_request(CONTRACT_MAIN, CONTRACT_PR_COMPATIBLE)

# Test 2: Evaluar PR destructivo
checker.audit_pull_request(CONTRACT_MAIN, CONTRACT_PR_BREAKING)
```

4. Agregá comentarios al final del archivo respondiendo:
   * **Consigna A:** ¿Por qué agregar una columna opcional (`required: false`) en un contrato se considera un cambio compatible (Non-Breaking), mientras que agregar una columna requerida (`required: true`) puede romper las ingestas existentes?
   * **Consigna B:** Si un equipo backend necesita realizar obligatoriamente un Breaking Change (ej. renombrar un campo clave), ¿cuál es el procedimiento estándar de versionado semántico (SemVer) y migración en paralelo que debe seguirse?