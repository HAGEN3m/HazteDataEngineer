# 🐳 Lección 03.B (Módulo 03): Orquestación Multicontenedor con Docker Compose: Healthchecks y Persistencia

&gt; **Propósito**: Dominar la orquestación de infraestructuras complejas de datos mediante Docker Compose, implementando controles de salud defensivos (*Healthchecks*), orden estricto de arranque (`service_healthy`), manejo seguro de variables de entorno y perfiles para desplegar stacks de producción resilientes (PostgreSQL, MinIO y Airflow).

---

## 📌 1\. El Problema del Arranque Sincrónico (`depends_on` Clásico)

En arquitecturas de datos distribuidas, los servicios dependen unos de otros. Por ejemplo, Apache Airflow o una API de Python no pueden iniciar si la base de datos PostgreSQL no está lista para aceptar conexiones.

```
❌ ANTI-PATRÓN CLÁSICO:
depends_on:
  - postgres_db  # Solo espera a que el contenedor inicie el proceso, NO a que Postgres esté listo.

```

### ¿Por qué se rompen los contenedores?

Un contenedor se considera "en ejecución" (`running`) en el instante en que su proceso principal (PID 1) arranca. Sin embargo, PostgreSQL o MySQL tardan varios segundos en inicializar el motor de almacenamiento, realizar la recuperación de WALs y abrir el puerto TCP `5432`. Si la app se conecta inmediatamente, arroja un error `Connection Refused` y colapsa.

---

## 🔬 2\. Healthchecks Defensivos y `condition: service_healthy`

Para resolver el problema del arranque en falso, definimos **Healthchecks** (chequeos de estado de salud) en cada servicio y condicionamos la dependencia al estado `service_healthy`.

```
[ PostgreSQL Container ] ─── (pg_isready) ───&gt; [ Estado: HEALTHY ]
                                                         │
                                                         ▼ (Permite arrancar)
[ Airflow Init / Migration ] ────────────────────────────┘

```

### Anatomía de un Healthcheck Defensivo:

```
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
  interval: 5s     # Frecuencia de chequeo
  timeout: 5s      # Tiempo máximo de espera por cada prueba
  retries: 5       # Intentos fallidos consecutivos antes de marcar 'UNHEALTHY'
  start_period: 10s # Margen de tiempo para la inicialización inicial del servicio

```

---

## 🛠️ 3\. Healthchecks Frecuentes en el Ecosistema de Datos

| Servicio                   | Comando de Healthcheck (`test`)                                   |
| -------------------------- | ----------------------------------------------------------------- |
| **PostgreSQL**             | `["CMD-SHELL", "pg_isready -U $$POSTGRES_USER -d $$POSTGRES_DB"]` |
| **MinIO (Object Storage)** | \`["CMD-SHELL", "curl -f http://localhost:9000/minio/health/live |
| **Redis**                  | \`["CMD-SHELL", "redis-cli ping                                  |
| **HTTP APIs / FastAPI**    | \`["CMD-SHELL", "curl -f http://localhost:8000/health            |

---

## ⚡ 4\. Perfiles (`profiles`) y Gestión de Recursos

En entornos locales o de testing, no siempre necesitas levantar todos los servicios pesados del stack simultáneamente (ej. Spark Cluster, Kafka, Superset).

Docker Compose permite agrupar servicios bajo **Perfiles**:

```
services:
  postgres:
    image: postgres:16-alpine
    # Se ejecuta siempre por defecto

  jupyter_notebook:
    image: jupyter/pyspark-notebook
    profiles: ["analytics"] # Solo se levanta si se especifica el perfil

  kafka:
    image: bitnami/kafka
    profiles: ["streaming"] # Solo se levanta para pruebas de tiempo real

```

### Ejecución por Perfil:

```
# Levanta solo el stack base (Postgres)
docker compose up -d

# Levanta Postgres + el entorno analítico con Jupyter
docker compose --profile analytics up -d

```

---

## 🏋️‍♂️ Ejercicio Práctico Hands-On: Stack Resiliente (Postgres + MinIO + App)

Crea el archivo `docker-compose.yml` en la raíz de tu proyecto con una arquitectura de datos completa y defensiva:

```
version: '3.8'

networks:
  data_pipeline_net:
    driver: bridge

volumes:
  postgres_data:
  minio_data:

services:
  # 1. Base de Datos Relacional (Metastore / OLTP)
  postgres_db:
    image: postgres:16-alpine
    container_name: postgres_db
    networks:
      - data_pipeline_net
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-de_user}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-de_password}
      POSTGRES_DB: ${POSTGRES_DB:-analytics}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $${POSTGRES_USER} -d $${POSTGRES_DB}"]
      interval: 5s
      timeout: 5s
      retries: 5
      start_period: 10s
    restart: unless-stopped

  # 2. Object Storage S3-Compatible (Data Lake local)
  minio_s3:
    image: minio/minio:RELEASE.2024-01-18T22-51-28Z
    container_name: minio_s3
    networks:
      - data_pipeline_net
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_ROOT_USER:-admin}
      MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD:-admin12345}
    volumes:
      - minio_data:/data
    ports:
      - "9000:9000"
      - "9001:9001"
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:9000/minio/health/live || exit 1"]
      interval: 5s
      timeout: 5s
      retries: 5
      start_period: 10s
    restart: unless-stopped

  # 3. Script de Ingesta / Pipeline Python (Esperará a que Postgres y MinIO estén listos)
  data_ingestion_app:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: data_ingestion_app
    networks:
      - data_pipeline_net
    environment:
      DB_HOST: postgres_db
      S3_HOST: minio_s3:9000
    depends_on:
      postgres_db:
        condition: service_healthy
      minio_s3:
        condition: service_healthy
    restart: "no"

```

---

## 🧠 Checkpoint de Autoevaluación

1. ¿Por qué el uso simple de `depends_on` sin `condition: service_healthy` suele causar fallos de conexión en servicios como PostgreSQL o Airflow?
2. ¿Qué significan las propiedades `interval`, `timeout`, `retries` y `start_period` en la definición de un *Healthcheck*?
3. ¿Cómo ayudan los `profiles` en Docker Compose a optimizar el consumo de RAM en la máquina de desarrollo de un Data Engineer?
4. ¿Por qué es fundamental que la variable de entorno dentro del comando del healthcheck de Postgres utilice doble signo pesos (`$${POSTGRES_USER}`) en un archivo Compose?