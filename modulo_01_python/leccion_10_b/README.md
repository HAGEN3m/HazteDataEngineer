# 🐍 Lección 10.B: I/O Streaming, Buffering y Procesamiento de Archivos Gigantes

&gt; **Propósito**: Dominar el procesamiento de datos por flujo (*streaming*) y bloques (*chunking*) en Python nativo para manipular archivos de decenas de gigabytes sin saturar la RAM del servidor, entendiendo la arquitectura del sistema de archivos, descriptores I/O y buffers.

---

## 📌 1. El Problema del I/O Tradicional con Archivos Masivos

El error más común en scripts iniciales de ingesta de datos es leer un archivo completo en memoria mediante `.read()` o `readlines()`.

```python
# ❌ ANTI-PATRÓN DE PRODUCCIÓN: Carga Completa (Eager Loading)
with open("dataset_10gb.csv", "r") as f:
    contenido = f.readlines()  # Intenta cargar 10 GB de strings a la RAM

```

### ¿Por qué colapsa la memoria RAM?

1. **Multiplicador de Overhead**: Como aprendimos en la Lección 01.B, una cadena de texto en Python tiene un overhead de 49+ bytes. Un CSV de **10 GB** en disco puede convertirse en **25–35 GB** de objetos `PyObject` en memoria RAM.
2. **Out Of Memory (OOM) Killer**: El Kernel de Linux, al detectar que el proceso de Python consume casi toda la memoria disponible, lo elimina inmediatamente arrojando un error `Killed` o `MemoryError`.

---

## 🔬 2\. Arquitectura de I/O: Buffering y Descriptores de Archivo

Cuando abres un archivo en el sistema operativo, ocurre la siguiente interacción entre Python y el Kernel:

```
[ Disco SSD / HDD ] &lt;---&gt; [ OS Kernel Page Cache ] &lt;---&gt; [ Python I/O Buffer ] &lt;---&gt; [ Tu Código ]

```

### Conceptos Clave de I/O de Bajo Nivel

* **Descriptor de Archivo (** **fd** **)**: Un entero que asigna el Kernel de Linux para identificar un recurso abierto.
* **Buffer de Lectura**: Un espacio intermedio de memoria (típicamente de 8 KB a 64 KB) donde el sistema operativo precarga bloques del disco para minimizar los accesos físicos.
* **Cursor de Archivo (** **seek** **/** **tell** **)**:
  * `f.tell()`: Devuelve la posición exacta en bytes del puntero de lectura dentro del archivo.
  * `f.seek(offset)`: Mueve el puntero a una posición específica en bytes (ideal para reintentos o procesamiento paralelo por rangos).

---

## 🛠️ 3\. El Patrón "Generator Pipeline" para ETLs In-Memory

Para procesar volúmenes masivos con un consumo de RAM constante (menor a 50 MB), conectamos **generadores perezosos** (*lazy generators*) en una tubería de datos donde cada línea fluye de extremo a extremo sin acumularse.

```
[ Lectura en Streaming ] ---&gt; [ Limpieza / Parseo ] ---&gt; [ Filtro ] ---&gt; [ Escritura / Destino ]
    (yield linea)                 (yield dict)          (yield row)           (sink final)

```

### Ejemplo de Implementación Completa:

```
import csv

# 1. Generador de Lectura Línea por Línea
def leer_linea_por_linea(ruta_archivo):
    with open(ruta_archivo, "r", encoding="utf-8") as archivo:
        for linea in archivo:
            yield linea

# 2. Generador de Transformación (Parseo a Diccionario)
def parsear_csv(stream_lineas):
    lector = csv.DictReader(stream_lineas)
    for registro in lector:
        yield registro

# 3. Generador de Filtrado
def filtrar_transacciones_altas(stream_registros, umbral=1000.0):
    for reg in stream_registros:
        if float(reg.get("monto", 0)) &gt; umbral:
            yield reg

# 4. Consumo final (Pipeline Lazy)
archivo_origen = "transacciones_gigante.csv"

pipeline = filtrar_transacciones_altas(
    parsear_csv(leer_linea_por_linea(archivo_origen)), umbral=5000.0
)

# Se procesa una sola fila a la vez en RAM
for registro_filtrado in pipeline:
    print(
        f"Alerta: Transacción de {registro_filtrado['monto']} USD por {registro_filtrado['usuario']}"
    )

```

---

## ⚙️ 4\. Procesamiento por Bloques (*Chunking*)

Cuando trabajar fila por fila genera demasiado overhead en llamadas a bases de datos o APIs externas, agrupamos los registros en **bloques (chunks)** optimizados.

```
def leer_por_bloques(ruta_archivo, tamaño_bloque=1000):
    """Lee un archivo y emite bloques de N filas."""
    with open(ruta_archivo, "r", encoding="utf-8") as f:
        bloque = []
        for linea in f:
            bloque.append(linea)
            if len(bloque) == tamaño_bloque:
                yield bloque
                bloque = []
        if bloque:
            yield bloque

```

---

## ⚠️ 5\. Casos de Borde en Producción y Hardening de I/O

1. **Líneas Incompletas / Corruptas**: Archivos interrumpidos a mitad de escritura. Se deben ignorar o derivar a una *Dead Letter Queue* (DLQ).
2. **Encodings Inconsistentes**: Archivos con mezcla de UTF-8, Latin-1 o caracteres BOM (`\ufeff`).
3. **Acumulación Accidental de Referencias**: Guardar referencias en una lista global dentro del bucle rompe el beneficio del streaming.

```
# ❌ ERROR COMÚN: Guardar todo en una lista invalida el streaming
historico = []
for registro in pipeline:
    historico.append(registro)  # ¡Satura la RAM nuevamente!

```

---

## 🏋️‍♂️ Ejercicio Práctico Hands-On: Procesamiento Defensivo con Medición de RAM

Crea el archivo `procesador_streaming.py` para procesar un log masivo filtrando eventos de error y registrando el pico de RAM consumido:

```
import sys
import time

def procesar_log_streaming(ruta_log, ruta_salida):
    registros_procesados = 0

    with (
        open(ruta_log, "r", encoding="utf-8", errors="replace") as entrada,
        open(ruta_salida, "w", encoding="utf-8") as salida,
    ):

        for linea in entrada:
            if "ERROR" in linea or "CRITICAL" in linea:
                salida.write(linea)
                registros_procesados += 1

    return registros_procesados

# Medición de memoria usada por el script
if __name__ == "__main__":
    print("Iniciando procesamiento en streaming...")
    # El archivo puede pesar 50 GB, pero el script consumirá menos de 10 MB de RAM

```

---

## 🧠 Checkpoint de Autoevaluación

1. ¿Por qué cargar un archivo CSV de 10 GB mediante `f.readlines()` en Python puede llegar a consumir más de 30 GB de memoria RAM?
2. ¿Qué ventaja ofrece conectar múltiples generadores (`yield`) en forma de tubería (*pipeline*) para el procesamiento de datos?
3. ¿Para qué sirven las funciones `f.tell()` y `f.seek()` al manipular descriptores de archivo en el sistema operativo?
4. ¿Qué diferencia existe entre el procesamiento fila por fila (*row-by-row streaming*) y el procesamiento por bloques (*chunking*)?