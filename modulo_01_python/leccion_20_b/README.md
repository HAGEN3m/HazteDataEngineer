# 🐍 Lección 20.B: Programación Asincrónica con asyncio e Ingesta Masiva de APIs

&gt; **Propósito**: Dominar el modelo de programación asincrónica en Python (`asyncio` y `httpx`/`aiohttp`) para construir ingestas masivas de APIs REST con concurrencia no bloqueante, control estricto de rate limits y reintentos defensivos.

---

## 📌 1\. Concurrencia vs. Paralelismo vs. Asincronía

Antes de escribir código asincrónico, es fundamental entender las diferencias en la arquitectura de ejecución del sistema operativo y CPython:

```
+-------------------+-----------------------------------+-------------------------------------+
| Concepto          | Mecanismo en Python               | Caso de Uso Principal               |
+-------------------+-----------------------------------+-------------------------------------+
| Paralelismo       | multiprocessing (Varios procesos) | Tareas CPU-bound (Cálculos, ML)     |
| Concurrencia      | threading (Hilos del SO con GIL)  | I/O bloqueante tradicional          |
| Asincronía (Async)| asyncio (Event Loop de 1 solo hilo)| I/O-bound masivo (Miles de peticiones)|
+-------------------+-----------------------------------+-------------------------------------+

```

### ¿Por qué `asyncio` revolucionó las ingestas de datos?

En llamadas HTTP a APIs o bases de datos, **el 95% del tiempo el script está esperando** a que la red responda (I/O Wait).

* Con código sincrónico (`requests`), la CPU queda completamente ociosa esperando cada respuesta una por una.
* Con `asyncio`, mientras la red responde a la Petición #1, el programa envía la Petición #2, #3 y #100 **en un solo hilo**, multiplexando las conexiones a nivel de Kernel de Linux (`epoll`/`kqueue`).

---

## 🔬 2\. Arquitectura Interna de asyncio: El Event Loop

El motor de la asincronía es el **Event Loop** (Bucle de Eventos):

```
       CÓDIGO                      EVENT LOOP (1 solo hilo)
   ┌─────────────┐             ┌───────────────────────────────┐
   │ async def   │ ──────────&gt; │  1. Registrar Corrutina       │
   │ await fetch │             │  2. Enviar petición HTTP      │
   └─────────────┘             │  3. Ceder control (Yield)     │
                               │  4. Procesar otra tarea lista │
                               │  5. Reanudar cuando hay datos │
                               └───────────────────────────────┘

```

### Conceptos Clave

1. **Corrutina (** **async def** **)**: Una función especial que se puede pausar y reanudar. Al llamarla, no se ejecuta inmediatamente; devuelve un objeto corrutina.
2. **Punto de Pausa (** **await** **)**: Le indica al Event Loop: *"Pauso esta función aquí hasta que la red/disco responda. Mientras tanto, ejecuta otra tarea"*.
3. **I/O Multiplexing**: El sistema operativo notifica al Event Loop mediante señales cuando los sockets de red reciben respuestas.

&gt; ⚠️ **REGLA DE ORO**: Nunca uses librerías bloqueantes (como `requests`, `time.sleep` o `urllib3`) dentro de un Event Loop asincrónico. Bloquearán todo el bucle de eventos, destruyendo los beneficios de concurrencia. Usa alternativas no bloqueantes como `httpx`, `aiohttp` o `asyncio.sleep`.

---

## 🛠️ 3\. Control de Concurrencia en Producción: Semáforos y Rate Limiting

Si envías 5.000 peticiones HTTP simultáneas sin control, ocurrirá uno de estos dos problemas:

1. La API de origen bloqueará tu IP con errores **HTTP 429 Too Many Requests**.
2. Agotarás los sockets de red del sistema operativo (*Connection Reset by Peer*).

Para solucionar esto, usamos un **asyncio.Semaphore** (un contador que limita cuántas corrutinas se ejecutan en paralelo).

```
import asyncio
import httpx

# Limitar a máximo 10 peticiones concurrentes simultáneas
semaforo = asyncio.Semaphore(10)

async def peticion_segura(client, url):
    async with semaforo:  # Espera turno si ya hay 10 peticiones en vuelo
        respuesta = await client.get(url)
        return respuesta.status_code

```

---

## ⚡ 4\. Reintentos Asincrónicos con Backoff Exponencial y Jitter

Las APIs de producción fallan por micro-cortes de red. Tu pipeline debe reintentar con un tiempo de espera creciente y un componente aleatorio (*Jitter*) para no saturar el servidor al recuperarse.

```
import asyncio
import random
import httpx

async def fetch_con_reintentos(client, url, max_reintentos=3):
    base_delay = 1.0  # Tiempo base en segundos

    for intento in range(1, max_reintentos + 1):
        try:
            response = await client.get(url, timeout=5.0)
            response.raise_for_status()
            return response.json()
        except (httpx.HTTPError, httpx.TimeoutException) as e:
            if intento == max_reintentos:
                print(f"❌ Fallo definitivo en {url}: {e}")
                raise e

            # Algoritmo Exponential Backoff con Jitter
            jitter = random.uniform(0.1, 0.5)
            espera = (base_delay * (2 ** (intento - 1))) + jitter
            print(
                f"⚠️ Error en {url}. Reintento {intento}/{max_reintentos} en {espera:.2f}s..."
            )
            await asyncio.sleep(espera)

```

---

## 🏋️‍♂️ Ejercicio Práctico Hands-On: Extractor Masivo de APIs Async

Crea el archivo `ingesta_api_async.py`. Simularemos descargar información de 50 endpoints de API con un límite estricto de concurrencia de 5 peticiones en paralelo:

```
import asyncio
import time
import httpx

async def consultar_endpoint(sem, client, item_id):
    url = f"https://jsonplaceholder.typicode.com/posts/{item_id}"

    async with sem:
        try:
            response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                return {"id": item_id, "titulo": data["title"][:20]}
        except Exception as e:
            return {"id": item_id, "error": str(e)}

async def main():
    inicio = time.perf_counter()

    # 1. Crear cliente HTTP asincrónico con conexión reutilizable
    limits = httpx.Limits(max_keepalive_connections=20, max_connections=50)
    async with httpx.AsyncClient(limits=limits) as client:

        # 2. Definir semáforo de concurrencia
        sem = asyncio.Semaphore(5)

        # 3. Crear lista de tareas (50 peticiones)
        tareas = [consultar_endpoint(sem, client, i) for i in range(1, 51)]

        # 4. Ejecutar todas las tareas concurrentemente
        resultados = await asyncio.gather(*tareas)

    fin = time.perf_counter()

    print(
        f"✅ Ingesta finalizada: {len(resultados)} registros procesados en {fin - inicio:.2f} segundos."
    )
    print(f"Muestra del primer registro: {resultados[0]}")

# Ejecutar el bucle de eventos
if __name__ == "__main__":
    asyncio.run(main())

```

---

## 🧠 Checkpoint de Autoevaluación

1. ¿Por qué usar la librería `requests` dentro de una función decorada con `async def` invalida los beneficios de `asyncio`?
2. ¿Qué función cumple el punto de pausa `await` y qué hace el Event Loop mientras espera la respuesta?
3. ¿Por qué es crítico configurar un `asyncio.Semaphore` cuando realizamos ingestas masivas de datos hacia APIs de terceros?
4. ¿Qué ventaja tiene el patrón *Exponential Backoff with Jitter* frente a reintentar inmediatamente con un intervalo fijo?