# 🐍 Lección 07: Tuplas (`tuple`) y Conjuntos (`set`)

En esta lección vamos a explorar dos estructuras de datos fundamentales que complementan a las listas y los diccionarios: las **Tuplas** (para datos inmutables que no deben modificarse) y los **Conjuntos** (para eliminar duplicados y hacer búsquedas ultrarrápidas).

---

## 1\. Tuplas (`tuple`): Colecciones Inmutables

Una **Tupla** es similar a una lista (mantiene un orden y se accede por índices), pero tiene una regla de oro: **es inmutable**, lo que significa que **no se puede modificar, agregar ni eliminar elementos** una vez creada. Se definen encerrando los valores entre **paréntesis** **()**.

```
# Definición de una tupla
coordenadas_servidor = (-34.6037, -58.3816)
conexion_db = ("127.0.0.1", 5432, "postgres")

# Acceso por índice (igual que en las listas)
host = conexion_db[0] # "127.0.0.1"
puerto = conexion_db[1] # 5432

```

### ¿Por qué usar Tuplas en Ingeniería de Datos?

* **Seguridad de datos**: Si tenés valores fijos (como credenciales de entorno, esquemas de tablas o configuraciones de red), usar tuplas evita que por error un script modifique esos valores en ejecución.
* **Menor consumo de memoria**: Ocupan menos espacio en RAM y son más rápidas de procesar que las listas.

```
# Si intentás modificar una tupla:
conexion_db[1] = 5433  # 🔴 TypeError: 'tuple' object does not support item assignment

```

---

## 2\. Conjuntos (`set`): Unicidad y Operaciones Rápidas

Un **Conjunto** es una colección de elementos **únicos y no ordenados**. Se definen usando **llaves** **{}** (sin parejas clave-valor) o la función `set()`.

Las dos características clave de un `set` son:

1. **No permite duplicados**: Si agregás el mismo valor 10 veces, solo conservará 1.
2. **Búsquedas instantáneas**: Saber si un elemento existe dentro de un `set` es exponencialmente más rápido que en una lista.

```
# Crear un conjunto con duplicados
ids_raw = [101, 102, 101, 103, 102, 104, 101]

# Eliminar duplicados convirtiendo a set
ids_unicos = set(ids_raw)
print(ids_unicos) # {101, 102, 103, 104}

```

### Operaciones Útiles entre Conjuntos

En producción se usan constantemente para comparar listas de datos (ej: saber qué IDs llegaron en un archivo pero no están en la base de datos):

```
clientes_ayer = {"C-10", "C-20", "C-30"}
clientes_hoy = {"C-20", "C-30", "C-40"}

# 1. Intersección (&): Elementos presentes en AMBOS conjuntos
clientes_reincidentes = clientes_ayer & clientes_hoy # {"C-20", "C-30"}

# 2. Diferencia (-): Elementos que están en el primero pero NO en el segundo
clientes_nuevos = clientes_hoy - clientes_ayer # {"C-40"}

# 3. Unión (|): Todos los elementos sin repetir
total_clientes = clientes_ayer | clientes_hoy # {"C-10", "C-20", "C-30", "C-40"}

```

---

## 🏋️‍♂️ Práctica de la Lección 07

1. Creá el archivo `ej_07_tuplas_sets.py` dentro de la carpeta `leccion_07/`.
2. Escribí un script para **depurar e inspeccionar un lote de transacciones**:
  * Definí una tupla inmutable llamada `CONFIG_ESQUEMA` con los nombres de las columnas obligatorias: `("id_transaccion", "cliente_id", "monto", "fecha")`.
  * Definí una lista con IDs de clientes que llegaron en un reporte de eventos sucios: `ids_reporte = ["C-01", "C-02", "C-01", "C-03", "C-02", "C-04", "C-01"]`
  * Convertí `ids_reporte` a un conjunto (`set`) llamado `ids_unicos` para eliminar los IDs duplicados.
  * Definí otro conjunto llamado `ids_base_datos = {"C-01", "C-02", "C-05"}`.
  * Calculá e imprimí con f-strings:
    * Cantidad original de registros vs. cantidad de registros únicos.
    * Cuáles clientes del reporte son completamente **nuevos** (están en `ids_unicos` pero NO en `ids_base_datos`).
    * Cuáles clientes están presentes en **ambas fuentes** (intersección).
3. Ejecutá tu script en la terminal: `python3 leccion_07/ej_07_tuplas_sets.py`