# 🐳 Lección 03: Persistencia y Redes en Docker — Volúmenes (`Named Volumes` vs. `Bind Mounts`) y Redes Aisladas (`Bridge`)

En la **Lección 02** aprendimos a empaquetar nuestro código de Python y Polars en imágenes de Docker optimizadas con *Multi-stage Builds*.

Sin embargo, por defecto, los contenedores son **efímeros y de estado no persistente (** **Stateless** **)**. Si un contenedor de PostgreSQL se detiene y se elimina (`docker rm`), **todos los datos guardados en la base de datos se pierden para siempre**.

En esta lección aprenderemos a resolver la persistencia de datos mediante **Volúmenes** y a conectar múltiples contenedores entre sí mediante **Redes Aisladas** con resolución de nombres por DNS interno.

---

## 1\. El Problema de la Capa Escriturable y la Efimeridad

Cada contenedor Docker posee una **capa de escritura temporal (** **Writable Layer** **)** donde guarda las modificaciones de archivos mientras está activo.

```
┌─────────────────────────────────────────┐
│ Capa de Escritura Temporal (Efímera)   │  &lt;-- 🚨 Se DESTRUYE al borrar el contenedor
├─────────────────────────────────────────┤
│ Capa de Aplicación (Read-Only)          │
├─────────────────────────────────────────┤
│ Capa Base de Sistema Operativo (R-O)    │
└─────────────────────────────────────────┘

```

Si el contenedor colapsa o es reemplazado por una versión más nueva, esa capa de escritura se elimina. Para bases de datos (PostgreSQL, ClickHouse) o almacenamiento de archivos analíticos (Data Lakes), debemos desacoplar el almacenamiento del ciclo de vida del contenedor.

---

## 2\. Tipos de Almacenamiento Persistente: `Bind Mounts` vs. `Named Volumes`

Docker ofrece dos mecanismos principales para guardar datos fuera del contenedor:

```
       MÁQUINA ANFITRIONA (HOST)                      CONTENEDOR
┌────────────────────────────────────────┐     ┌───────────────────────┐
│ /var/lib/docker/volumes/mi_db_data/   │────&gt;│ /var/lib/postgresql/  │  &lt;-- Named Volume
│                                        │     │                       │
│ /Users/de/proyecto/src/                │────&gt;│ /app/src/             │  &lt;-- Bind Mount
└────────────────────────────────────────┘     └───────────────────────┘

```

### A. `Bind Mounts` (Mapeo de Directorios Locales)

Montan un directorio o archivo específico de tu computadora local directamente dentro del contenedor.

* **Uso ideal**: **Entornos de Desarrollo Local (** **Live Reload** **)**. Si modificás un script Python en tu IDE (VSCode/PyCharm), el cambio se refleja al instante dentro del contenedor sin necesidad de reconstruir la imagen (`docker build`).
* **Sintaxis**:

```
docker run -d \
  -v $(pwd)/src:/app/src \
  --name app_dev mi_etl:v1

```

### B. `Named Volumes` (Volúmenes Gestionados por Docker)

Docker crea y administra una carpeta aislada en el sistema de archivos del servidor (`/var/lib/docker/volumes/`).

* **Uso ideal**: **Bases de Datos y Almacenamiento de Producción**. Alta velocidad de I/O, independientes de la estructura de carpetas del host y administrados mediante comandos de Docker CLI.
* **Sintaxis**:

```
# Crear un volumen administrado
docker volume create postgres_data_vol

# Montar el volumen en el contenedor de PostgreSQL
docker run -d \
  --name db_prod \
  -v postgres_data_vol:/var/lib/postgresql/data \
  -e POSTGRES_PASSWORD=secret \
  postgres:16-alpine

```

---

## 3\. Redes en Docker (`Docker Networks`)

Por defecto, los contenedores se ejecutan en aislamiento. Para que un script de Python en un contenedor pueda conectarse a una base de datos PostgreSQL en otro contenedor, ambos deben estar conectados a la misma **Red de Docker**.

### Red Personalizada de Tipo `Bridge`

Al crear una red personalizada tipo `bridge`, Docker activa un **servidor DNS interno**. Los contenedores pueden comunicarse entre sí utilizando directamente **sus nombres de contenedor como Hostname**, sin importar qué dirección IP dinámica tengan asignada.

```
# 1. Crear una red privada aislada para el pipeline de datos
docker network create red_datos_etl

# 2. Levantar la base de datos en esa red
docker run -d \
  --name postgres_db \
  --network red_datos_etl \
  -e POSTGRES_PASSWORD=secret \
  postgres:16-alpine

# 3. Desde otro contenedor en la MISMA red, nos conectamos usando 'postgres_db' como host:
# DB_HOST=postgres_db

```

---

## 🛠️ Comandos Útiles de Gestión de Volúmenes y Redes

```
# Listar y limpiar volúmenes
docker volume ls
docker volume prune   # Elimina volúmenes huérfanos sin contenedor asociado

# Listar y administrar redes
docker network ls
docker network inspect red_datos_etl

```

---

## 🏋️‍♂️ Práctica de la Lección 03

1. Ubicate en la carpeta `practica/modulo_04/` de tu repositorio local.
2. Creá el script bash `ej_03_volumes_and_networks.sh`.
3. Escribí las instrucciones bash para demostrar la persistencia ante la destrucción del contenedor:
  * **Paso 1**: Crear la red `red_practica_etl`.
  * **Paso 2**: Crear el volumen administrado `vol_postgres_test`.
  * **Paso 3**: Iniciar un contenedor `db_v1` de PostgreSQL usando el volumen y la red creada.
  * **Paso 4**: Crear una tabla e insertar un registro de prueba usando `docker exec`.
  * **Paso 5**: Detener y **destruir** el contenedor `db_v1` (`docker rm -f db_v1`).
  * **Paso 6**: Levantar un **nuevo contenedor totalmente diferente** (`db_v2`) montando el **mismo volumen** `vol_postgres_test`.
  * **Paso 7**: Consultar la tabla con `docker exec` desde `db_v2` para verificar que **los datos sobrevivieron intactos a la destrucción del contenedor**.
4. Otorgale permisos de ejecución (`chmod +x practica/modulo_04/ej_03_volumes_and_networks.sh`) y ejecutalo.