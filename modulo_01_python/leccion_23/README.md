# 🐍 Lección 23: Comprensiones Avanzadas de Listas, Diccionarios y Conjuntos (Comprehensions)

En la Ingeniería de Datos, la limpieza, transformación y filtrado de colecciones son tareas cotidianas. En Python, las **Comprensiones** (*Comprehensions*) permiten escribir estas transformaciones en una sola línea de código concisa, elegante y altamente eficiente (*Pythonic*).

Además de ser más legibles, las comprensiones están optimizadas internamente a nivel de C, por lo que suelen ejecutarse significativamente más rápido que un bucle `for` convencional con `.append()`.

---

## 1\. List Comprehensions (Comprensión de Listas)

Sintaxis básica: `[expresion for elemento in iterable if condicion]`

### A. Filtrar y transformar elementos

```
# 🔴 ENFOQUE TRADICIONAL CON BUCLE FOR
montos_raw = [100.0, -50.0, 200.0, 0.0, 350.5]
montos_validos = []
for m in montos_raw:
    if m &gt; 0:
        montos_validos.append(m * 1.21)

# 🟢 ENFOQUE PYTHONIC CON LIST COMPREHENSION
montos_validos = [m * 1.21 for m in montos_raw if m &gt; 0]

```

### B. Uso de `if-else` en la Expresión (Operador Ternario)

Si querés transformar el elemento según una condición (en lugar de filtrarlo), la estructura `if-else` se ubica **antes** del `for`:

```
estados = ["COMPLETADA", "ERROR", "COMPLETADA", "PENDIENTE"]

# Asigna 'ACTIVO' o 'INACTIVO' según el estado
flag_estados = ["ACTIVO" if e == "COMPLETADA" else "INACTIVO" for e in estados]

```

---

## 2\. Dict Comprehensions (Comprensión de Diccionarios)

Sintaxis básica: `{clave_exp: valor_exp for elemento in iterable if condicion}`

Se utiliza muchísimo en Data Engineering para crear índices en memoria, remapear esquemas o filtrar configuraciones:

```
clientes = [
    {"id": "C-101", "nombre": "Juan", "pais": "AR"},
    {"id": "C-102", "nombre": "María", "pais": "CL"},
    {"id": "C-103", "nombre": "Pedro", "pais": "AR"}
]

# Crear un mapa rápido de ID -&gt; Nombre solo para clientes de Argentina
mapa_clientes_ar = {c["id"]: c["nombre"] for c in clientes if c["pais"] == "AR"}
print(mapa_clientes_ar) # {'C-101': 'Juan', 'C-103': 'Pedro'}

```

### Invertir claves y valores de un diccionario

```
codigos_pais = {"AR": "Argentina", "CL": "Chile", "MX": "México"}
pais_a_codigo = {nombre: codigo for codigo, nombre in codigos_pais.items()}

```

---

## 3\. Set Comprehensions (Comprensión de Conjuntos)

Sintaxis básica: `{expresion for elemento in iterable if condicion}`

Es idéntica a la de diccionarios pero sin parejas `clave: valor`. Es perfecta para extraer listas de categorías, nombres de columnas o dominios únicos limpios:

```
emails_raw = ["juan@gmail.com", "MARIA@HOTMAIL.COM", "pedro@gmail.com", "  juan@gmail.com  "]

# Normaliza a minúsculas, quita espacios y elimina duplicados automáticamente
dominios_unicos = {email.strip().lower().split("@")[1] for email in emails_raw}
print(dominios_unicos) # {'gmail.com', 'hotmail.com'}

```

---

## 4\. Cuándo NO usar Comprensiones (Regla de Legibilidad)

Aunque las comprensiones son muy potentes, **nunca se debe sacrificar la legibilidad del código**.

* **SÍ usar**: Para transformaciones o filtrados simples de una sola línea.
* **NO usar**: Cuando requiera bucles anidados complejos, múltiples `if/else` cruzados o bloques de prueba con `try/except`. En esos casos, es preferible usar un bucle `for` tradicional bien documentado.

---

## 🏋️‍♂️ Práctica de la Lección 23

1. Creá el archivo `ej_23_comprehensions.py` dentro de la carpeta `practica/`.
2. Escribí un script para **sanear y catalogar un dataset heterogéneo de ventas**:
  * Dado el dataset raw:

```
ventas_raw = [
    {"transaccion_id": "T-01", "monto": "$1,500.50", "categoria": "  Electrónica  "},
    {"transaccion_id": "T-02", "monto": "$0.00", "categoria": "Hogar"},
    {"transaccion_id": "T-03", "monto": "$2,300.00", "categoria": "electrónica"},
    {"transaccion_id": "T-04", "monto": "INVALIDO", "categoria": "  Moda  "}
]

```

1. **Consigna 1 (List Comprehension)**: Creá una lista con los IDs de las transacciones cuya categoría sea `"electrónica"` (sin importar mayúsculas/minúsculas ni espacios extra).
2. **Consigna 2 (Dict Comprehension)**: Creá un diccionario donde la clave sea el `transaccion_id` y el valor sea el monto convertido a `float` (eliminando `$` y `,`), incluyendo solo aquellas transacciones cuyo monto sea numérico y mayor a 0.
3. **Consigna 3 (Set Comprehension)**: Extraé un conjunto (`set`) con todas las categorías únicas normalizadas en mayúsculas y sin espacios.
4. Ejecutá tu script en la terminal: `python3 practica/ej_23_comprehensions.py`