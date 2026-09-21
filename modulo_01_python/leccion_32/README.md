# 🐍 Lección 32: Consumo Defensivo de APIs REST con `requests` (Rate Limiting, Retries y Backoff Exponencial)

En la Ingeniería de Datos, gran parte de la ingesta de datos (*Extract*) proviene de **APIs REST** externas (servicios como Stripe, Salesforce, Google Analytics o hubs de datos públicos).

Sin embargo, la red es intrínsecamente inestable. Las peticiones HTTP pueden fallar por latencia, caídas temporales del servidor externo o cuotas de consumo superadas (**Rate Limits**). En esta lección aprenderemos a construir clientes HTTP robustos y defensivos utilizando **requests**, **requests.Session** y **urllib3.util.Retry**.

---

## 1\. Códigos de Estado HTTP Críticos en Pipelines

Al consumir una API, la respuesta incluye un código de estado (*HTTP Status Code*). Debemos saber interpretar y reaccionar ante cada categoría:

| Código / Rango                                    | Significado                             | Acción en Data Engineering                                |
| ------------------------------------------------- | --------------------------------------- | --------------------------------------------------------- |
| **200 OK** **/** **201 Created**                  | Petición exitosa                        | Procesar el payload JSON.                                 |
| **400 Bad Request** **/** **422**                 | Parámetros o JSON mal formado           | Error de código. Lanzar excepción e inspeccionar payload. |
| **401 Unauthorized** **/** **403**                | API Key vencida o sin permisos          | Fallo de credenciales. Interrumpir pipeline.              |
| **429 Too Many Requests**                         | Límite de cuota excedido (*Rate Limit*) | **Reintentar con pausa (Backoff Exponencial).**           |
| **500** **/** **502** **/** **503** **/** **504** | Errores temporales de servidor/gateway  | **Reintentar de forma defensiva.**                        |

---

## 2\. Peticiones Básicas y Timeouts Explícitos

El error más peligroso al usar la librería `requests` es realizar peticiones sin especificar un **timeout**. Si el servidor remoto se congela, tu script quedará colgado indefinidamente consumiendo recursos.

```
import requests

url = "https://api.ejemplo.com/v1/ventas"
headers = {"Authorization": "Bearer tok_live_123456"}

try:
    # SIEMPRE definir timeout: (tiempo_conexion, tiempo_lectura_respuesta)
    respuesta = requests.get(url, headers=headers, timeout=(3.05, 10.0))
    
    # Lanza HTTPError si el status es 4xx o 5xx
    respuesta.raise_for_status() 
    
    datos = respuesta.json()
    print(f"✅ Descargados {len(datos)} registros.")

except requests.exceptions.Timeout:
    print("🔴 Error: El servidor remoto tardó demasiado en responder.")
except requests.exceptions.HTTPError as err:
    print(f"🔴 Error HTTP {respuesta.status_code}: {err}")

```

---

## 3\. Estrategia Defensiva: Sesiones, Reintentos y Backoff Exponencial

Para evitar escribir bloques `try/except` con bucles `while` manuales para reintentar cada petición, la mejor práctica en Python es reutilizar conexiones con **requests.Session()** y montar un **HTTPAdapter** configurado con **urllib3.util.Retry**.

### ¿Qué es el Backoff Exponencial?

Es un algoritmo que incrementa exponencialmente el tiempo de espera entre cada reintento fallido (ej. esperar 1s, luego 2s, 4s, 8s...). Esto evita saturar el servidor remoto cuando está recuperándose de un fallo.

```
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

def crear_sesion_defensiva(
    retries_totales: int = 5, 
    factor_backoff: float = 1.0
) -&gt; requests.Session:
    """Crea una sesión de requests con reintentos automáticos y backoff exponencial."""
    
    sesion = requests.Session()
    
    # Configuración de estrategia de reintentos
    estrategia_reintentos = Retry(
        total=retries_totales,              # Número máximo de reintentos
        backoff_factor=factor_backoff,      # Factor de multiplicación de tiempo (1s, 2s, 4s...)
        status_forcelist=[429, 500, 502, 503, 504], # Reintentar solo en estos estados
        allowed_methods=["GET", "POST"]     # Verbos HTTP sobre los que reintentar
    )
    
    adaptador = HTTPAdapter(max_retries=estrategia_reintentos)
    
    # Montamos el adaptador para protocolos HTTP y HTTPS
    sesion.mount("http://", adaptador)
    sesion.mount("https://", adaptador)
    
    return sesion

```

---

## 4\. Manejo del Encabezado `Retry-After` (Rate Limiting)

Cuando una API responde con un código **429 Too Many Requests**, suele incluir un encabezado HTTP llamado **Retry-After**, el cual indica exactamente cuántos segundos debemos esperar antes de volver a consultar:

```
import time
import requests

def extraer_con_rate_limit(sesion: requests.Session, url: str) -&gt; dict:
    respuesta = sesion.get(url, timeout=5.0)
    
    if respuesta.status_code == 429:
        # Extraemos el tiempo de espera recomendado por la API (por defecto 5 segundos)
        segundos_espera = int(respuesta.headers.get("Retry-After", 5))
        print(f"⚠️ Rate Limit alcanzado. Pausando ejecución por {segundos_espera} segundos...")
        time.sleep(segundos_espera)
        # Reintentamos la petición
        return extraer_con_rate_limit(sesion, url)
        
    respuesta.raise_for_status()
    return respuesta.json()

```

---

## 🏋️‍♂️ Práctica de la Lección 32

1. Creá el archivo `ej_32_apis_defensivas.py` dentro de la carpeta `practica/`.
2. Escribí un cliente HTTP reutilizable para ingesta de datos:
  * Importá `requests`, `HTTPAdapter` y `Retry` de `urllib3.util`.
  * Implementá la clase `ClienteAPIDefensivo`:
    * Constructor `__init__(self, base_url: str, api_token: str)`:
      * Guarda `base_url` e inicializa una sesión con reintentos automáticos (máximo 4 reintentos para estados `429, 500, 502, 503, 504`).
      * Setea los encabezados por defecto en `self.sesion.headers`: `{"Authorization": f"Bearer {api_token}", "Accept": "application/json"}`
    * Método `obtener_datos(self, endpoint: str) -&gt; dict`:
      * Realiza una petición `GET` construyendo la URL completa.
      * Define un timeout de `(3.0, 10.0)`.
      * Captura excepciones de red y retorna el diccionario de datos o un payload de error defensivo.
3. En el bloque `if __name__ == "__main__":`:
  * Instanciá la clase usando una API pública de prueba (ejemplo: `https://httpbin.org`).
  * Probá realizar una petición al endpoint `/status/503` para verificar cómo la sesión reintenta automáticamente antes de fallar.
  * Probá una petición exitosa al endpoint `/json` e imprimí el resultado.
4. Ejecutá tu script desde la terminal: `python3 practica/ej_32_apis_defensivas.py`