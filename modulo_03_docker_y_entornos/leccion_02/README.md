# 🐳 Lección 02: Creación de Imágenes Defensivas con `Dockerfile` y *Multi-stage Builds*

En la **Lección 01** aprendimos a descargar y ejecutar contenedores preexistentes desde Docker Hub (`postgres`, `redis`). Sin embargo, para desplegar nuestros propios pipelines de datos de Python, Polars o scripts de ingesta en producción, necesitamos empaquetar nuestro código y sus dependencias en **nuestras propias imágenes personalizadas**.

En esta lección aprenderemos a escribir un **Dockerfile** defensivo, optimizar el almacenamiento en capas y aplicar el patrón de la industria **Multi-stage Builds** para reducir el peso de las imágenes de 1 GB a menos de 150 MB.

---

## 1\. ¿Qué es un `Dockerfile` y cómo funcionan las Capas (*Layers*)?

Un **Dockerfile** es un archivo de texto plano que contiene la "receta" paso a paso para construir una imagen de Docker.

Cada instrucción en un `Dockerfile` (`FROM`, `COPY`, `RUN`) crea una **capa inmutable de solo lectura (** **Read-Only Layer** **)** en el sistema de archivos:

```
┌───────────────────────────────────────────────────┐
│ CMD ["python", "main.py"]      &lt;-- Capa de inicio │
├───────────────────────────────────────────────────┤
│ COPY src/ /app/src             &lt;-- Capa de código │
├───────────────────────────────────────────────────┤
│ RUN pip install -r req.txt     &lt;-- Capa de deps   │
├───────────────────────────────────────────────────┤
│ FROM python:3.11-slim          &lt;-- Capa Base      │
└───────────────────────────────────────────────────┘

```

### ⚡ Estrategia de Caché por Capas

Docker reutiliza el resultado de ejecuciones previas (*Layer Caching*). Si no cambiaste el archivo `requirements.txt`, Docker saltará la instalación pesada de dependencias (`pip install`) reusando la capa en caché.

**Regla de Oro**: Colocá las instrucciones que cambian con menos frecuencia (instalación de paquetes) **antes** de las instrucciones que cambian constantemente (tu código fuente).

---

## 2\. Instrucciones Esenciales de un `Dockerfile`

| Instrucción | Propósito                                                  | Ejemplo / Buena Práctica                                                         |
| ----------- | ---------------------------------------------------------- | -------------------------------------------------------------------------------- |
| **FROM**    | Define la imagen base.                                     | Usar versiones delgadas y etiquetadas como `python:3.11-slim` (Evitar `latest`). |
| **WORKDIR** | Define el directorio de trabajo predeterminado.            | `WORKDIR /app`                                                                   |
| **COPY**    | Copia archivos locales de tu computadora a la imagen.      | `COPY requirements.txt .`                                                        |
| **RUN**     | Ejecuta comandos durante la **construcción de la imagen**. | `RUN pip install --no-cache-dir -r requirements.txt`                             |
| **ENV**     | Define variables de entorno permanentes.                   | `ENV PYTHONUNBUFFERED=1` (Fuerza salida inmediata a logs).                       |
| **USER**    | Define el usuario no-privilegiado que ejecutará la app.    | `USER appuser` *(Principio de menor privilegio)*.                                |
| **CMD**     | Comando por defecto al **arrancar el contenedor**.         | `CMD ["python", "src/main.py"]`                                                  |

---

## 3\. Prácticas Defensivas y Seguridad en la Imagen

1. **Evitar ejecutar como Usuario Root**: Por defecto, Docker ejecuta los procesos dentro del contenedor como `root`. Si el contenedor sufre una vulnerabilidad, el atacante ganaría acceso de administrador en el servidor anfitrión. Debemos crear un usuario sin privilegios.
2. **Uso del archivo** **.dockerignore**: Al igual que `.gitignore`, evita copiar carpetas innecesarias o sensibles (`.git`, `__pycache__`, `.env`, `.venv`) dentro de la imagen final:

```
# .dockerignore
.git
__pycache__/
*.pyc
.env
.venv/
tests/

```

---

## 4\. Optimización Extrema: *Multi-stage Builds* (Construcción en Etapas)

Cuando instalamos librerías complejas de Python (como Polars, Pandas o compiladores de C/Rust), el proceso de construcción requiere paquetes pesados como `gcc`, `g++` o `git` que ocupan cientos de Megabytes y no se necesitan para ejecutar la aplicación final.

Con **Multi-stage Builds**, utilizamos múltiples instrucciones `FROM` dentro del mismo `Dockerfile`:

* **Etapa 1 (** **builder** **)**: Instala compiladores, descarga dependencias y genera los paquetes compilados.
* **Etapa 2 (** **runner** **)**: Copia **únicamente los paquetes finales compilados** desde la etapa `builder` a una imagen limpia y liviana, descartando todas las herramientas de compilación pesadas.

### Ejemplo de `Dockerfile` Profesional con Multi-stage Build:

```
# ==========================================
# ETAPA 1: Builder (Compilaciones y Deps)
# ==========================================
FROM python:3.11-slim AS builder

WORKDIR /app

# Inhabilitar la creación de caché de pip para reducir espacio
ENV PIP_NO_CACHE_DIR=1 \
    PYTHONUNBUFFERED=1

# Instalar dependencias del sistema necesarias solo para compilar
RUN apt-get update &amp;&amp; apt-get install -y --no-install-recommends \
    build-essential \
    &amp;&amp; rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Crear un entorno virtual e instalar las librerías
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --upgrade pip &amp;&amp; pip install -r requirements.txt

# ==========================================
# ETAPA 2: Runner (Entorno Limpio Final)
# ==========================================
FROM python:3.11-slim AS runner

WORKDIR /app

# Crear usuario sin privilegios por seguridad
RUN groupadd -r appgroup &amp;&amp; useradd -r -g appgroup appuser

# Copiar el entorno virtual con todas las librerías desde la etapa 'builder'
COPY --from=builder /opt/venv /opt/venv

# Asegurar que el entorno virtual tenga prioridad en el PATH
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

# Copiar el código fuente de la aplicación
COPY --chown=appuser:appgroup src/ /app/src/

# Cambiar al usuario seguro antes de ejecutar
USER appuser

# Comando de entrada
CMD ["python", "src/main.py"]

```

---

## 🏋️‍♂️ Práctica de la Lección 02

1. Ubicate en la carpeta `practica/modulo_04/` de tu repositorio local.
2. Creá una subcarpeta `app_etl_docker/`:

```
practica/modulo_04/app_etl_docker/
├── .dockerignore
├── Dockerfile
├── requirements.txt
└── src/
    └── main.py

```

1. Escribí los archivos:
  * **requirements.txt**: Agregá `polars==1.8.0`.
  * **src/main.py**: Un script breve de Polars que genere un DataFrame sintético de 5 filas e imprima el resultado en pantalla.
  * **Dockerfile**: Implementá el patrón Multi-stage de 2 etapas descrito arriba.
  * **.dockerignore**: Agregá `__pycache__` y `.env`.
2. Construí la imagen desde la terminal ejecutando:

```
docker build -t mi_etl_polars:v1 practica/modulo_04/app_etl_docker/

```

1. Ejecutá el contenedor y comprobá la salida limpia:

```
docker run --rm mi_etl_polars:v1
```