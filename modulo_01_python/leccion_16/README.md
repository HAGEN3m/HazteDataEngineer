# 🐍 Lección 16: Variables de Entorno (`.env`) y Gestión de Credenciales

En la Ingeniería de Datos, **jamás se deben hardcodear (escribir directamente en el código) contraseñas, claves de API, tokens de acceso o URLs de bases de datos**. Si subís un archivo `.py` con credenciales a un repositorio público en GitHub, en cuestión de minutos bots automatizados van a robar tus claves.

En esta lección aprenderemos a separar el código de la configuración sensible utilizando **Variables de Entorno** y archivos **.env**, la regla de oro de la seguridad en software y datos.

---

## 1\. El Principio de Seguridad y la Regla del `.gitignore`

La configuración sensible debe vivir **fuera del repositorio de código**, en el sistema operativo del servidor o en un archivo local `.env`.

### 🚨 La Regla de Oro:

1. El archivo **.env** guarda las claves reales en tu máquina local. **NUNCA se sube a Git.**
2. El archivo **.gitignore** debe incluir la línea `.env` para que Git lo ignore automáticamente.
3. Se crea un archivo **.env.example** (que sí se sube a Git) como plantilla con valores vacíos para que otros desarrolladores sepan qué variables necesita el proyecto.

```
mi_proyecto/
├── .gitignore        &lt;-- Contiene la línea ".env"
├── .env.example      &lt;-- Plantilla pública (ej: DB_HOST=localhost, DB_PASS=)
├── .env              &lt;-- Credenciales reales (¡NUNCA SE SUBE A GIT!)
└── main.py

```

---

## 2\. Leer Variables de Entorno Nativas (`os.getenv`)

El módulo nativo `os` de Python permite consultar las variables de entorno del sistema operativo a través de `os.getenv()`:

```
import os

# os.getenv("NOMBRE_VARIABLE", valor_por_defecto)
entorno = os.getenv("APP_ENV", "development")
puerto = int(os.getenv("DB_PORT", "5432"))

print(f"Modo: {entorno} | Puerto: {puerto}")

```

&gt; 💡 **Diferencia clave**: Usar `os.getenv("CLAVE")` devuelve `None` si la variable no existe (evitando que el programa colapse). En cambio, `os.environ["CLAVE"]` lanza un error `KeyError` si la clave falta.

---

## 3\. Cargar Archivos `.env` con `python-dotenv`

Para no tener que configurar variables en el sistema operativo manualmente cada vez que desarrollamos, usamos la librería de terceros `python-dotenv`.

### Instalación (en terminal):

```
pip install python-dotenv

```

### Contenido de tu archivo `.env`:

```
DB_HOST=127.0.0.1
DB_PORT=5432
DB_USER=data_engineer
DB_PASSWORD=SuperSecretPass123!
API_KEY=key_live_abc123xyz

```

### Uso en Python:

```
import os
from dotenv import load_dotenv

# load_dotenv() busca el archivo .env en la raíz del proyecto y lo carga en memoria
load_dotenv()

# Ahora podemos leer las variables con os.getenv()
db_host = os.getenv("DB_HOST")
db_pass = os.getenv("DB_PASSWORD")

print(f"Conectando a {db_host} con contraseña: {'*' * len(db_pass) if db_pass else 'NO_SET'}")

```

---

## 4\. Validación Defensiva de Credenciales al Iniciar el Pipeline

Un pipeline profesional **no debe arrancar si faltan credenciales críticas**. Debemos validar las variables requeridas al inicio del script antes de ejecutar cualquier procesamiento pesado:

```
import os
from dotenv import load_dotenv

def cargar_y_validar_configuracion() -&gt; dict:
    load_dotenv()
    
    variables_requeridas = ["DB_HOST", "DB_USER", "API_KEY"]
    variables_faltantes = [var for var in variables_requeridas if not os.getenv(var)]
    
    if variables_faltantes:
        raise EnvironmentError(
            f"🔴 Error crítico: Faltan las siguientes variables de entorno: {', '.join(variables_faltantes)}"
        )
    
    return {
        "host": os.getenv("DB_HOST"),
        "user": os.getenv("DB_USER"),
        "api_key": os.getenv("API_KEY")
    }

```

---

## 🏋️‍♂️ Práctica de la Lección 16

1. En la raíz de tu proyecto o carpeta de práctica, creá un archivo llamado `.env` y agregá estas líneas:

```
PIPELINE_ENV=stage
API_SECRET_TOKEN=tok_live_9988776655
MAX_REINTENTOS=5

```

1. Creá también el archivo `.env.example` como plantilla pública:

```
PIPELINE_ENV=development
API_SECRET_TOKEN=tu_token_aqui
MAX_REINTENTOS=3

```

1. Creá el archivo `ej_16_variables_entorno.py` dentro de la carpeta `practica/`:
  * Importá `os` y `from dotenv import load_dotenv`.
  * Cargá las variables del archivo `.env` usando `load_dotenv()`.
  * Definí una función `obtener_config_pipeline()` que:
    * Valide que `API_SECRET_TOKEN` exista. Si no existe, lance un `ValueError("Token de API no configurado")`.
    * Lea `MAX_REINTENTOS` convirtiéndolo a entero (`int`). Si no existe, use `3` por defecto.
    * Deuelva un diccionario con la configuración lista para consumir.
  * Ejecutá la función, mostrá la configuración en pantalla (ocultando el token sensible con asteriscos) y probá qué pasa si borrás la variable `.env` para verificar el manejo del error.
2. Ejecutá tu script en la terminal: `python3 practica/ej_16_variables_entorno.py`