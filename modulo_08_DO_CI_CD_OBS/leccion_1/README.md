# 🚀 Lección 01: Fundamentos de DataOps e Integración Continua para Data Engineering

En los módulos anteriores aprendiste a procesar datos con Python y Polars (Módulo 01), optimizar bases de datos (Módulo 02), empaquetar entornos aislados con Docker (Módulo 03), diseñar Data Warehouses en capas Medallón (Módulo 04), transformar modelos con dbt (Módulo 05), implementar Data Contracts (Módulo 06) y orquestar flujos idempotentes con Apache Airflow (Módulo 07).

Hasta este punto tenemos todas las piezas técnicas individuales. Pero en un equipo de ingeniería maduro surge un desafío crítico: **¿Cómo garantizamos que cuando varios ingenieros trabajan en paralelo, agregan nuevos pipelines o modifican código existente, no rompan el entorno de producción ni introduzcan inconsistencias de datos?**

En este Módulo 08 aprenderemos la disciplina que separa a los proyectos de juguete de las plataformas Enterprise: **DataOps, CI/CD y Observabilidad**.

---

## 1. ¿Qué es DataOps y por qué es indispensable?

**DataOps (Data Operations)** no es un software específico ni una herramienta; es una filosofía de trabajo y metodología cultural que fusiona las prácticas de **Agile** (Desarrollo Ágil), **DevOps** y **Gobernanza Lean** aplicadas al ciclo de vida completo de la ingeniería de datos.

```text
               EL CICLO DE VIDA CONTINUO DE DATAOPS
  ┌───────────────────────────────────────────────────────────┐
  │  1. PLAN  ──►  2. CODE  ──►  3. TEST  ──►  4. BUILD      │
  │     ▲                                           │         │
  │     │                                           ▼         │
  │  8. MONITOR ◄── 7. OBSERVE ◄── 6. DEPLOY ◄── 5. RELEASE   │
  └───────────────────────────────────────────────────────────┘
```

### El Problema del Desarrollo Tradicional Ad-Hoc
En organizaciones sin cultura DataOps:
* Un ingeniero modifica una consulta SQL directamente en el entorno de producción (*"Hot-fixing"* en la base de datos).
* Las pruebas de código y calidad de datos se realizan de forma manual y esporádica.
* Un cambio en una tabla afecta a múltiples tableros de PowerBI sin que nadie lo sepa hasta que un ejecutivo reclama datos erróneos.
* Desplegar una nueva funcionalidad tarda semanas por miedo a romper la plataforma.

### La Solución DataOps
DataOps automatiza la construcción, prueba, despliegue y monitoreo de los componentes de datos mediante pipelines de código versionados en Git, reduciendo el ciclo de entrega de semanas a minutos con cero errores no detectados en producción.

---

## 2. Los 4 Pilares Fundamentales de DataOps

```text
                             LOS 4 PILARES DE DATAOPS
                                         │
         ┌───────────────────────────────┼───────────────────────────────┐
         ▼                               ▼                               ▼
1. INTEGRACIÓN CONTINUA (CI)    2. ENTORNOS AISLADOS (Sandbox)  3. PRUEBAS AUTOMÁTICAS (Testing)
   • Linting & Análisis Estático   • Dev, Staging y Prod           • Unit Tests (pytest)
   • Integración en Git/PRs        • Base de datos efímera         • Data Quality Tests (dbt/GE)
```

1. **Integración Continua (CI - Continuous Integration):** Cada cambio en los archivos Python, modelos dbt, DAGs de Airflow o scripts SQL debe ser validado automáticamente por un servidor de CI (ej. GitHub Actions) antes de fusionarse a la rama principal (`main`).
2. **Entornos Aislados (Isolated Sandboxes):** Ningún ingeniero debe desarrollar o probar código sobre la base de datos de producción. Cada desarrollador trabaja en un entorno de Desarrollo (`dev`) o Pruebas (`staging`) totalmente aislado, asegurando que las fallas afecten únicamente a entornos efímeros.
3. **Pruebas Automatizadas en Dos Niveles (Dual-Layer Testing):** En ingeniería de datos, el código puede estar sintácticamente correcto pero los datos pueden ser basura. Por eso DataOps exige validar dos capas:
   * **Pruebas de Código (*Code Testing*):** Pytest, linters de estilo, análisis sintáctico de SQL.
   * **Pruebas de Datos (*Data Testing*):** Validaciones de esquema, nulidad, duplicados y reglas de negocio sobre los datos producidos.
4. **Monitoreo Continuo y Observabilidad:** Sensórica en tiempo real sobre la latencia de los pipelines, la frescura de los datos (*Data Freshness*), el volumen de filas procesadas y las anomalías en la distribución de los valores (*Data Drift*).

---

## 3. La Diferencia Crucial: DevOps vs. DataOps

Aunque DataOps hereda los principios de DevOps, existe una diferencia fundamental que hace a la ingeniería de datos única: **el estado persistente de los datos**.

```text
  DEVOPS TRADICIONAL (Software de Aplicación)
  ┌──────────────────────────────────────────────────────────┐
  │  Código Source  ──►  Compilación/Build  ──►  Deploy Binario│
  │  (El estado es volátil o aislado en la app)              │
  └──────────────────────────────────────────────────────────┘

  DATAOPS (Ingeniería de Datos)
  ┌──────────────────────────────────────────────────────────┐
  │  Código (SQL/Python)  +  DATOS EN VIVO (Persistentes)     │
  │           │                       │                      │
  │           ▼                       ▼                      │
  │  Un cambio de código puede alterar o CORROMPER terabytes │
  │  de datos históricos irreversibles en la base analítica. │
  └──────────────────────────────────────────────────────────┘
```

En DevOps tradicional, si un microservicio desplegado tiene un bug, basta con hacer un **Rollback** (revertir al ejecutable anterior). En DataOps, si un script defectuoso sobreescribió o borró una tabla de hechos de 500 millones de filas en el Data Warehouse, hacer un rollback de código no restaura la base de datos; exige una estrategia de recuperación y reprocesamiento idempotente.

---

## 📊 Matriz Comparativa: Desarrollo Ad-Hoc vs. Cultura DataOps

| Criterio | Desarrollo Tradicional Ad-Hoc | Desarrollo bajo Cultura DataOps |
| :--- | :--- | :--- |
| **Control de Cambios** | Edición directa en DB o servidores | Todo el código versionado en Git (IaC) |
| **Entornos de Trabajo** | Compartido o directamente Producción | Dev / Staging / Prod aislados |
| **Validación de Código** | Manual ("Corre en mi máquina") | Automatizada mediante CI/CD (GitHub Actions) |
| **Detección de Errores** | El cliente/usuario reporta tableros rotos | Alertas preventivas in-pipeline antes del consumo |
| **Confianza en Despliegues** | Miedo a hacer deploy el viernes | Múltiples deploys diarios seguros e invisibles |

---

## 🏋️‍♂️ Práctica de la Lección 01

1. Ubicate en la carpeta `practica/modulo_08/` de tu repositorio local.
2. Creá el archivo `ej_01_fundamentos_dataops.py`.
3. Escribí un script Python que simule un Arnés de Pruebas DataOps (*DataOps CI Pipeline Simulator*) que ejecute tres fases de validación automática sobre un cambio de código antes de autorizar su promoción a producción:

```python
import pandas as pd
import sys

# 1. Código SQL propuesto en una Pull Request
SQL_PROPOSED_QUERY = """
SELECT
    cliente_id,
    SUM(monto_usd) AS total_ventas,
    COUNT(transaccion_id) AS cantidad_ordenes
FROM analytics.stg_ventas
WHERE estado = 'COMPLETADA'
GROUP BY cliente_id;
"""

# 2. Dataset simulado cargado en entorno de