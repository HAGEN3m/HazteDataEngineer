# 🐍 Lección 04: Colecciones de Datos con Listas (`list`)

Hasta ahora guardábamos un solo valor por variable (por ejemplo, `edad = 25`). En la **Ingeniería de Datos**, casi siempre trabajamos con colecciones de múltiples valores juntos: filas de una tabla, registros de transacciones o rutas de archivos a procesar.

Una **Lista** es una estructura de datos que permite guardar **múltiples elementos en orden** dentro de una misma variable, encerrados entre **corchetes** **[]** y separados por comas.

---

## 1\. Crear una Lista

```
# Lista de textos (strings)
paises = ["Argentina", "Chile", "Uruguay"]

# Lista de números
montos_usd = [1500.50, 2300.00, 4500.25, 1200.00]

# Lista vacía (muy común para ir llenándola después)
archivos_procesados = []

```

---

## 2\. Acceder a Elementos por Índice

Cada elemento dentro de una lista ocupa una **posición numerada (índice)** que comienza **siempre desde el número 0**:

```
clientes = ["Juan", "María", "Pedro", "Ana"]

# Posiciones:    0        1        2       3

print(clientes[0]) # "Juan"  (El primer elemento)
print(clientes[2]) # "Pedro" (El tercer elemento)

```

### Índices Negativos (Contar desde el final)

Podés usar números negativos para acceder de atrás hacia adelante sin necesidad de saber el largo de la lista:

```
print(clientes[-1]) # "Ana"   (El último elemento)
print(clientes[-2]) # "Pedro" (El anteúltimo elemento)

```

---

## 3\. Modificar y Trabajar con Listas

### Saber la cantidad de elementos (`len()`)

La función `len()` devuelve la cantidad total de elementos dentro de la lista:

```
total_clientes = len(clientes) # 4

```

### Agregar un elemento al final (`.append()`)

```
clientes.append("Lucas")
print(clientes) # ["Juan", "María", "Pedro", "Ana", "Lucas"]

```

### Modificar un elemento existente

```
clientes[1] = "María Laura" # Reemplaza el elemento en el índice 1

```

### Eliminar un elemento (`.remove()` o `del`)

```
clientes.remove("Pedro") # Busca y elimina el valor "Pedro"

```

---

## 🏋️‍♂️ Práctica de la Lección 04

1. Creá el archivo `ej_04_listas.py` dentro de la carpeta `practica/`.
2. Escribí un script que simule una **cola de archivos pendientes de ingesta**:
  * Definí una lista llamada `archivos_pendientes` con tres elementos: `"ventas_jan.csv"`, `"ventas_feb.csv"`, `"ventas_mar.csv"`.
  * Imprimí en la consola cuántos archivos hay cargados usando `len()` y una f-string: `"Archivos pendientes en cola: 3"`
  * Agregá un nuevo archivo al final de la lista usando `.append()`: `"ventas_apr.csv"`.
  * Corregí el nombre del primer archivo (`"ventas_jan.csv"`) reemplazándolo en el índice `0` por `"ventas_jan_corregido.csv"`.
  * Muestra en pantalla cuál es el primer archivo a procesar y cuál es el último de la cola usando índices (`[0]` y `[-1]`).
3. Ejecutá tu script en la terminal: `python3 practica/ej_04_listas.py`