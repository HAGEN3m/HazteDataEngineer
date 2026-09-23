```
# 🛠️ HazteDataEngineer (HAGEN3m)

&gt; **De Cero a Ingeniero de Datos Semi-Senior (Ssr) / Senior Ready**  
&gt; *Guía libre de humo, arquitectura real, teoría con rigor universitario y práctica de producción sin falsas promesas ni atajos.*

---

## 🎯 Visión y Filosofía Pedagógica

Este repositorio es una formación integral y rigurosa en **Ingeniería de Datos y Sistemas Distribuidos**, diseñada para llevar al estudiante desde las bases computacionales fundamentales hasta los estándares arquitectónicos exigidos por las empresas líderes del sector [1, 7, 8].

### 📐 La Metodología de 4 Capas (Scaffolding Universitario)
Cada módulo no es una simple lista de herramientas; está diseñado con un andamiaje progresivo en 4 niveles para garantizar una comprensión profunda:

```

[Nivel 1: Intuición y Fundamentos] ──&gt; [Nivel 2: Práctica Guiada (Hands-On)] ──&gt; [Nivel 3: Fricción Real y Fallos] ──&gt; [Nivel 4: Patrón Enterprise (Ssr/Sr)]

```

1. **Nivel 1 — Intuición y Fundamentos (Sin Asunciones)**: Explicación conceptual clara del problema de negocio/arquitectura, modelos mentales e internas del sistema (*database/OS internals*) [8, 9].
2. **Nivel 2 — Práctica Guiada (Hands-On)**: Implementación local paso a paso (*Hello World* listo para producción) [10].
3. **Nivel 3 — Fricción y Fallos de Producción**: Trabajo bajo condiciones extremas (escala, memoria, CPU, I/O, latencia, datos corruptos y *schema drift*) [5].
4. **Nivel 4 — Patrones Enterprise**: Automatización CI/CD, observabilidad, contratos de datos, idempotencia, resiliencia y FinOps [5, 9].

&gt; **🎟️ Desafíos Basados en Tickets de Producción (Jira / GitHub Issues)**  
&gt; Cada módulo culmina con la simulación de un ticket real de ingeniería, donde resolverás problemas complejos con el mismo estándar de calidad y resiliencia que un equipo Senior.

---

## 💡 Principios Innegociables de Ingeniería

1. **Ingeniería de Software Primero, Herramientas Después**: Código limpio, tipado estático, testing unitario, modularidad, control de versiones y CI/CD antes de levantar clústeres complejos [2, 11].
2. **Pragmatismo sobre Complejidad**: Si una consulta SQL u optimización columnar en DuckDB resuelve el problema en milisegundos, no introducimos infraestructura distribuida pesada [2, 12].
3. **Calidad, Gobernanza Preventiva e Idempotencia**: La degradación silenciosa de datos (*schema drift*) es inaceptable. Los pipelines deben ser idempotentes y los datos deben estar protegidos por contratos automatizados [2, 5].
4. **Resiliencia e Inyección de Fallas (*Chaos Data Engineering*)**: Un sistema de producción debe estar diseñado para tolerar caídas de red, registros malformados y reintentos con retraso exponencial [13].
5. **Rigor de Ciencias de la Computación (CS Foundations)**: Comprender *cómo* funcionan los motores por dentro (LSM-Trees vs. B-Trees, almacenamiento columnar, particionado, *shuffling*, Teorema CAP) [9, 14].

---

## 🗺️ Roadmap de Contenidos (Módulos 00 - 09)

### 🔹 `modulo_00_entorno_y_git` — Entorno de Desarrollo, CLI &amp; Control de Versiones
* **Nivel 1 — Fundamentos**: Internas del SO (procesos, hilos, I/O, descriptores de archivos, streams `stdin`/`stdout`/`stderr`).
* **Nivel 2 — Práctica**: CLI avanzado de Linux/Unix, Gitflow profesional y gestión de entornos virtuales con `venv` y `uv`.
* **Nivel 3 — Fricción**: Scripting defensivo en Bash (`set -euo pipefail`), inspección de recursos en tiempo real (`top`, `htop`, `lsof`).
* **Nivel 4 — Enterprise**: Automatización con `Makefile` y configuración de **Hooks de Git (`pre-commit`)** para linters (`ruff`, `black`, `mypy`).
* 🎟️ **Ticket Práctico**: `DE-101`: *Scripting de automatización de entorno local con validación estricta y Git Hooks integrados.*

---

### 🔹 `modulo_01_python` — Python Avanzado, Tipado &amp; Procesamiento Eficiente
* **Nivel 1 — Fundamentos**: Modelo de memoria de Python, mutabilidad, referencias y el impacto del GIL (*Global Interpreter Lock*).
* **Nivel 2 — Práctica**: POO avanzada, `dataclasses`, tipado estático estricto (`mypy`) y empaquetado modular.
* **Nivel 3 — Fricción**: Procesamiento streaming in-memory de archivos multichunk (ej. 50 GB en 8 GB de RAM) con generadores e iteradores. Introducción a **Polars** para manipulación multihilo ultrarrápida [9, 10].
* **Nivel 4 — Enterprise**: Unit testing avanzado con `pytest` (*fixtures*, *mocking* de APIs/DBs) y profiling de CPU/memoria (`cProfile`, `memory_profiler`).
* 🎟️ **Ticket Práctico**: `DE-102`: *Refactorización de pipeline monolítico en librería modular tipada con streaming e suite de pruebas.*

---

### 🔹 `modulo_02_sql` — SQL Avanzado, Internas de Motores &amp; OLAP Local
* **Nivel 1 — Fundamentos**: *Database Internals*: Almacenamiento por Filas (OLTP) vs. Columnar (OLAP), B-Trees vs. LSM-Trees [9].
* **Nivel 2 — Práctica**: Window Functions avanzadas (`ROW_NUMBER`, `RANK`, `LAG`, `LEAD`), CTEs complejas y JOINs optimizados [10].
* **Nivel 3 — Fricción**: Análisis físico de consultas (`EXPLAIN ANALYZE`), eliminación de *Sequential Scans*, estrategias de particionado y *salting*.
* **Nivel 4 — Enterprise**: **Motor OLAP Local**: Uso de **DuckDB** para ejecutar consultas analíticas sobre Parquet a alta velocidad sin infraestructura dedicada [9, 12].
* 🎟️ **Ticket Práctico**: `DE-201`: *Optimización de consulta analítica crítica y migración a motor columnar DuckDB.*

---

### 🔹 `modulo_03_docker_y_entornos` — Contenedores, Aislamiento e Infraestructura como Código (IaC)
* **Nivel 1 — Fundamentos**: Virtualización a nivel de SO: Linux Namespaces, Cgroups y aislamiento de Kernel.
* **Nivel 2 — Práctica**: Contenedorización de microservicios de datos y bases relacionales con Docker y `docker-compose` [15].
* **Nivel 3 — Fricción**: *Multi-stage builds* para reducir imágenes de producción a &lt;100 MB, aislamiento de redes internas y volúmenes persistentes.
* **Nivel 4 — Enterprise**: **Infraestructura como Código (IaC) con Terraform**: Aprovisionamiento declarativo y versionado de buckets S3/MinIO, almacenes analíticos y roles IAM [9, 15].
* 🎟️ **Ticket Práctico**: `DE-301`: *Containerización multi-etapa e infraestructura declarativa con Terraform para la plataforma.*

---

### 🔹 `modulo_04_mod_dim_y_olap` — Modelado Dimensional &amp; Data Warehousing (Kimball)
* **Nivel 1 — Fundamentos**: Por qué 3NF falla en analítica masiva: Transición de OLTP a OLAP y principios de Kimball [12].
* **Nivel 2 — Práctica**: Construcción de Esquemas en Estrella (*Star Schema*) y Copo de Nieve (*Snowflake Schema*) [12].
* **Nivel 3 — Fricción**: Dimensiones de Cambio Lento (**SCD Tipo 1, Tipo 2 y Tipo 3**) y Tablas de Hechos sin Hechos (*Factless Fact Tables*) [12].
* **Nivel 4 — Enterprise**: *Cumulative Table Design* y estructuras anidadas/ARRAYs para analítica de eventos a gran escala evitando JOINs masivos.
* 🎟️ **Ticket Práctico**: `DE-401`: *Diseño e implementación de SCD Tipo 2 para rastreo histórico de dimensiones.*

---

### 🔹 `modulo_05_dbt_y_capa-semantica` — Transformación Declarativa, Medallón &amp; Analytics Engineering
* **Nivel 1 — Fundamentos**: Paradigma ELT frente a ETL tradicional y computación *in-warehouse* [16].
* **Nivel 2 — Práctica**: Estructuración modular de dbt Core en 3 capas (**Staging, Intermediate, Marts**) [17].
* **Nivel 3 — Fricción**: **Arquitectura Medallón Estricta (Bronce -&gt; Plata -&gt; Oro)**: Reglas de limpieza, deduplicación y conformación [18].
* **Nivel 4 — Enterprise**: Contratos en dbt (`dbt contracts`), *snapshots* para SCDs, dbt tests de relación/unicidad y definición de la Capa Semántica / Métricas [17, 19].
* 🎟️ **Ticket Práctico**: `DE-501`: *Pipeline Medallón completo en dbt con contratos strictly enforced, snapshots y capa de métricas.*

---

### 🔹 `modulo_06_DataContracts_y_GobernanzaPreventiva` — Contratos de Datos &amp; CI/CD Enforcement
* **Nivel 1 — Fundamentos**: La crisis del *Schema Drift* y los cambios silenciosos que rompen tableros de producción [5].
* **Nivel 2 — Práctica**: Especificaciones formales en YAML utilizando el estándar Open Data Contract Standard (ODCS) o Soda [5, 19].
* **Nivel 3 — Fricción**: Matriz de cambios compatibles vs. incompatibles (*breaking changes*) y políticas de deprecación.
* **Nivel 4 — Enterprise**: **Enforcement automatizado en CI/CD**: GitHub Actions con `datacontract CLI` / `Soda Core` para bloquear Pull Requests con *breaking changes* [5, 9].
* 🎟️ **Ticket Práctico**: `DE-601`: *Implementación de Data Contract en ingesta y status check en GitHub Actions.*

---

### 🔹 `modulo_07_apache_airflow` — Orquestación, Idempotencia &amp; Workflow Management
* **Nivel 1 — Fundamentos**: Principios de orquestación de workflows vs. cron jobs tradicionales [19].
* **Nivel 2 — Práctica**: Construcción de DAGs con la TaskFlow API moderna en Python [19].
* **Nivel 3 — Fricción**: **Idempotencia estricta**, estrategias de **Backfilling** histórico sin duplicación y reintentos con retraso exponencial [19].
* **Nivel 4 — Enterprise**: *Deferrable Operators*, sensores dinámicos, arquitectura de colas de mensajes fallidos (*Dead-Letter Queues - DLQ*) y orquestación híbrida Airflow-dbt [19].
* 🎟️ **Ticket Práctico**: `DE-701`: *DAG de Airflow idempotente para orquestación diaria con backfilling y manejo de DLQ.*

---

### 🔹 `modulo_08_DO_CI_CD_OBS` — DataOps, Observabilidad de Datos &amp; Chaos Engineering
* **Nivel 1 — Fundamentos**: Filosofía DataOps y observabilidad de datos (frescura, volumen, esquema, distribución, linaje) vs. monitoreo de infra [9, 20].
* **Nivel 2 — Práctica**: CI/CD automatizado con GitHub Actions para linter y test unitario de pipelines [20].
* **Nivel 3 — Fricción**: **Inyección de Fallas (*Chaos Data Engineering*)**: Simulación de datos corruptos y latencias extremas para evaluar la tolerancia a fallos.
* **Nivel 4 — Enterprise**: Pruebas en tiempo de ejecución con **Soda Core / Great Expectations**, linaje a nivel de columna con **OpenLineage** y alertas automáticas [9, 20].
* 🎟️ **Ticket Práctico**: `DE-801`: *Pipeline CI/CD completo con observabilidad, linaje OpenLineage y Chaos Test de corrupción.*

---

### 🔹 `modulo_09_PySpark_Arq_Lake` — Cómputo Distribuido, Open Table Formats &amp; Streaming
* **Nivel 1 — Fundamentos**: Arquitectura Spark: Driver, Workers, RDDs, DataFrames y optimización de ejecución [14].
* **Nivel 2 — Práctica**: Transformaciones Batch distribuidas en PySpark sobre Object Storage [14].
* **Nivel 3 — Fricción**: Internas de Spark: optimización de memoria, *shuffling*, técnicas de *salting* para solucionar datos sesgados (*data skew*) y resolución del problema de archivos pequeños (*small file problem*).
* **Nivel 4 — Enterprise**: **Formatos de Tabla Abierta (Apache Iceberg / Delta Lake)** con transacciones ACID, viajes en el tiempo (*time travel*) y mutaciones; **Procesamiento Streaming Real-Time con Apache Kafka** y PySpark Structured Streaming usando marcas de agua (*watermarks*) [9, 14, 21].
* 🎟️ **Ticket Práctico**: `DE-901`: *Lakehouse en tiempo real consumiendo de Kafka, aplicando marcas de agua y escribiendo en tablas transaccionales Apache Iceberg/Delta Lake.*

---

## 📂 Proyectos Prácticos Destacados (Capstones)

| Proyecto | Descripción Arquitectónica | Stack Tecnológico |
| :--- | :--- | :--- |
| **`end-to-end-pipeline`** | Ingesta declarativa con `dlt`, infraestructura provisionada con Terraform, transformación Medallón con dbt, validación estricta de contratos con Soda Core, orquestación idempotente en Airflow y CI/CD en GitHub Actions [22]. | Python (`dlt`), Terraform, PostgreSQL/Snowflake, dbt Core, Soda Core, Airflow, GitHub Actions |
| **`stream-processing-lab`** | Ingesta continua con Apache Kafka, transformaciones agregadas sobre ventanas temporales en PySpark, manejo de eventos fuera de orden mediante *watermarks* y almacenamiento transaccional con *time travel* [21]. | Apache Kafka, PySpark Structured Streaming, Delta Lake / Apache Iceberg, Docker |
| **`data-lake-analytics`** | Analytics Lakehouse sobre S3/MinIO con almacenamiento Parquet e Iceberg, ejecuciones analíticas locales de alto rendimiento con DuckDB, consultas de viajes en el tiempo y compacción física Z-Order / *Liquid Clustering* [9, 12, 14]. | AWS S3 / MinIO, PySpark, DuckDB, Apache Iceberg |

---

## 🚀 Cómo Iniciar el Camino

1. **Clona el repositorio**:
   ```bash
   git clone https://github.com/HAGEN3m/HazteDataEngineer.git
   cd HazteDataEngineer

```

1. **Revisa la guía del** **modulo\_00\_entorno\_y\_git** y ejecuta la configuración inicial de tu entorno de desarrollo.
2. **Resuelve los ejercicios y completa los Tickets Prácticos** al finalizar cada módulo.

---

## 🤝 Contribuciones y Comunidad

Este proyecto es de código abierto y de libre acceso. Las contribuciones, sugerencias y Pull Requests con mejoras pedagógicas o correcciones son bien recibidas[7].

Si este recurso aporta valor a tu carrera profesional, **no olvides dejarle una ⭐ al repositorio** para ayudar a más futuros Data Engineers[7].

*Licencia MIT — Desarrollado con rigor técnico e impacto real.*