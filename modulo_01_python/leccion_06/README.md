# 🐍 Lección 06: Estructuras de Datos - Diccionarios (`dict`)

En la **Ingeniería de Datos**, los diccionarios son una de las estructuras más utilizadas. Se usan constantemente para representar filas de tablas, registros JSON provenientes de APIs, configuraciones de pipelines y metadatos.

A diferencia de las listas (que ordenan elementos por índices numéricos `0, 1, 2...`), un **Diccionario** almacena datos en parejas de **Clave: Valor** (*Key: Value*), delimitados por **llaves** **{}**.

---

## 1\. Crear y Acceder a un Diccionario

Las claves suelen ser cadenas de texto (`str`) que describen qué información guarda ese campo:

```
# Diccionario que representa un registro de transacción
transaccion = {
    "id": 1001,
    "cliente": "María Pérez",
    "monto_usd": 250.75,
    "estado": "COMPLETADA"
}

# Acceder a un valor usando su clave entre corchetes
print(transaccion["cliente"])     # "María Pérez"
print(transaccion["monto_usd"])   # 250.75

```

---

## 2\. Acceso Seguro con `.get()` (Evitar que el código se rompa)

Si intentás acceder a una clave que **no existe** usando corchetes (ejemplo: `transaccion["fecha"]`), Python lanzará un error de tipo `KeyError` y detendrá la ejecución del programa.

Para evitar esto en código de producción, usamos el método **.get()**, el cual devuelve `None` (o un valor por defecto) si la clave no existe:

```
# Si la clave 'fecha' no existe, devuelve None en lugar de romper el programa
fecha = transaccion.get("fecha") # None

# También podés definir un valor por defecto
fecha_default = transaccion.get("fecha", "2026-01-01") # "2026-01-01"

```

---

## 3\. Modificar, Agregar y Eliminar Campos

```
# Modificar un valor existente
transaccion["estado"] = "PROCESADA"

# Agregar una nueva clave-valor
transaccion["moneda"] = "USD"

# Eliminar una clave
del transaccion["cliente"]

```

---

## 4\. Recorrer un Diccionario (`.items()`)

Para iterar sobre las claves y los valores al mismo tiempo dentro de un bucle `for`, usamos el método `.items()`:

```
for clave, valor in transaccion.items():
    print(f"Campo: {clave} -> Valor: {valor}")

```

---

## 5\. Listas de Diccionarios (Representación de Datasets)

En pipelines reales, un conjunto de datos suele representarse como una **lista llena de diccionarios**:

```
ventas = [
    {"id": 1, "monto": 100.0, "estado": "COMPLETADA"},
    {"id": 2, "monto": -50.0, "estado": "ERROR"},
    {"id": 3, "monto": 300.0, "estado": "COMPLETADA"}
]

for venta in ventas:
    if venta["estado"] == "COMPLETADA":
        print(f"🟢 Venta #{venta['id']} aprobada por ${venta['monto']}")

```

---

## 🏋️‍♂️ Práctica de la Lección 06

1. Creá el archivo `ej_06_diccionarios.py` dentro de la carpeta `leccion_06/`.
2. Escribí un script que procese la configuración de conexión a una base de datos:
  * Definí el diccionario `config_db`:

```
config_db = {
    "host": "localhost",
    "puerto": 5432,
    "usuario": "admin_data",
    "base_datos": "dw_ventas"
}

```

1. Agregá una nueva clave `"ssl"` con el valor booleano `True`.
2. Intentá leer la clave `"password"` usando `.get()` pasando como valor por defecto `"SIN_PASSWORD"`.
3. Recorré el diccionario con un bucle `for` y `.items()`, imprimiendo en pantalla cada parámetro formateado: `"Parámetro: host | Valor: localhost"` `"Parámetro: puerto | Valor: 5432"` ... etc.
4. Usá un condicional `if` para verificar si el puerto es `5432`. Si lo es, imprimí: `"⚡ Conexión configurada para PostgreSQL en puerto estándar."`
5. Ejecutá tu script desde la terminal: `python3 leccion_06/ej_06_diccionarios.py`