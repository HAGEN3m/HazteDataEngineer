# 🐍 Lección 30.B: Profiling Avanzado de CPU y Memoria RAM (cProfile, tracemalloc y Line Profiler)

&gt; **Propósito**: Identificar científicamente cuellos de botella de rendimiento (*bottlenecks*) y fugas de memoria en pipelines de Python utilizando herramientas de profiling determinista y rastreo de asignaciones de memoria en tiempo de ejecución.

---

## 📌 1\. La Regla de Oro del Perfilado: "No Asumas, Mide"

En ingeniería de software y datos, optimizar código basándote en intuición suele ser un error. El **80% del tiempo de ejecución de un programa se concentra en el 20% del código** (Principio de Pareto).

```
[ Intuición / Adivinar ]  ---&gt;  Suele optimizar código que no impacta en el runtime total.
[ Profiling Científico ]  ---&gt;  Identifica la línea exacta de código que satura la CPU o la RAM.

```

### Tipos de Profiling en Python:

1. **CPU Profiling**: Mide el número de llamadas a funciones y el tiempo acumulado (*cumulative time*) en cada una.
2. **Memory Profiling**: Rastrea qué líneas o estructuras están reservando bloques de memoria RAM en el Heap.

---

## 🔬 2\. Profiling de CPU con `cProfile` y `pstats`

`cProfile` es el profilador determinista nativo de CPython. Registra cada llamada a función con un overhead mínimo.

### Métricas Clave de `cProfile`:

* **ncalls**: Número de veces que se llamó a la función.
* **tottime**: Tiempo total consumido en la propia función (excluyendo llamadas a subfunciones).
* **percall**: `tottime` dividido por `ncalls`.
* **cumtime**: Tiempo acumulado ejecutando esa función y **todas sus subfunciones**.

### Ejemplo Práctico de Profiling de CPU:

```
import cProfile
import pstats
import time

def funcion_lenta():
    # Simula un cálculo pesado en CPU
    return sum(i**2 for i in range(5_000_000))

def funcion_rapida():
    time.sleep(0.1)

def pipeline_principal():
    funcion_rapida()
    resultado = funcion_lenta()
    return resultado

# Ejecutar el profiler sobre el pipeline
if __name__ == "__main__":
    profiler = cProfile.Profile()
    profiler.enable()

    pipeline_principal()

    profiler.disable()

    # Imprimir estadísticas ordenadas por tiempo acumulado (cumtime)
    stats = pstats.Stats(profiler).sort_stats("cumtime")
    stats.print_stats(10)  # Mostrar las top 10 funciones más pesadas

```

---

## 🛠️ 3\. Line-by-Line CPU Profiling con `line_profiler`

Mientras que `cProfile` te dice *qué función* es lenta, `line_profiler` te dice **qué línea exacta dentro de la función** se lleva el tiempo.

### Instalación y Uso:

```
uv pip install line-profiler

```

Decoramos la función objetivo con `@profile` (sin necesidad de importarlo) y ejecutamos desde la terminal:

```
# script_a_perfilar.py
@profile
def transformar_registros(registros):
    resultados = []
    for reg in registros:
        # Línea potencialmente lenta
        valor_limpio = reg.strip().lower()
        if "error" in valor_limpio:
            resultados.append(valor_limpio)
    return resultados

```

Ejecución en consola:

```
kernprof -l -v script_a_perfilar.py

```

---

## ⚡ 4\. Profiling de Memoria RAM con `tracemalloc`

`tracemalloc` es el módulo nativo de CPython que rastrea bloques de memoria asignados por el intérprete, permitiendo comparar *snapshots* antes y después de una transformación masiva.

### Rastreo de Memory Leaks con `tracemalloc`:

```
import sys
import tracemalloc

def procesar_datos_masivos():
    # Inicia el rastreo de asignaciones de memoria
    tracemalloc.start()

    # Snapshot 1: Antes de cargar datos
    snapshot1 = tracemalloc.take_snapshot()

    # Simulamos crear un objeto pesado que se queda en RAM
    datos_pesados = [dict(id=i, payload="x" * 100) for i in range(500_000)]

    # Snapshot 2: Después de cargar datos
    snapshot2 = tracemalloc.take_snapshot()

    # Comparar diferencia entre snapshots
    estadisticas = snapshot2.compare_to(snapshot1, "lineno")

    print("TOP 3 LÍNEAS QUE MÁS MEMORIA RESERVARON:")
    for stat in estadisticas[:3]:
        print(stat)

if __name__ == "__main__":
    procesar_datos_masivos()

```

---

## ⚠️ 5\. Identificación de Cuellos de Botella por C-Extensions vs. Python Puro

Un hallazgo común durante el profiling en Data Engineering es que **el código escrito en Python puro es de 10x a 100x más lento que delegar a librerías compiladas en C/Rust (NumPy, Polars, PyArrow)**.

| Operación                | Implementación Python Puro                 | Delegación C/Vectorizada (NumPy/Polars)    |
| ------------------------ | ------------------------------------------ | ------------------------------------------ |
| **Sumar 10M de números** | Bucle `for` / List Comprehension (\~0.85s) | `np.sum()` / `pl.col().sum()` (\~0.01s)    |
| **Búsqueda en texto**    | `str.contains()` en bucle Python           | Expresiones vectorizadas en Apache Arrow   |
| **Overhead de CPU**      | Alto (Interpreter Loop de CPython)         | Nulo (Ejecución directa en código máquina) |

---

## 🏋️‍♂️ Ejercicio Práctico Hands-On: Diagnóstico y Refactor de Pipeline Lento

Crea el archivo `laboratorio_profiling.py` para medir y corregir un pipeline de transformación de texto:

```
import cProfile
import pstats
import time

# ❌ VERSIÓN LENTA (Bucle tradicional y concatenación de strings)
def transformacion_lenta(datos):
    resultado = ""
    for texto in datos:
        resultado += texto.upper() + ","
    return resultado

# ✅ VERSIÓN OPTIMIZADA (Uso de .join y generadores)
def transformacion_optimizada(datos):
    return ",".join(texto.upper() for texto in datos)

if __name__ == "__main__":
    dataset = ["usuario_" + str(i) for i in range(200_000)]

    print("--- Profiling Versión Lenta ---")
    prof1 = cProfile.Profile()
    prof1.runcall(transformacion_lenta, dataset)
    pstats.Stats(prof1).sort_stats("tottime").print_stats(3)

    print("--- Profiling Versión Optimizada ---")
    prof2 = cProfile.Profile()
    prof2.runcall(transformacion_optimizada, dataset)
    pstats.Stats(prof2).sort_stats("tottime").print_stats(3)

```

---

## 🧠 Checkpoint de Autoevaluación

1. ¿Cuál es la diferencia entre el tiempo total (`tottime`) y el tiempo acumulado (`cumtime`) en los reportes de `cProfile`?
2. ¿Qué ventaja ofrece `line_profiler` sobre `cProfile` cuando intentamos optimizar una función específica de muchas líneas?
3. ¿Cómo nos ayuda el módulo `tracemalloc` a detectar fugas de memoria (*memory leaks*) entre dos etapas de un pipeline?
4. ¿Por qué sustituir un bucle `for` en Python nativo por operaciones vectorizadas en Polars o PyArrow elimina el cuello de botella de la CPU?