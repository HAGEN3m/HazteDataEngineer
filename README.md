```
# 🚀 Data Engineering: De 0 a Semi-Senior (Ssr)

&gt; *Un roadmap honesto, práctico y de código abierto para dominar la Ingeniería de Datos moderna sin atajos ni falsas promesas.*

---

## 📌 ¿Por qué existe este repositorio?

Este proyecto nace para acompañar a todas aquellas personas que se encuentran en el limbo de querer aprender programación e ingeniería de datos, pero solo encuentran un mar de contenido comercial diseñado para **venderles promesas en lugar de enseñarles habilidades reales**.

Mi objetivo es facilitarte la teoría, la arquitectura y la práctica necesarias para que no tengas que sufrir la desorientación y la frustración que viví en mi propio camino. Quería construir el recurso que a mí me hubiera gustado encontrar cuando arranqué desde el cero absoluto.

---

## 🧠 La Filosofía del Proyecto

### 1. Sin atajos ni recetas mágicas
La ingeniería de datos no se aprende de un día para el otro. **No existe el "0 a experto en 12 horas"**. El dominio técnico real exige tiempo, resiliencia ante el error, horas de vuelo en consola y pensamiento crítico frente a problemas de arquitectura.

### 2. Estudio activo + Inmersión pasiva
Para dominar esta disciplina, el código en pantalla no alcanza por sí solo. Es fundamental acompañar la práctica diaria con consumo pasivo de contenido técnico (documentaciones, artículos de ingeniería, YouTube, podcasts y debates de la industria) para incorporar de forma natural la jerga, los patrones de diseño y la cultura de la comunidad.

### 3. Uso consciente y defensivo de la Inteligencia Artificial
La Inteligencia Artificial es una herramienta extraordinaria si se la utiliza como un **tutor socrático**: usala para preguntar conceptos, pedir explicaciones de arquitectura o entender el *"por qué"* detrás de un error. 

&gt; ⚠️ **Regla de oro del repositorio**: Pasar una consigna a la IA, copiar el código generado, lograr que ejecute y asumir que entendiste es una ilusión de competencia. Si no podés explicar qué hace cada línea de tu script, no estás aprendiendo.

---

## 🌊 Las Corrientes Subterráneas (*Undercurrents*)

Inspirado en los fundamentos de la ingeniería de datos moderna, este contenido no solo te enseña a usar herramientas, sino a dominar los 6 pilares transversales que definen a un **Ingeniero de Datos Semi-Senior (Ssr)**:

1. **Seguridad &amp; Privacidad**: Manejo seguro de credenciales (`.env`), principio de menor privilegio y enmascaramiento de datos sensibles (PII).
2. **Calidad de Datos &amp; Gobernanza (*Shift-Left*)**: Detención preventiva del dato corrupto en origen mediante **Data Contracts (ODCS)** y validaciones automáticas.
3. **Arquitectura de Datos**: Elección consciente entre OLTP y OLAP, **Modelado Dimensional Kimball** y **Arquitectura Medallón** (Bronze, Silver, Gold).
4. **Orquestación e Idempotencia**: Diseño de pipelines en los que reejecutar un flujo con el mismo input no genera duplicados ni rompe métricas.
5. **DataOps e Ingeniería de Software**: Versionado estricto con Git, entornos aislados con Docker, unit testing (`pytest`) e Integración Continua (CI/CD).
6. **Observabilidad &amp; FinOps**: Monitoreo de frescura, volumen, esquemas y optimización del costo de cómputo Cloud.

---

## 🗺️ Temario General (Roadmap de 0 a Ssr)

### 🔴 FASE 1: CIMIENTOS DE PROGRAMACIÓN Y SISTEMAS (Nivel Inicial)
* **Módulo 0: Entorno de Trabajo, Unix Shell &amp; Versionado**  
  Consola Linux/Bash desde cero (`cd`, `ls`, `mkdir`, `grep`), Git, GitHub, ramas, PRs y `.gitignore`.
* **Módulo 1: Programación Modular y Código Defensivo en Python**  
  Variables, estructuras nativas, control de flujo, funciones puras, manejo de excepciones (`try/except`) y logging.
* **Módulo 2: SQL de Alto Rendimiento y Modelo Relacional**  
  Orden de ejecución física en SQL, JOINs, agregaciones, funciones de ventana (`ROW_NUMBER`, `RANK`, `LAG`, `LEAD`) y tratamiento de `NULL`.

### 🟡 FASE 2: PROCESAMIENTO, CONTENEDORES Y ALMACENAMIENTO OLAP (Nivel Intermedio)
* **Módulo 3: Procesamiento Tabular en Memoria (Pandas vs. Polars)**  
  Vectorización (`numpy.select`), reestructuración (`melt`/`pivot_table`) y migración a Polars (ejecución *eager* vs. *lazy*).
* **Módulo 4: Contenedores e Infraestructura como Código (Docker &amp; Terraform)**  
  Creación de imágenes inmutables con `Dockerfile`, orquestación de servicios con `Docker Compose` e IaC con Terraform.
* **Módulo 5: Almacenamiento Columnar &amp; Modelado Dimensional**  
  OLTP vs. OLAP (DuckDB), Apache Parquet, Modelado Kimball (Fact/Dim, SCD Tipo 1 y 2) y Arquitectura Medallón.

### 🟢 FASE 3: ARQUITECTURA ENTERPRISE, PIPELINES Y GOBERNANZA (Nivel Ssr)
* **Módulo 6: Analytics Engineering (dbt Core &amp; Capa Semántica)**  
  Paradigma ELT, Jinja/SQL, materializaciones incrementales y métricas centradas con dbt MetricFlow.
* **Módulo 7: Gobernanza Preventiva &amp; Data Contracts**  
  Especificación ODCS en YAML, validación en pipelines de CI/CD con `datacontract-cli` y solución de *Schema Drift*.
* **Módulo 8: Orquestación e Idempotencia (Apache Airflow)**  
  Diseño de DAGs en Python, operadores, sensores, retries y ejecuciones idempotentes.
* **Módulo 9: DataOps, CI/CD &amp; Observabilidad de Datos**  
  Pruebas automáticas con `pytest`, linters (`sqlfluff`/`flake8`), GitHub Actions y monitoreo de salud del pipeline.
* **Módulo 10: Big Data, Cómputo Distribuido &amp; Lakehouse**  
  Procesamiento masivo por lotes con PySpark y formatos de tabla abiertos (Delta Lake / Iceberg).

---

## 🛠️ Stack Tecnológico

| Capa | Herramientas |
| :--- | :--- |
| **Lenguajes** | SQL, Python 3.10+, Bash/Unix Shell |
| **Procesamiento &amp; Transformación** | Pandas, Polars, dbt Core, PySpark |
| **Almacenamiento &amp; OLAP** | PostgreSQL, DuckDB, Apache Parquet, Delta Lake |
| **Infraestructura &amp; Orquestación** | Docker, Docker Compose, Terraform, Apache Airflow |
| **Calidad, Gobernanza &amp; CI/CD** | Data Contracts (ODCS), `pytest`, `datacontract-cli`, GitHub Actions |

---

## 🧪 Autoevaluación Práctica (Estilo SQLZoo / CI/CD)

Cada módulo práctico incluye ejercicios con **autoevaluación automática**:
1. Escribís tu consulta SQL o script en el archivo correspondiente.
2. Ejecutás `pytest` localmente para validar los datos sobre un motor DuckDB en memoria.
3. Al hacer `git push` a GitHub, un flujo de **GitHub Actions** valida automáticamente tu solución y te otorga el tilde verde (🟢).

---

## 📁 Estructura del Repositorio

```text
.
├── README.md
├── .gitignore
├── .github/
│   └── workflows/
│       └── autograding.yml
├── modulo-00-entorno-y-git/
├── modulo-01-python-defensivo/
├── modulo-02-sql-alto-rendimiento/
├── modulo-03-procesamiento-pandas-polars/
├── modulo-04-docker-y-entornos/
├── modulo-05-modelado-dimensional-olap/
├── modulo-06-dbt-y-capa-semantica/
├── modulo-07-data-contracts/
├── modulo-08-airflow-e-idempotencia/
├── modulo-09-dataops-y-observabilidad/
└── modulo-10-pyspark-y-lakehouse/

```

---

## 👤 Autor &amp; Contacto

Creado por **Tomás Martín Herlein**

* **LinkedIn**: [Tu Perfil de LinkedIn](#)
* **GitHub**: [Tu Usuario de GitHub](#)

---

*¡Las contribuciones, correcciones y Pull Requests son más que bienvenidas! Si este recurso te sirvió, dejale una ⭐ al repositorio.*