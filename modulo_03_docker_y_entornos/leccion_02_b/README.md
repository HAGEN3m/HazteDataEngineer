# 🐳 Lección 02.B (Módulo 03): Storage &amp; Networking en Docker: Redes, DNS y Volúmenes

&gt; **Propósito**: Dominar la arquitectura de red e interfaces de almacenamiento en Docker, comprendiendo el funcionamiento de los drivers de red (`bridge`, `host`), la resolución de nombres vía DNS interno, y la diferencia crítica de rendimiento e I/O entre **Docker Volumes**, **Bind Mounts** y **tmpfs**.

---

## 📌 1\. Drivers de Red en Docker: Bridge vs. Host vs. Overlay

Por defecto, Docker aísla los contenedores del stack de red del sistema operativo host mediante interfaces virtuales y reglas de **iptables** / **nftables**.

```
[ Host OS Physical Network: eth0 (192.168.1.50) ]
                      │
                      ▼
[ Docker Bridge Network: docker0 (172.17.0.1/16) ]
          ┌───────────┴───────────┐
          ▼                       ▼
 [ Contenedor A (172.17.0.2) ] [ Contenedor B (172.17.0.3) ]

```

### Principales Drivers de Red:

1. **bridge** **(Por defecto)**:
  * Crea un puente virtual (`docker0` o red personalizada). Los contenedores obtienen su propia dirección IP privada dentro de la subred del bridge.
  * Aísla el tráfico de la máquina host. Los puertos deben exponerse explícitamente (`-p host_port:container_port`).
2. **host**:
  * Remueve el aislamiento de red entre el contenedor y el host. El contenedor comparte directamente la interfaz de red de la máquina (`eth0`).
  * **Ventaja**: Máximo rendimiento de red (sin overhead de NAT/iptables).
  * **Desventaja**: No hay aislamiento de puertos (colisión de puertos si dos procesos usan el mismo).
3. **none**:
  * Desconecta por completo la interfaz de red del contenedor (aislamiento total para procesos sensibles).
4. **overlay**:
  * Usado en entornos multinodo (Docker Swarm / Kubernetes) para conectar contenedores ejecutándose en distintas máquinas físicas mediante túneles VXLAN.

---

## 🔬 2\. DNS Interno de Docker y Name Resolution

En la red `bridge` por defecto de Docker, los contenedores **solo se pueden comunicar entre sí mediante IP**. Sin embargo, las IPs de los contenedores son efímeras y cambian cada vez que se reinician.

### Redes User-Defined (Personalizadas)

Cuando creas una red de usuario (`docker network create mi_red`), Docker activa automáticamente un **servidor DNS interno** (ubicado en `127.0.0.11` dentro del contenedor).

```
   [ Contenedor "app" ] ─── (DNS Query: "db") ───&gt; [ Embedded DNS (127.0.0.11) ]
                                                            │
                                                            ▼ (Resuelve a 172.20.0.5)
   [ Contenedor "db" ]  &lt;─── (TCP Connect 5432) ────────────┘

```

&gt; 💡 **REGLA DE ORO DE REDES**: Nunca hardcodees direcciones IP dentro de tus scripts de Python o pipelines. Crea una red personalizada y usa el **nombre del contenedor o servicio** como host de conexión (ej. `host="postgres_db"`).

---

## 🛠️ 3\. Arquitectura de Almacenamiento: Volumes vs. Bind Mounts vs. tmpfs

Un contenedor por defecto escribe sus archivos en su propia capa de lectura/escritura (*Writable Layer*) usando `Overlay2`. Si el contenedor se destruye, **todos los datos no guardados en un montaje externo se pierden permanentemente**.

```
    TIPO                   DÓNDE RESIDE EN EL HOST               CASO DE USO IDEAL
┌──────────────┐     ┌──────────────────────────────────┐     ┌──────────────────────────────┐
│  VOLUMES     │ ──&gt; │ /var/lib/docker/volumes/          │ ──&gt; │ BBDD (PostgreSQL, MinIO)    │
├──────────────┤     ├──────────────────────────────────┤     ├──────────────────────────────┤
│ BIND MOUNTS  │ ──&gt; │ /home/usuario/mi_proyecto/       │ ──&gt; │ Código fuente en desarrollo  │
├──────────────┤     ├──────────────────────────────────┤     ├──────────────────────────────┤
│ TMPFS        │ ──&gt; │ Memoria RAM del Host             │ ──&gt; │ Secretos, tokens efímeros    │
└──────────────┘     └──────────────────────────────────┘     └──────────────────────────────┘

```

### A. Docker Volumes (Gestionados por Docker)

* Los datos se almacenan en un área del sistema de archivos gestionada exclusivamente por Docker (`/var/lib/docker/volumes/`).
* **Ventajas**: Totalmente aislados del sistema operativo host, alto rendimiento I/O, fáciles de respaldar y migrar.
* **Uso**: Persistencia de datos de producción (PostgreSQL, MySQL, MinIO, Redis).

### B. Bind Mounts (Mapeo Directo de Carpetas)

* Mapean una carpeta o archivo específico de la computadora host directamente dentro del contenedor (`-v /ruta/local:/ruta/contenedor`).
* **Ventajas**: Los cambios realizados en el host se reflejan de inmediato dentro del contenedor.
* **Uso**: Desarrollo local de código (permite *live-reloading* de scripts Python sin re-construir la imagen).

### C. tmpfs Mounts (En Memoria RAM)

* Los datos se escriben directamente en la memoria RAM del host. Nunca tocan el disco rígido.
* **Uso**: Almacenar información highly sensible (claves privadas, credenciales) o buffers de alto rendimiento que no requieren persistencia.

---

## ⚡ 4\. Problemas de Permisos, UID/GID y Performance I/O

### A. Colisión de Permisos de Archivo (`permission denied`)

Por defecto, los procesos dentro del contenedor corren como `root` (UID 0). Si usas un **Bind Mount**, los archivos creados por el contenedor pertenecerán a `root`, impidiendo que tu usuario normal en Linux/Mac los edite o borre.

**Solución en Producción**: Pasar el UID/GID de tu usuario local al ejecutar o construir el contenedor:

```
docker run -u $(id -u):$(id -g) -v $(pwd):/app mi_imagen

```

### B. Performance I/O en Mac y Windows (Docker Desktop)

En macOS y Windows, Docker corre dentro de una máquina virtual ligera de Linux. Mapear carpetas con miles de archivos pequeños mediante **Bind Mounts** (ej. `node_modules` o un `.venv` de Python) puede ser hasta **10 veces más lento** debido al overhead de sincronización entre sistemas de archivos (macOS APFS &lt;-&gt; Linux ext4).

**Buena Práctica**: Mantén los entornos virtuales (`venv`) y dependencias DENTRO de un Docker Volume o de la imagen, mapeando por Bind Mount únicamente tu código fuente.

---

## 🏋️‍♂️ Ejercicio Práctico Hands-On: Red Privada y Persistencia con PostgreSQL

Crea el script `setup_red_y_volumen.sh` para levantar una base de datos PostgreSQL aislada en su propia red con un volumen de persistencia:

```
#!/usr/bin/env bash
set -euo pipefail

# 1. Crear una red personalizada
echo "Creating custom docker network 'red_data_engineering'..."
docker network create red_data_engineering || true

# 2. Crear un volumen administrado para PostgreSQL
echo "Creating volume 'postgres_data_vol'..."
docker volume create postgres_data_vol || true

# 3. Lanzar contenedor de PostgreSQL conectado a la red y al volumen
echo "Launching PostgreSQL container..."
docker run -d \
  --name postgres_db \
  --network red_data_engineering \
  -v postgres_data_vol:/var/lib/postgresql/data \
  -e POSTGRES_USER=de_user \
  -e POSTGRES_PASSWORD=de_password \
  -e POSTGRES_DB=analytics \
  postgres:16-alpine

# 4. Lanzar un contenedor cliente efímero en la MISMA red usando DNS interno
echo "Testing internal DNS resolution from client container..."
docker run --rm \
  --network red_data_engineering \
  postgres:16-alpine \
  pg_isready -h postgres_db -U de_user

echo "✅ Environment successfully setup with internal DNS and persistent volume!"

```

---

## 🧠 Checkpoint de Autoevaluación

1. ¿Por qué el servidor DNS interno de Docker solo funciona en redes personalizadas (*user-defined networks*) y no en la red `bridge` por defecto?
2. ¿Cuál es la diferencia fundamental entre un **Docker Volume** y un **Bind Mount** y cuándo deberías usar cada uno?
3. ¿Qué problema de seguridad y permisos ocurre cuando un contenedor corriendo como `root` escribe archivos dentro de un *Bind Mount*?
4. ¿Por qué los *Bind Mounts* masivos con miles de archivos pequeños sufren degradación de I/O en Docker Desktop para macOS o Windows?