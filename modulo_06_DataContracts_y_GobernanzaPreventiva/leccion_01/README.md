# 📜 Lección 01: Concepto de Data Contracts y el Cambio de Paradigma Shift-Left

En los módulos anteriores aprendiste a transformar datos in-warehouse con dbt, construir modelos dimensionales Kimball y gestionar la calidad de datos en la capa analítica.

Sin embargo, hay un problema que destruye la confianza en los equipos de datos todos los días en la industria: **los ingenieros de software modifican las bases de datos de producción (OLTP) o APIs sin avisarle al equipo de datos, rompiendo los pipelines silenciosamente.**

Un desarrollador backend renombra la columna `user_id` a `account_id` o cambia el tipo de dato de `INTEGER` a `VARCHAR`. A las 3:00 AM, los pipelines de ingesta colapsan, los tableros de PowerBI muestran métricas en cero y el equipo de datos pasa horas haciendo "autopsias" y apagando incendios.

En este Módulo 06 aprenderemos a resolver este problema estructural mediante **Data Contracts (Contratos de Datos)** y el paradigma **Shift-Left**.

---

## 1. El Problema de la "Reactividad" y la Caída de Pipelines

En las arquitecturas tradicionales, el equipo de datos trabaja de forma puramente reactiva en la cola del proceso (*downstream*):

```text
ARQUITECTURA REACTIVA TRADICIONAL (Silos de Trabajo):
[ Software Engineer ] ──► Modifica la DB OLTP / API (ej. Cambia tipo de dato)
                                │
                                ▼ (Sin aviso)
[ Pipeline ETL/ELT ]  ──► 💥 COLAPSO SILENCIOSO O DATOS CORRUPTOS
                                │
                                ▼ (Horas después)
[ Data Engineer ]     ──► Pasa la madrugada arreglando el pipeline roto
```

### ¿Por qué ocurre esto?
* **Falta de Acoplamiento y Responsabilidad:** Los ingenieros de software consideran que la base de datos OLTP es su responsabilidad, pero el Data Warehouse "es problema de datos".
* **Falta de Garantías en Origen:** Las APIs y microservicios no garantizan la estabilidad del esquema de los eventos que emiten para analítica.

---

## 2. El Paradigma Shift-Left (Mover la Calidad a la Izquierda)

El concepto de **Shift-Left** propone desplazar la validación de calidad y la gobernanza de datos hacia la izquierda del flujo de desarrollo (al momento exacto en que el código de la aplicación de origen se está escribiendo y probando).

```text
PARADIGMA SHIFT-LEFT (Gobernanza Preventiva con Data Contracts):
[ Software Engineer ] ──► Escribe código en la App / Microservicio
                                │
                                ▼ (Validación Automática en CI/CD)
                       ┌─────────────────────────────────────────┐
                       │   DATA CONTRACT (Acuerdo Vinculante)    │
                       │ • Valida esquema, tipos y semántica     │
                       └─────────────────────────────────────────┘
                                │
           ┌────────────────────┴────────────────────┐
           ▼                                         ▼
  ❌ Intento de Breaking Change             ✅ Cambio Válido
     El CI/CD BLOQUEA el deploy                El pipeline ingiere
     de la App origen                          datos limpios sin fallar
```

> ### 💡 Principio Fundamental
>
> **El dato no se limpia en el Data Warehouse; el dato se emite limpio y garantizado desde la fuente.**  
> Los equipos de software de origen pasan a considerar los datos que emiten como un producto primario (*Data-as-a-Product*) con un contrato de servicio (SLA) asegurado.

---

## 3. ¿Qué es exactamente un Data Contract?

Un **Data Contract (Contrato de Datos)** es un acuerdo formal, declarativo y ejecutable entre los creadores de los datos (ingenieros de software/aplicaciones) y los consumidores (ingenieros de datos, analistas y científicos de datos).

Especifica exactamente la estructura, los tipos de datos, la semántica de negocio y los niveles de servicio que la fuente se compromete a mantener estables en el tiempo.

```text
                             ANATOMÍA DE UN DATA CONTRACT
                                           │
         ┌─────────────────────────────────┼─────────────────────────────────┐
         ▼                                 ▼                                 ▼
1. ESQUEMA TÉCNICO Y TIPOS        2. SEMÁNTICA Y REGLAS            3. SLAs Y PROPIEDAD
• Nombres de columnas             • Significado del dato           • Owner (Equipo emisor)
• Tipos de datos (INT, TEXT)      • Valores permitidos             • Frescura (ej. < 15 min)
• Nulabilidad (NOT NULL)          • Reglas de negocio (monto > 0)  • Disponibilidad (99.9%)
```

### Los 3 Pilares de un Data Contract:
* **Esquema Técnico (*Schema Definition*):** Define la estructura física exacta (columnas, tipos de datos, nulos, campos requeridos) en un formato estándar como YAML o JSON Schema.
* **Semántica y Calidad (*Semantics & Data Quality*):** Define qué significa cada campo en el negocio y las restricciones que debe cumplir (ej. "el estado solo puede ser `PENDIENTE`, `COMPLETADO` o `CANCELADO`").
* **Acuerdos de Nivel de Servicio (*SLAs / Operational Metadata*):** Define quién es el equipo dueño del dato (*Owner*), la frecuencia de actualización (frescura) y el canal de alertas ante incidentes.

---

## 📊 Comparativa: Pipeline Tradicional vs. Pipeline con Data Contracts

| Criterio | Pipeline Tradicional (Reactivo) | Pipeline con Data Contracts (Preventivo) |
| :--- | :--- | :--- |
| **Punto de Detección de Errores** | Downstream (En el Data Warehouse a las 3 AM) | Upstream (En la App de origen antes de hacer Deploy) |
| **Responsabilidad del Dato** | Exclusiva del Data Engineer | Compartida (Software Engineer es dueño del origen) |
| **Gestión de Cambios (*Breaking Changes*)** | Sorpresiva y sin aviso | Planificada y versionada (`v1.0.0` $\rightarrow$ `v2.0.0`) |
| **Calidad de Datos** | Limpieza defensiva posterior (`COALESCE`, `TRY_CAST`) | Garantizada por diseño en la fuente |
| **Tiempo de Reparación (MTTR)** | Alto (Horas o días arreglando tablas) | Cero (Evita la corrupción del pipeline) |

---

## 🏋️‍♂️ Práctica de la Lección 01

1. Ubicate en la carpeta `practica/modulo_06/` de tu repositorio local.
2. Creá el archivo `ej_01_concepto_data_contracts.py`.
3. Escribí un script Python que simule un motor de validación de contratos en origen que bloquee la emisión de un evento si viola el esquema acordado:

```python
import json

# 1. Definición del Contrato de Datos (Acuerdo en YAML/JSON)
DATA_CONTRACT_SCHEMA = {
    "version": "1.0.0",
    "entity": "transaccion_pago",
    "owner": "team_checkout_backend",
    "columns": {
        "transaccion_id": {"type": int, "required": True},
        "monto_usd": {"type": float, "required": True, "min_value": 0.01},
        "estado": {"type": str, "required": True, "allowed_values": ["PENDIENTE", "APROBADO", "RECHAZADO"]}
    }
}

# 2. Validador Preventivo de Contratos (Simulación de Middleware en la App de Origen)
class DataContractValidator:
    def __init__(self, contract: dict):
        self.contract = contract

    def validate_event(self, payload: dict) -> tuple[bool, str]:
        cols_contract = self.contract["columns"]

        for col_name, rules in cols_contract.items():
            # Validar requerimiento
            if rules.get("required") and col_name not in payload:
                return False, f"❌ VIOLACIÓN DE CONTRATO: Campo requerido '{col_name}' ausente."

            val = payload[col_name]

            # Validar tipo de dato
            if not isinstance(val, rules["type"]):
                return False, f"❌ VIOLACIÓN DE CONTRATO: Tipo incorrecto en '{col_name}'. Esperado {rules['type'].__name__}, recibido {type(val).__name__}."

            # Validar rango/valores permitidos
            if "min_value" in rules and val < rules["min_value"]:
                return False, f"❌ VIOLACIÓN DE CONTRATO: '{col_name}' debe ser >= {rules['min_value']}. Valor recibido: {val}."

            if "allowed_values" in rules and val not in rules["allowed_values"]:
                return False, f"❌ VIOLACIÓN DE CONTRATO: '{col_name}' tiene el valor no permitido '{val}'."

        return True, "✅ EVENTO CUMPLE CON EL DATA CONTRACT"

# 3. Pruebas de Ingesta
validator = DataContractValidator(DATA_CONTRACT_SCHEMA)

# Evento Válido
evento_correcto = {"transaccion_id": 9001, "monto_usd": 150.50, "estado": "APROBADO"}
valid, msg = validator.validate_event(evento_correcto)
print(f"Prueba 1: {msg}")

# Evento Erróneo (Breaking Change: tipo de dato String en monto y estado inválido)
evento_invalido = {"transaccion_id": 9002, "monto_usd": -50.00, "estado": "COMPLETADO"}
valid, msg = validator.validate_event(evento_invalido)
print(f"Prueba 2: {msg}")
```

4. Agregá comentarios al final del archivo respondiendo:
   * **Consigna A:** ¿Qué diferencia existe entre hacer validaciones con `CHECK` constraints en SQL dentro del Data Warehouse vs. aplicar el paradigma Shift-Left con Data Contracts en la fuente origen?
   * **Consigna B:** Si un equipo de desarrollo de software necesita renombrar la columna `monto_usd` a `monto_total`, ¿cómo debe gestionarse esa modificación dentro del ciclo de vida de un Data Contract sin romper las aplicaciones aguas abajo?