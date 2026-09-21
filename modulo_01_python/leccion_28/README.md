# 🐍 Lección 28: Concurrencia y Paralelismo (`threading`, `multiprocessing` y `concurrent.futures`)

En los pipelines de Ingeniería de Datos, la velocidad de procesamiento suele verse limitada por dos cuellos de botella bien diferenciados:

1. **I/O-Bound (Limitado por Entrada/Salida)**: El script pasa la mayor parte del tiempo esperando respuestas externas (descargar 100 archivos desde S3, consultar una API REST o leer datos de una base de datos remota).
2. **CPU-Bound (Limitado por Procesamiento)**: El script satura el procesador realizando cálculos intensivos, transformaciones matemáticas complejas o parseo masivo de JSONs.

En esta lección aprenderemos a acelerar nuestros pipelines aplicando **Concurrencia y Paralelismo** de forma limpia y moderna.

---

## 1\. I/O-Bound vs. CPU-Bound y el GIL (*Global Interpreter Lock*)

Para elegir la herramienta adecuada, primero debemos entender una característica interna de CPython: el **GIL (Global Interpreter Lock)**.

* **El GIL**: Es un cerrojo que impide que múltiples hilos de ejecución (*threads*) ejecuten bytecode de Python al mismo tiempo dentro del mismo proceso.
* **Tareas I/O-Bound**: Cuando un hilo espera a la red o al disco, **libera el GIL**. Por lo tanto, el uso de **Hilos (** **threading** **/** **ThreadPoolExecutor** **)** es ideal para acelerar descargas y consultas concurrentes.
* **Tareas CPU-Bound**: Para aprovechar verdaderamente todos los núcleos (*cores*) de tu procesador en cálculos intensivos, debemos esquivar el GIL creando **Procesos Independientes (** **multiprocessing** **/** **ProcessPoolExecutor** **)**, donde cada proceso tiene su propia instancia de Python y su propia memoria.

| Tipo de Tarea | Cuello de Botella             | Solución Recomendada  | Mecanismo                              |
| ------------- | ----------------------------- | --------------------- | -------------------------------------- |
| **I/O-Bound** | Red, APIs, Lectura de Discos  | `ThreadPoolExecutor`  | Concurrencia por hilos (mismo proceso) |
| **CPU-Bound** | Cálculos, Parsing, Compresión | `ProcessPoolExecutor` | Paralelismo real (múltiples procesos)  |

---

## 2\. La Interfaz Moderna: `concurrent.futures`

Aunque Python incluye los módulos `threading` y `multiprocessing`, la forma estándar y profesional de trabajar con concurrencia desde Python 3.2 es el módulo **concurrent.futures**.

Provee una abstracción llamada **Executor** que gestiona automáticamente un grupo de trabajadores (*Pool* de hilos o procesos) y nos entrega objetos **Future** (promesas de resultados futuros).

---

## 3\. Concurrencia I/O-Bound con `ThreadPoolExecutor`

Imaginá que tenés que consultar 10 endpoints de una API. De forma secuencial (un bucle `for`), si cada consulta tarda 1 segundo, el proceso completo tardará 10 segundos. Con un pool de hilos, podés ejecutar las 10 consultas en paralelo en aproximadamente 1 segundo.

```
import time
from concurrent.futures import ThreadPoolExecutor

def consultar_api_cliente(cliente_id: int) -&gt; dict:
    """Simula una llamada HTTP con latencia de red."""
    time.sleep(1.0) # Simula espera I/O
    return {"cliente_id": cliente_id, "status": 200, "data": f"datos_{cliente_id}"}

clientes = [1-5]

# Ejecución concurrente con hasta 5 hilos simultáneos
inicio = time.time()
with ThreadPoolExecutor(max_workers=5) as executor:
    # executor.map aplica la función a cada elemento de la lista de forma concurrente
    resultados = list(executor.map(consultar_api_cliente, clientes))

fin = time.time()
print(f"⏱️ Procesados {len(resultados)} clientes en {fin - inicio:.2f} segundos.")
# Salida: ~1.00 segundo en lugar de 5.00 segundos.

```

---

## 4\. Paralelismo CPU-Bound con `ProcessPoolExecutor`

Para tareas intensivas de cómputo, el `ThreadPoolExecutor` no ofrece ganancias de velocidad debido al GIL. En su lugar, utilizamos **ProcessPoolExecutor** para distribuir la carga entre múltiples núcleos de la CPU:

```
import time
from concurrent.futures import ProcessPoolExecutor

def calcular_hash_intensivo(numero: int) -&gt; int:
    """Simula un cálculo intensivo en CPU."""
    total = 0
    for i in range(10_000_000):
        total += i * numero
    return total

if __name__ == "__main__":
    numeros = [6-9]
    
    inicio = time.time()
    # Utiliza múltiples procesos aislados (uno por cada core disponible)
    with ProcessPoolExecutor() as executor:
        resultados = list(executor.map(calcular_hash_intensivo, numeros))
    
    fin = time.time()
    print(f"⚡ Cálculo paralelo finalizado en {fin - inicio:.2f} segundos.")

```

&gt; ⚠️ **Nota importante de Windows**: Cuando usás `multiprocessing` o `ProcessPoolExecutor`, el código principal **debe estar obligatoriamente** dentro del bloque `if __name__ == "__main__":` para evitar un bucle infinito de creación de procesos.

---

## 🏋️‍♂️ Práctica de la Lección 28

1. Creá el archivo `ej_28_concurrencia.py` dentro de la carpeta `practica/`.
2. Escribí un script de **ingesta masiva concurrente y procesamiento paralelo**:
  * Definí una lista simulada de 8 URLs de archivos Parquet: `archivos = [f"s3://bucket-dw/landing/particion_{i}.parquet" for i in range(1, 9)]`
  * Definí la función `descargar_archivo_io(ruta_s3: str) -&gt; dict`:
    * Simulá una latencia de descarga de `0.5` segundos con `time.sleep(0.5)`.
    * Retorná un diccionario: `{"archivo": ruta_s3, "status": "DESCARGADO", "filas_raw": 5000}`.
  * En el bloque `if __name__ == "__main__":`:
    * **Paso 1**: Medí el tiempo de descargar los 8 archivos de forma secuencial con un bucle `for` tradicional.
    * **Paso 2**: Medí el tiempo de descargar los mismos 8 archivos usando `ThreadPoolExecutor(max_workers=4)`.
    * Imprimí en pantalla la diferencia de tiempo entre ambos enfoques.
3. Ejecutá tu script desde la terminal: `python3 practica/ej_28_concurrencia.py`