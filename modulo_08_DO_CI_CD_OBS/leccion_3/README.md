# 🚀 Lección 03: Pruebas de Calidad de Datos in-Pipeline y Monitoreo de Data Drift

En la Lección 02 aprendimos a configurar workflows de GitHub Actions para auditar automáticamente el código Python (`ruff`, `pytest`) y las consultas SQL (`SQLFluff`) en cada Pull Request.

Sin embargo, en el paradigma DataOps existe un desafío adicional: **el código puede ser 100% perfecto, pero los datos reales que ingresan diariamente al pipeline pueden degradarse, cambiar de formato o alterar su comportamiento estadístico.**

Si una API de origen comienza a enviar precios en pesos en lugar de dólares, o si un formulario web empieza a emitir edades negativas o nulas, el pipeline ejecutará sin errores de código (código de salida exitoso `exit code 0`), pero corromperá los tableros analíticos y los modelos de Machine Learning.

En esta lección aprenderemos a implementar **Barreras de Calidad in-Pipeline (*Data Quality Gates*)** y a detectar el fenómeno de **Deriva de Datos (*Data Drift*)** antes de que impacte al negocio.

---

## 1. La Diferencia entre Validar Código vs. Validar Datos en Producción

```text
  VALIDACIÓN DE CÓDIGO (Lección 02 - CI/CD)
  ┌──────────────────────────────────────────────────────────┐
  │ Audita la SINTAXIS y LÓGICA del script en GitHub         │
  │ • ¿El código compila sin errores?                        │
  │ • ¿Las funciones unitarias responden según lo esperado?  │
  └──────────────────────────────────────────────────────────┘

  VALIDACIÓN DE DATOS (Lección 03 - In-Pipeline Quality)
  ┌──────────────────────────────────────────────────────────┐
  │ Audita el CONTENIDO de los datos vivos en tiempo de ejec.│
  │ • ¿El lote de hoy tiene la cantidad habitual de filas?   │
  │ • ¿Ocurrió un cambio brusco en la distribución de datos? │
  │ • ¿Aparecieron nulos o valores fuera de rango?           │
  └──────────────────────────────────────────────────────────┘
```

---

## 2. Barreras de Calidad in-Pipeline (Data Quality Gates)

Un **Data Quality Gate** es un punto de control automatizado insertado estratégicamente en el flujo de transformación de datos (habitualmente entre las capas Medallón Bronze $\rightarrow$ Silver y Silver $\rightarrow$ Gold).

```text
               UBICACIÓN DE DATA QUALITY GATES
 ┌──────────────┐      ┌──────────────┐      ┌──────────────┐      ┌──────────────┐
 │ CAPA BRONZE  │ ──►  │ QUALITY GATE │ ──►  │ CAPA SILVER  │ ──►  │ QUALITY GATE │ ──►  CAPA GOLD
 │ (Data Cruda) │      │   (Gate 1)   │      │ (Clean/Dedu) │      │  (Gate 2)    │
 └──────────────┘      └──────────────┘      └──────────────┘      └──────────────┘
                        • Schema Check                              • Reglas de Negocio
                        • Nullability                               • Integridad Referencial
                        • Types & Ranges                            • Monitoreo de Drift
```

### Estrategias de Manejo ante Fallos en un Quality Gate:
* **Hard Stop (Abortar el Pipeline):** Cancela la ejecución del pipeline inmediatamente y dispara alertas de emergencia (Slack/Email).
  * *Cuándo usarlo:* En fallos críticos de esquema, claves primarias duplicadas o cuando la corrupción impediría cualquier cálculo posterior en la Capa Gold.
* **Soft Quarantine / Dead Letter Queue (DLQ):** Separa las filas erróneas o fuera de contrato y las deriva a una tabla o bucket de Cuarentena (DLQ), permitiendo que las filas válidas continúen su viaje hacia la Capa Silver.
  * *Cuándo usarlo:* En sistemas de alto volumen donde perder el 100% de la carga por un 0.5% de registros defectuosos resulta inaceptable para el negocio.

---

## 3. ¿Qué es el Data Drift (Deriva de Datos) y cómo detectarlo?

El **Data Drift (Deriva de Datos)** ocurre cuando las propiedades estadísticas o la distribución de los datos de entrada cambian significativamente con el tiempo respecto a una línea de base (*Baseline* / Histórico), aunque el esquema técnico (nombres de columnas y tipos de datos) siga intacto.

```text
                 EJEMPLO VISUAL DE DATA DRIFT (Distribución de Montos)
  FRECUENCIA
     ▲
     │       LINEA DE BASE (Histórico)          LOTE ACTUAL (Anómalo / Drift)
     │            ┌─────────┐                         ┌─────────┐
     │           ┌┘         └┐                       ┌┘         └┐
     │          ┌┘           └┐                     ┌┘           └┐
     └──────────┴─────────────┴─────────────────────┴─────────────┴────────► MONTO ($)
               Promedio: $50 USD                   Promedio: $500 USD (x10)
```

### Tipos de Deriva en Ingeniería de Datos:
* **Covariate Shift (Data Drift):** Cambio en la distribución de las variables de entrada $P(X)$.  
  * *Ejemplo:* El monto promedio de compra pasa bruscamente de \$50 a \$500 por un cambio no anunciado en la moneda de origen (de ARS a USD).
* **Concept Drift:** Cambio en la relación entre las variables de entrada y la variable objetivo $P(Y \mid X)$.  
  * *Ejemplo:* Un cambio macroeconómico altera drásticamente el comportamiento de la tasa de cancelación de clientes (*Churn*).

### Técnicas Estadísticas para Detección de Data Drift:
* **Z-Score (Desviación Estándar):** Mide cuántas desviaciones estándar se aleja la media del lote actual respecto al promedio histórico:
  $$Z = \frac{\vert{}\mu_{\text{actual}} - \mu_{\text{histórico}}\vert{}}{\sigma_{\text{histórico}}}$$
  > **Regla Ssr:** Si $Z > 3.0$, existe una anomalía estadística severa en el lote de datos.
* **Population Stability Index (PSI):** Mide el cambio en la distribución de frecuencias dividiendo los datos en deciles o buckets. Un $\text{PSI} > 0.25$ indica un cambio drástico en la población de datos.
* **Prueba Kolmogorov-Smirnov (K-S Test):** Prueba no paramétrica que compara si dos muestras continuas provienen de la misma distribución subyacente.

---

## 4. Implementación de Data Quality Gates y Drift Monitor en Python

A continuación se muestra un módulo reutilizable en Python que combina la validación in-pipeline con la detección de Data Drift por Z-Score:

```python
import pandas as pd
import numpy as np

class DataDriftAndQualityGate:
    def __init__(self, baseline_mean: float, baseline_std: float, z_threshold: float = 3.0):
        self.baseline_mean = baseline_mean
        self.baseline_std = baseline_std
        self.z_threshold = z_threshold

    def evaluate_batch(self, df: pd.DataFrame, target_col: str) -> dict:
        results = {"status": "PASSED", "alerts": []}

        # 1. Quality Check: Validar Nulos
        null_count = df[target_col].isnull().sum()
        if null_count > 0:
            results["status"] = "WARNING"
            results["alerts"].append(f"❌ QUALITY GATE: {null_count} valores nulos en '{target_col}'.")

        # 2. Data Drift Check: Calcular Z-Score de la media actual
        current_mean = df[target_col].mean()
        
        if self.baseline_std > 0:
            z_score = abs(current_mean - self.baseline_mean) / self.baseline_std
            
            if z_score > self.z_threshold:
                results["status"] = "DRIFT_DETECTED"
                results["alerts"].append(
                    f"🚨 DATA DRIFT ALERT: La media actual (${current_mean:.2f}) "
                    f"se desvía Z={z_score:.2f} de la base (${self.baseline_mean:.2f})."
                )

        return results
```

---

## 🏋️‍♂️ Práctica de la Lección 03

1. Ubicate en la carpeta `practica/modulo_08/` de tu repositorio local.
2. Creá el archivo `ej_03_data_drift_quality_gates.py`.
3. Escribí un script Python que simule el monitoreo in-pipeline de dos lotes diarios (Lote Normal vs. Lote con Data Drift):

```python
import pandas as pd
import numpy as np

# 1. Datos Históricos de Referencia (Baseline: Ventas de los últimos 6 meses)
np.random.seed(42)
baseline_sales = np.random.normal(