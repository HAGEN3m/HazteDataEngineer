# 🐳 Lección 01: Fundamentos de Contenedorización, Arquitectura de Docker y Comandos Esenciales

En la Ingeniería de Datos moderna, escribir código que funciona únicamente en tu computadora personal (*"en mi máquina funciona"*) es inaceptable. Los pipelines ETL/ELT, las bases de datos (PostgreSQL, ClickHouse), los orquestadores (Airflow) y las transformaciones (dbt, Polars) deben ejecutarse en **entornos idénticos, aislados y reproducibles**, ya sea en tu laptop, en un servidor de CI/CD o en la nube (AWS, GCP, Azure).

Aquí es donde entra **Docker** y el paradigma de la contenedorización.

---

## 1\. Contenedores vs. Máquinas Virtuales (VMs)

Para entender la eficiencia de Docker, debemos compararlo con las Máquinas Virtuales tradicionales (VirtualBox, VMware):

```
┌───────────────────────────────┐     ┌───────────────────────────────┐
│       MÁQUINA VIRTUAL         │     │     CONTENEDOR (DOCKER)       │
├───────────────────────────────┤     ├───────────────────────────────┤
│ App A   │ App B   │ App C     │     │ App A   │ App B   │ App C     │
│ Bins/Lib│ Bins/Lib│ Bins/Lib  │     │ Bins/Lib│ Bins/Lib│ Bins/Lib  │
│ OS Huésped (Linux 2GB RAM ea.)│     ├───────────────────────────────┤
├───────────────────────────────┤     │        Docker Engine          │
│          Hypervisor           │     ├───────────────────────────────┤
├───────────────────────────────┤     │     OS Anfitrión (Host)       │
│     Hardware Servidor/PC      │     │     Hardware Servidor/PC      │
└───────────────────────────────┘     └───────────────────────────────┘

```

* **Máquinas Virtuales**: Cada VM emula hardware completo y ejecuta un **Sistema Operativo Huésped completo** (ocupando Gigabytes de RAM y disco, tardando minutos en arrancar).
* **Contenedores Docker**: Comparten el **Kernel del Sistema Operativo Anfitrión (** **Host** **)**. Cada contenedor es un proceso aislado en espacio de usuario que arranca en **milisegundos** y consume solo la memoria que su aplicación requiere.

---

## 2\. Conceptos Fundamentales: Imagen vs. Contenedor

Para usar la analogía de Programación Orientada a Objetos:

* **Imagen (** **Docker Image** **)**: Es la **Clase / Plantilla inmutable (read-only)**. Contiene el sistema de archivos, librerías, binarios y código necesarios para ejecutar una aplicación.
* **Contenedor (** **Docker Container** **)**: Es la **Instancia ejecutable en memoria** creada a partir de una imagen. Podés arrancar, pausar, reiniciar o destruir decenas de contenedores usando la misma imagen base.
* **Docker Hub / Registry**: Es el repositorio público/privado (similar a GitHub, pero para imágenes) desde donde descargamos imágenes oficiales (`postgres`, `python`, `clickhouse`, `adminer`).

---

## 3\. Comandos Esenciales de Gestión en la Terminal

A continuación se resumen los comandos que utilizarás a diario como Data Engineer:

### A. Descargar y Ejecutar Contenedores (`docker run`)

```
# Descarga la imagen de PostgreSQL (si no la tiene) y la arranca en segundo plano (-d)
docker run -d \
  --name mi_postgres_local \
  -e POSTGRES_PASSWORD=secret \
  -p 5432:5432 \
  postgres:16-alpine

```

* **\-d** **(** **Detached** **)**: Ejecuta el contenedor en segundo plano liberando la terminal.
* **\--name**: Asigna un nombre legible al contenedor.
* **\-e** **(** **Environment** **)**: Inyecta variables de entorno (como credenciales).
* **\-p host:container**: Mapea el puerto de tu computadora (`5432`) al puerto interno del contenedor (`5432`).

### B. Inspección y Estado (`docker ps` &amp; `docker logs`)

```
# Listar contenedores activos en ejecución
docker ps

# Listar TODOS los contenedores (incluyendo los detenidos)
docker ps -a

# Inspeccionar los logs/salida estándar (stdout/stderr) de un contenedor
docker logs -f mi_postgres_local

```

### C. Ejecutar Comandos dentro de un Contenedor (`docker exec`)

```
# Entrar de forma interactiva (-it) a la consola psql dentro del contenedor corriendo
docker exec -it mi_postgres_local psql -U postgres

```

### D. Limpieza y Detención (`docker stop` &amp; `docker rm`)

```
# Detener el contenedor
docker stop mi_postgres_local

# Eliminar el contenedor (libera el proceso)
docker rm mi_postgres_local

# Eliminar imágenes sin usar para liberar espacio en disco
docker image prune -a

```

---

## 🏋️‍♂️ Práctica de la Lección 01

1. Creá la carpeta `practica/modulo_04/` en tu repositorio local.
2. Creá el script bash `ej_01_docker_basics.sh`.
3. Escribí los comandos necesarios para realizar el siguiente flujo:
  * Levantar un contenedor en segundo plano con la imagen oficial de **Redis** (`redis:7-alpine`) llamado `cache_de_prueba` expuesto en el puerto `6379`.
  * Verificar que el contenedor esté corriendo listando los procesos activos.
  * Ejecutar la herramienta `redis-cli ping` dentro del contenedor mediante `docker exec` para confirmar respuesta (`PONG`).
  * Ver los logs del contenedor.
  * Detener y eliminar el contenedor.
4. Otorgale permisos de ejecución (`chmod +x practica/modulo_04/ej_01_docker_basics.sh`) y ejecutalo en tu terminal.