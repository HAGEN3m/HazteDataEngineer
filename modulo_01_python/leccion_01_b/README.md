# 🐍 Lección 01.B: CPython, Modelo de Memoria y Optimización de RAM

&gt; **Propósito**: Comprender el funcionamiento interno del intérprete CPython para escribir código eficiente en memoria, diagnosticar fugas de recursos (*memory leaks*) y entender el costo real de las estructuras de datos nativas de Python cuando se procesan volúmenes masivos de datos.

---

## 📌 1\. ¿Cómo maneja la memoria CPython por dentro?

En Python **todo es un objeto**. Cuando declaras una variable, no estás reservando una casilla con un valor directo; estás creando una **etiqueta (referencia)** que apunta a una estructura en la memoria RAM llamada `PyObject`.

```
        CÓDIGO (Stack)                   MEMORIA RAM (Heap)
   ┌──────────────────────┐           ┌──────────────────────────────┐
   │  registros = 100000  │ ────────&gt; │ PyObject (int)               │
   └──────────────────────┘           │ ├── ob_refcnt: 1 (Referencias)│
                                      │ ├── ob_type: int (Tipo)      │
                                      │ └── ob_ival: 100000 (Valor)  │
                                      └──────────────────────────────┘

```

### A. Anatomía de un `PyObject`

En CPython (el intérprete estándar de Python escrito en C), cualquier objeto en el Heap contiene como mínimo:

* **ob\_refcnt** **(Reference Counter)**: Contador de referencias. Indica cuántas variables o colecciones apuntan a este objeto. Cuando llega a `0`, el espacio se libera.
* **ob\_type**: Puntero hacia el tipo del objeto (ej. `int`, `list`, `dict`), definiendo qué métodos puede ejecutar.
* **El valor del objeto**: La representación real del dato en bytes.

---

## 🔬 2\. Memoria Stack (Pila) vs. Heap (Montículo)

La memoria RAM asignada al proceso de Python se divide en dos áreas de trabajo:

| Característica | Stack (Pila)                                                        | Heap (Montículo)                                               |
| -------------- | ------------------------------------------------------------------- | -------------------------------------------------------------- |
| **Contenido**  | Nombres de variables, referencias y marcos de llamadas a funciones. | Objetos reales (`PyObject`), instancias, listas, diccionarios. |
| **Acceso**     | Ultra rápido, gestión LIFO (*Last In, First Out*).                  | Dinámico, gestionado por el Garbage Collector.                 |
| **Tamaño**     | Limitado y fijo por el sistema operativo.                           | Escalable según la memoria RAM disponible en el servidor.      |

---

## 📊 3\. El Costo Oculto de la Memoria en Python

En C tradicional, un entero de 64 bits ocupa **8 bytes**. En Python, ese mismo entero ocupa **28 bytes** debido al overhead de metadatos de la estructura `PyObject`.

```
import sys

entero_c = 1000
print("Tamaño de int(1000) en Python:", sys.getsizeof(entero_c), "bytes")
# Salida: 28 bytes

cadena_vacia = ""
print("Tamaño de str vacía en Python:", sys.getsizeof(cadena_vacia), "bytes")
# Salida: 49 bytes

```

&gt; **Impacto en Data Engineering**: Procesar una lista de 10 millones de enteros nativos en Python consume cerca de **280 MB** de RAM solo en punteros y metadatos. Usar estructuras compactas en C (como arreglos de NumPy, DataFrames de Polars o PyArrow) reduce ese consumo a **80 MB** para el mismo volumen.

---

## 🧪 4\. Práctica: Inspección de Referencias e Identidad

En Python existen dos operadores para comparar variables:

* **\==** **(Igualdad de valor)**: Evalúa si dos objetos contienen la misma información.
* **is** **(Igualdad de identidad)**: Evalúa si dos referencias apuntan a la **misma posición de memoria RAM** (`id(a) == id(b)`).

```
import sys

# 1. Dos listas con el mismo contenido
lista_a = [1, 2, 3]
lista_b = [1, 2, 3]

print("¿Tienen el mismo contenido? (==):", lista_a == lista_b)  # True
print("¿Ocupan la misma posición de memoria? (is):", lista_a is lista_b)  # False

# 2. Conteo de referencias
# sys.getrefcount suma 1 temporalmente al pasar la variable como argumento
print("Referencias a lista_a:", sys.getrefcount(lista_a) - 1)  # 1

lista_c = lista_a  # Asignamos una nueva referencia al mismo objeto
print("Referencias tras asignar lista_c:", sys.getrefcount(lista_a) - 1)  # 2

```

---

## ⚠️ 5\. Casos de Borde en Producción: Fugas de Memoria por Ciclos de Referencia

Python utiliza un **Recolector de Basura (Garbage Collector)** basado en dos mecanismos:

1. **Conteo de referencias (Principal)**: Libera la memoria de inmediato en cuanto `ob_refcnt == 0`.
2. **Colector de ciclos (** **gc** **module)**: Detecta y destruye referencias circulares entre objetos que ya no son accesibles desde el Stack.

### Ejemplo de Referencia Circular (Memory Leak Potencial)

```
import gc

class NodoConexion:

    def __init__(self, nombre):
        self.nombre = nombre
        self.siguiente = None

# Crear dos nodos que se apuntan mutuamente
nodo1 = NodoConexion("Pipeline_A")
nodo2 = NodoConexion("Pipeline_B")

nodo1.siguiente = nodo2
nodo2.siguiente = nodo1

# Eliminar las referencias del Stack
del nodo1
del nodo2

# En este punto, los objetos siguen en el Heap porque ob_refcnt == 1 mutuamente.
# El recolector de ciclos debe ejecutarse para liberar esa memoria.
colectados = gc.collect()
print(f"Objetos inalcanzables liberados por el GC: {colectados}")

```

---

## 🏋️‍♂️ Ejercicio Práctico Hands-On: Medición de Eficiencia de Memoria

Crea el archivo `medicion_memoria.py` y compara el impacto en RAM de crear 1.000.000 de registros con una lista nativa vs. un generador o una estructura optimizada:

```
import sys

# 1. Lista nativa cargada completamente en memoria (Eager)
lista_enteros = [i for i in range(1_000_000)]
tamaño_lista_mb = sys.getsizeof(lista_enteros) / (1024 * 1024)
print(f"RAM ocupada por Lista Nativa (1M enteros): {tamaño_lista_mb:.2f} MB")

# 2. Generador perezoso (Lazy)
generador_enteros = (i for i in range(1_000_000))
tamaño_gen_kb = sys.getsizeof(generador_enteros) / 1024
print(f"RAM ocupada por Generador Lazy: {tamaño_gen_kb:.2f} KB")

```

---

## 🧠 Checkpoint de Autoevaluación

1. ¿Cuáles son los tres atributos fundamentales que contiene la estructura `PyObject` en CPython?
2. ¿Por qué el uso del operador `is` es más rápido que el operador `==` al comparar dos objetos grandes?
3. ¿Qué ocurre en la memoria RAM si una colección de Python mantiene referencias a objetos que ya no se utilizan en la lógica del negocio?
4. ¿Cuál es la ventaja de usar un generador perezoso (`tuple`/`generator`) sobre una lista cargada completa en memoria cuando procesamos archivos de varios gigabytes?