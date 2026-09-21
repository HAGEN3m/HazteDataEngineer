# 🐳 Lección 04: Orquestación Multicontenedor con `docker-compose.yml` (Levantando el Stack Local)

En la **Lección 03** aprendimos a gestionar la persistencia de datos con **Volúmenes** y a conectar contenedores manualmente dentro de una **Red de Docker** (`docker network create`).

Sin embargo, ejecutar comandos individuales de `docker run` con múltiples parámetros (`-v`, `-p`, `-e`, `--network`) para cada uno de los componentes de nuestra arquitectura analítica (PostgreSQL, Adminer, scripts ETL, orquestadores) se vuelve **impracticable y propenso a errores en equipos de desarrollo**.

En esta lección aprenderemos a declarar y orquestar todo nuestro stack de datos en un único archivo de configuración **docker-compose.yml**, permitiéndonos levantar entornos completos con un solo comando.

---

## 1\. ¿Qué es Docker Compose?

**Docker Compose** es una herramienta oficial para definir y ejecutar aplicaciones multicontenedor mediante un archivo de configuración declarativo en formato **YAML**.

En lugar de recordar largas líneas de comandos en bash, definimos los servicios, redes, volúmenes y variables de entorno en el archivo `docker-compose.yml` y los gestionamos como **una sola unidad lógica**.

---

## 2\. Anatomía de un archivo `docker-compose.yml`

Un archivo `docker-compose.yml` estándar de Data Engineering se divide en 3 secciones principales:

```
services:      # 1. Lista de contenedores/servicios a levantar
  postgres_db:
    # ...
  adminer_ui:
    # ...
  etl_app:
    # ...

volumes:       # 2. Volúmenes administrados declarados
  postgres_data:

networks:      # 3. Redes privadas declaradas
  red_analitica:

```

### Directivas Clave dentro de cada servicio:

* **build**: Especifica la ruta del `Dockerfile` para construir la imagen localmente.
* **image**: Descarga una imagen preexistente desde Docker Hub.
* **container\_name**: Asigna un nombre fijo al contenedor.
* **environment** **/** **env\_file**: Inyecta variables de entorno o lee un archivo `.env`.
* **ports**: Mapea puertos (`host:contenedor`).
* **volumes**: Monta volúmenes o carpetas locales (`bind mounts`).
* **networks**: Conecta el servicio a redes específicas.
* **depends\_on**: Define el **orden de arranque** (ej. la App ETL no arranca hasta que la base de datos esté lista).

---

## 3\. Ejemplo Profesional: Stack Completo de Ingesta Analítica

A continuación armamos un stack local con 3 servicios interactuando sobre la misma red:

1. **db**: PostgreSQL 16 con volumen persistente.
2. **adminer**: Interfaz web liviana para inspeccionar la base de datos desde el navegador en `http://localhost:8080`.
3. **etl\_runner**: Nuestra aplicación Python/Polars que se compila localmente y se conecta a la base de datos.

```
version: '3.8'

services:
  # Servicio 1: Base de datos PostgreSQL
  postgres_db:
    image: postgres:16-alpine
    container_name: db_postgres_compose
    restart: always
    environment:
      POSTGRES_DB: data_warehouse
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: secret_password
    ports:
      - "5432:5432"
    volumes:
      - pgdata_volume:/var/lib/postgresql/data
    networks:
      - red_stack_datos

  # Servicio 2: Interfaz Web para consultar SQL (Adminer)
  adminer_ui:
    image: adminer:latest
    container_name: adminer_compose
    restart: always
    ports:
      - "8080:8080"
    networks:
      - red_stack_datos
    depends_on:
      - postgres_db

  # Servicio 3: Aplicación ETL en Python / Polars
  etl_runner:
    build:
      context: ./app_etl
      dockerfile: Dockerfile
    container_name: etl_polars_runner
    environment:
      DATABASE_URL: postgresql://admin:secret_password@postgres_db:5432/data_warehouse
    volumes:
      - ./app_etl/src:/app/src  # Bind mount para Live Reload en desarrollo
    networks:
      - red_stack_datos
    depends_on:
      - postgres_db

# Volúmenes Persistentes
volumes:
  pgdata_volume:
    driver: local

# Redes Aisladas
networks:
  red_stack_datos:
    driver: bridge

```

---

## 4\. Comandos del Ciclo de Vida de Docker Compose (V2)

En las versiones modernas de Docker, Compose está integrado directamente en la CLI (`docker compose` sin guion):

```
# 1. Levantar todo el stack en segundo plano (-d) y construir imágenes si es necesario (--build)
docker compose up -d --build

# 2. Ver el estado de todos los servicios del stack
docker compose ps

# 3. Ver logs en tiempo real de todos los servicios (o de uno específico)
docker compose logs -f postgres_db

# 4. Ejecutar comandos dentro de un servicio del stack
docker compose exec postgres_db psql -U admin -d data_warehouse

# 5. Detener y destruir el stack completo (manteniendo los volúmenes)
docker compose down

# 6. Destruir el stack Y ELIMINAR LOS VOLÚMENES PERSISTENTES
docker compose down -v

```

---

## 🏋️‍♂️ Práctica de la Lección 04

1. Ubicate en la carpeta `practica/modulo_04/` de tu repositorio local.
2. Creá la subcarpeta `stack_docker_compose/`:

```
practica/modulo_04/stack_docker_compose/
├── docker-compose.yml
└── app_etl/
    ├── Dockerfile
    ├── requirements.txt
    └── src/
        └── main.py

```

1. Configurá los archivos:
  * **app\_etl/requirements.txt**: Agregá `polars==1.8.0` y `psycopg2-binary`.
  * **app\_etl/src/main.py**: Escribí un script breve que espere la conexión a `postgres_db` e imprima un mensaje de éxito.
  * **docker-compose.yml**: Utilizá el archivo YAML definido en esta lección.
2. Ejecutá desde la terminal en la carpeta `stack_docker_compose/`:

```
docker compose up -d --build

```

1. Abrí tu navegador en `http://localhost:8080`, seleccioná el motor **PostgreSQL**, servidor **postgres\_db**, usuario **admin**, clave **secret\_password** y base de datos **data\_warehouse** para verificar el acceso desde Adminer.
2. Cuando termines la verificación, apagá el stack con:

```
docker compose down

```