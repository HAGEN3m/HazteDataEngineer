# 🐍 Lección 02: Operaciones Matemáticas, F-Strings y Conversión de Tipos

En esta lección vamos a aprender a hacer cálculos numéricos, formatear texto de manera profesional y convertir un tipo de dato en otro (por ejemplo, transformar un texto `"100"` en el número `100`).

---

## 1\. Operadores Matemáticos Básicos

En Python podemos realizar operaciones matemáticas directas usando los siguientes símbolos:

```
suma = 10 + 5          # 15
resta = 20 - 8         # 12
multiplicacion = 4 * 5  # 20
division = 10 / 4      # 2.5 (La división siempre devuelve un float)
division_entera = 10 // 4 # 2 (Descarta los decimales)
modulo_resto = 10 % 3  # 1 (Es el resto de la división)
potencia = 2 ** 3      # 8 (2 elevado a la 3)

```

---

## 2\. Formateo de Texto Moderno: F-Strings

Para combinar variables dentro de un texto sin usar el signo `+` (que suele dar errores de tipo), usamos las **f-strings** (cadenas formateadas). Se escriben agregando una letra `f` antes de las comillas y encerrando las variables entre llaves `{}`:

```
nombre = "Tomás"
edad = 25

# Forma moderna y limpia (f-string)
mensaje = f"Hola, me llamo {nombre} y tengo {edad} años."
print(mensaje)

```

---

## 3\. Conversión de Tipos de Datos (Type Casting)

Muchas veces los datos entran a nuestros sistemas como texto (strings), pero necesitamos hacer cálculos numéricos con ellos. Para cambiar el tipo de dato usás las funciones de conversión:

* **int()**: Convierte a número entero.
* **float()**: Convierte a número decimal.
* **str()**: Convierte cualquier valor a texto.

```
precio_texto = "1500" # Tipo str
descuento = 200        # Tipo int

# Si intentás hacer "1500" - 200, Python da ERROR.
# Debemos convertir el texto a entero primero:
precio_numero = int(precio_texto)
total = precio_numero - descuento

print(f"El precio final es: ${total}") # Salida: El precio final es: $1300

```

---

## 🏋️‍♂️ Práctica de la Lección 02

1. Creá el archivo `ej_02_operaciones.py` dentro de la carpeta `practica/`.
2. Escribí un script que simule el cálculo del sueldo neto de un desarrollador:
  * Definí la variable `sueldo_bruto_str = "3500.50"` (como string).
  * Definí la variable `porcentaje_impuesto = 15` (como número entero).
  * Convierte `sueldo_bruto_str` a número decimal (`float`).
  * Calculá el monto descontado por impuestos y el sueldo neto final.
  * Muestra en pantalla el resultado formateado con un f-string: `"Sueldo Bruto: $3500.50 | Descuento (15%): $525.075 | Sueldo Neto: $2975.425"`
3. Ejecutá tu script desde la terminal: `python3 practica/ej_02_operaciones.py`