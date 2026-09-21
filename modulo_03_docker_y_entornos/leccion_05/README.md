# 🐳 Lección 05: Cierre del Módulo 03 — Proyecto Integrador con Healthchecks, Variables de Entorno (`.env`) y Resiliencia

¡Llegamos al hito final del **Módulo 04: Docker y Entornos Contenedorizados**!

A lo largo de este módulo hemos cubierto la base de contenedorización para producción:

* **Lección 01**: Fundamentos de Docker, arquitectura, imágenes vs. contenedores y comandos de gestión (`run`, `exec`, `logs`, `ps`).
* **Lección 02**: Creación de imágenes optimizadas con `Dockerfile`, capas, seguridad sin usuario root y *Multi-stage Builds*.
* **Lección 03**: Persistencia de datos con `Named Volumes` y `Bind Mounts`, y aislamiento en redes `bridge` con resolución DNS.
* **Lección 04**: Orquestación declarativa de stacks multicontenedor con `docker-compose.yml` (PostgreSQL + Adminer + App ETL).

En esta lección cerramos el módulo integrando tres conceptos críticos de producción: **monitoreo de estado de salud (** **Healthchecks** **)**, **gestión segura de credenciales con archivos** **.env** y **límites de recursos con políticas de reinicio automático**.

---

## 1\. Manejo Seguro de Credenciales con Archivos `.env`

Nunca debemos escribir claves, contraseñas o URLs de bases de datos hardcodeadas dentro del archivo `docker-compose.yml`. Si ese YAML se sube a un repositorio de GitHub, las credenciales quedan expuestas.

La buena práctica consiste en separar la configuración de la infraestructura mediante un archivo **.env**:

```
# .env (NO SE SUBE A GIT - Incluir en .gitignore)
POSTGRES_DB=dw_analitico
POSTGRES_USER=app_de_user
POSTGRES_PASSWORD=SuperSecretPassword2026!
POSTGRES_PORT=5432
ADMINER_PORT=8080

```

Docker Compose lee automáticamente el archivo `.env` ubicado en el mismo directorio y sustituye las variables sintácticamente mediante `${VARIABLE}`:

```
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}

```

---

## 2\. Control de Arranque Resiliente con `healthcheck`

Un problema clásico en sistemas distribuidos ocurre cuando la aplicación ETL intenta conectarse a PostgreSQL apenas se inicia el contenedor de la base de datos. Que el contenedor esté en estado `running` **no significa que la base de datos esté lista para aceptar conexiones** (PostgreSQL tarda unos segundos en inicializar la memoria y ejecutar scripts).

Para evitar que la App falle al arrancar, implementamos un **healthcheck**:

```
services:
  postgres_db:
    image: postgres:16-alpine
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 5s     # Evalúa cada 5 segundos
      timeout: 5s      # Espera máxima por respuesta
      retries: 5       # Reintentos antes de marcar 'unhealthy'
      start_period: 10s # Tiempo de gracia inicial

  etl_app:
    build: ./app
    depends_on:
      postgres_db:
        condition: service_healthy # ⚡ Espera a que el healthcheck SEA EXITOSO

```

---

## 3\. Límites de Recursos y Políticas de Reinicio

Para evitar que un script de Python con un consumo imprevisto de memoria RAM colapse el servidor anfitrión (*OOM Killer*), asignamos **límites de CPU y RAM**:

```
services:
  etl_app:
    restart: unless-stopped # Se reinicia automáticamente si colapsa, salvo que lo detengas explícitamente
    deploy:
      resources:
        limits:
          cpus: '1.5'      # Máximo 1.5 núcleos de CPU
          memory: 512M     # Máximo 512 MB de RAM
        reservations:
          memory: 128M     # Memoria garantizada al arrancar

```

---

## 🟢 4\. Archivo `docker-compose.yml` Completo de Producción

A continuación integramos todos los conceptos en el stack definitivo del módulo:

```
version: '3.8'

services:
  # 1. Base de Datos Relacional con Healthcheck
  postgres_db:
    image: postgres:16-alpine
    container_name: db_production_pg
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    ports:
      - "${POSTGRES_PORT}:5432"
    volumes:
      - pg_prod_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 5s
      timeout: 5s
      retries: 5
      start_period: 5s
    networks:
      - red_produccion_data

  # 2. UI de Administración (Adminer)
  adminer_ui:
    image: adminer:latest
    container_name: adminer_prod_ui
    restart: unless-stopped
    ports:
      - "${ADMINER_PORT}:8080"
    networks:
      - red_produccion_data
    depends_on:
      postgres_db:
        condition: service_healthy

  # 3. App ETL en Python / Polars
  etl_runner:
    build:
      context: ./app_etl
      dockerfile: Dockerfile
    container_name: runner_etl_polars
    restart: "no" # Correrá una vez y finalizará
    environment:
      DATABASE_URL: postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres_db:5432/${POSTGRES_DB}
    networks:
      - red_produccion_data
    depends_on:
      postgres_db:
        condition: service_healthy
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 256M

volumes:
  pg_prod_data:
    driver: local

networks:
  red_produccion_data:
    driver: bridge

```

---

## 🏋️‍♂️ Práctica del Proyecto Integrador (Lección 05)

1. Ubicate en la carpeta `practica/modulo_04/` de tu repositorio local.
2. Creá la subcarpeta `proyecto_integrador_docker/`:

```
practica/modulo_04/proyecto_integrador_docker/
├── .env
├── .env.example
├── .gitignore
├── docker-compose.yml
└── app_etl/
    ├── .dockerignore
    ├── Dockerfile
    ├── requirements.txt
    └── src/
        └── main.py

```

1. Configurá los archivos:
  * **.env**: Definí `POSTGRES_DB=dw_integrador`, `POSTGRES_USER=de_admin`, `POSTGRES_PASSWORD=ClaveSegura123!`, `POSTGRES_PORT=5432` y `ADMINER_PORT=8080`.
  * **.env.example**: Archivo de plantilla para subir a Git sin valores reales (ej: `POSTGRES_PASSWORD=tu_clave_aqui`).
  * **.gitignore**: Agregá `.env`.
  * **app\_etl/src/main.py**: Escribí un script en Python usando `Polars` y `SQLAlchemy` que inserte una tabla de prueba de 10 filas en PostgreSQL al arrancar.
2. Levanta el stack desde la terminal con:

```
docker compose up -d --build

```

1. Comprobá el estado del healthcheck y los logs:

```
docker compose ps
docker compose logs -f etl_runner

```

1. Abrí `http://localhost:8080`, ingresá a Adminer y confirmá que la tabla generada por la App ETL existe y tiene los datos insertados.
2. Una vez verificado, destruí el stack liberando recursos:

```
docker compose down -v
```