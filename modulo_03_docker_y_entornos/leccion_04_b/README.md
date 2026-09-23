# 🐳 Lección 04.B (Módulo 03): Hardening de Seguridad, Logging Drivers y Diagnóstico en Producción

&gt; **Propósito**: Dominar la seguridad en contenedores, límites estrictos de recursos (CPU/RAM, OOM Killer), estrategias de rotación de logs (*Logging Drivers*) y comandos de diagnóstico a bajo nivel (`docker stats`, `docker inspect`, exit code 137) para operar infraestructuras de datos en producción de forma segura e ininterrumpida.

---

## 📌 1\. Hardening de Seguridad: Principio de Menor Privilegio

Por defecto, los procesos dentro de un contenedor se ejecutan con permisos de usuario `root` (UID 0) dentro del namespace del contenedor. Si un atacante o un script malicioso logra escapar del aislamiento (*Container Breakout*), obtendrá control total de la máquina host.

```
❌ INSEGURO (Por defecto):
[ Process: python pipeline.py (UID 0 - root) ] ─── Breakout ───&gt; [ Host OS: Control Total ]

✅ HARDENED (Producción):
[ Process: python pipeline.py (UID 10001 - appuser) ] ─── Breakout ───&gt; [ Host OS: Acceso Denegado ]

```

### Reglas de Oro de Seguridad en Docker:

1. **Nunca ejecutes como** **root**: Define siempre un usuario sin privilegios en tu `Dockerfile`.
2. **Sistema de Archivos de Solo Lectura (** **read\_only** **)**: Evita que un script modifique el binario o inyecte archivos maliciosos en la imagen. Usa `tmpfs` para carpetas temporales (`/tmp`).
3. **Desactivar Escalado de Privilegios**: Desactiva `allow_privilege_escalation: false` para evitar exploit de `sudo` o `setuid`.
4. **Drop Capabilities (** **cap\_drop: [ALL]** **)**: El Kernel de Linux divide los privilegios de root en "capabilities". En contenedores de datos, debemos remover todas las capabilities innecesarias (ej. modificar red, montar discos).

```
# Ejemplo en Dockerfile de Producción
FROM python:3.12-slim

# Crear grupo y usuario no-root con ID fijo
RUN groupadd -g 10001 appgroup &amp;&amp; \
    useradd -u 10001 -g appgroup -s /bin/bash -m appuser

WORKDIR /app
COPY --chown=appuser:appgroup . /app

# Cambiar al usuario no privilegiado
USER appuser

CMD ["python", "main.py"]

```

---

## 🔬 2\. Límites de Recursos y el Linux OOM Killer (Exit Code 137)

Cuando un pipeline de Python o un job de Spark dentro de un contenedor intenta consumir más memoria RAM de la disponible en el servidor host, el Kernel de Linux activa el **Out Of Memory (OOM) Killer**.

```
[ Contenedor consumiendo RAM ] ─── (Supera cgroup limit) ───&gt; [ Linux OOM Killer ]
                                                                       │
                                                                       ▼
                                                       [ Envía SIGKILL (Signal 9) ]
                                                                       │
                                                                       ▼
                                                       [ Exit Code 137 (128 + 9) ]

```

### Cómo diagnosticar un fallo por OOM Killer:

Si tu contenedor se detiene de forma repentina con el código de salida **137**, significa que el Kernel lo mató por exceso de memoria (`128 + 9 (SIGKILL) = 137`).

### Configuración de Límites en Docker Compose:

```
services:
  data_pipeline:
    image: mi_pipeline:latest
    deploy:
      resources:
        limits:
          cpus: '2.0'       # Máximo 2 núcleos virtuales de CPU
          memory: 2048M     # Límite estricto de RAM (si lo supera -&gt; OOM Killer)
        reservations:
          cpus: '0.5'       # Garantía mínima de CPU
          memory: 512M      # Garantía mínima de RAM

```

---

## 🛠️ 3\. Logging Drivers y Rotación de Logs

Por defecto, Docker utiliza el driver de logs `json-file`, el cual escribe cada salida estándar (`stdout` y `stderr`) del contenedor en un archivo `.log` dentro del host (`/var/lib/docker/containers/