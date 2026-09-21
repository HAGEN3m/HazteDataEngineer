# 🐍 Lección 22: Generadores (`yield`, `next()`) e Iteradores (Procesamiento de Archivos Gigantes)

En la Ingeniería de Datos, uno de los errores más comunes al iniciar es intentar cargar datasets gigantescos (ejemplo: un archivo CSV o JSON de 50 GB) directamente en una lista de Python usando `.readlines()` o `json.load()`. Si tu servidor tiene 8 GB de Memoria RAM, el script colapsará inmediatamente con un error fatídico de memoria: **MemoryError** (*Out of Memory / OOM*).

Para procesar volúmenes masivos de datos sin llenar la Memoria RAM, Python utiliza el concepto de **Evaluación Perezosa (** **Lazy Evaluation** **)** a través de los **Generadores** e **Iteradores**.

---

## 1\. ¿Qué es un Generador y cómo funciona `yield`?

A diferencia de una función tradicional que calcula todos sus resultados, los guarda en una lista y los devuelve de golpe con `return`, un **Generador**:

1. Calcula y entrega **un solo elemento a la vez**.
2. **Pausa** su ejecución reteniendo el estado de todas sus variables locales.
3. Se reanuda en el punto exacto donde se pausó cuando se le solicita el siguiente elemento.

Para transformar una función en un generador, reemplazamos la palabra clave `return` por **yield**.

```
# 🔴 ENFOQUE TRADICIONAL (Consume mucha RAM):
def generar_lista_numeros(n: int) -&gt; list:
    resultados = []
    for i in range(n):
        resultados.append(i) # Guarda N elementos al mismo tiempo en RAM
    return resultados

# 🟢 ENFOQUE CON GENERADOR (Consumo de RAM constante = ~0 MB):
def generar_secuencia_lazy(n: int):
    for i in range(n):
        yield i # Entrega un número y pausa la función

```

---

## 2\. Consumir un Generador (`next()` y Bucle `for`)

Un generador se puede consumir de dos formas:

### A. Manualmente con la función `next()`

Cada llamada a `next(generador)` ejecuta la función hasta encontrar el siguiente `yield`:

```
gen = generar_secuencia_lazy(3)

print(next(gen)) # 0 (La función se frena acá)
print(next(gen)) # 1 (Se reanuda y se vuelve a frenar)
print(next(gen)) # 2

# Si llamás a next() una 4ta vez, Python lanza la excepción StopIteration

```

### B. Automáticamente con un bucle `for`

El bucle `for` captura internamente la excepción `StopIteration` y finaliza de forma limpia:

```
for numero in generar_secuencia_lazy(1000000000): # ¡1 billón de elementos!
    if numero &gt;= 3:
        break
    print(f"Procesando elemento: {numero}")

```

---

## 3\. Generador para Streaming de Archivos Gigantes

Este es el patrón estándar de producción para leer archivos de texto o CSV línea por línea en streaming:

```
from typing import Generator

def lector_streaming_csv(ruta_archivo: str) -&gt; Generator[str, None, None]:
    """Lee un archivo línea por línea sin cargarlo completo en memoria."""
    with open(ruta_archivo, mode="r", encoding="utf-8") as archivo:
        for linea in archivo:
            # yield entrega únicamente una línea por iteración
            yield linea.strip()

# Uso en el pipeline:
# Se procesan 10 millones de filas sin consumir más de un par de Megabytes de RAM
for fila_raw in lector_streaming_csv("dataset_50gb.csv"):
    # Procesar fila por fila...
    pass

```

---

## 4\. Expresiones Generadoras (*Generator Expressions*)

Así como existen las *List Comprehensions*, podés crear generadores anónimos usando **paréntesis** **()** en lugar de corchetes `[]`:

```
# List Comprehension (Crea toda la lista en memoria):
lista_cuadrados = [x ** 2 for x in range(1000000)] # Ocupa ~8 MB en RAM

# Expresión Generadora (Crea un generador perezoso):
gen_cuadrados = (x ** 2 for x in range(1000000))   # Ocupa ~100 Bytes en RAM

print(next(gen_cuadrados)) # 0
print(next(gen_cuadrados)) # 1

```

---

## 🏋️‍♂️ Práctica de la Lección 22

1. Creá el archivo `ej_22_generadores.py` dentro de la carpeta `practica/`.
2. Escribí un script que implemente un **pipeline de filtrado y transformación en streaming (pipeline lazy)**:
  * **Paso 1**: Creá una función generadora llamada `generar_transacciones_raw(cantidad: int)` que haga `yield` de un diccionario simulado por cada iteración: `{"id": i, "monto": i * 50.0, "estado": "COMPLETADA" if i % 2 == 0 else "PENDIENTE"}`
  * **Paso 2**: Creá una función generadora llamada `filtrar_completadas(generador_origen)` que reciba el generador anterior, recorra los elementos con un `for` y haga `yield` **solo** de aquellas transacciones con `"estado" == "COMPLETADA"`.
  * **Paso 3**: Creá una función generadora llamada `aplicar_impuesto(generador_origen, porcentaje: float = 21.0)` que reciba el generador filtrado y haga `yield` del registro con una clave nueva `"monto_con_impuesto"`.
3. En el bloque `if __name__ == "__main__":`:
  * Conectá los generadores en cadena (Pipeline Lazy):

```
stream_raw = generar_transacciones_raw(10)
stream_filtrado = filtrar_completadas(stream_raw)
stream_final = aplicar_impuesto(stream_filtrado)

```

1. Consumí los primeros 3 resultados del `stream_final` usando un bucle `for` o `next()` e imprimí los registros resultantes.
2. Ejecutá tu script desde la terminal: `python3 practica/ej_22_generadores.py`