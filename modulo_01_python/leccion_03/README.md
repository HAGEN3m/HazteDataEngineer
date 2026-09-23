# 🐍 Lección 03: Control de Flujo con Condicionales (`if`, `elif`, `else`)

Hasta ahora nuestros scripts ejecutaban las instrucciones de arriba a abajo en una sola línea recta. En esta lección aprenderemos a **tomar decisiones**: ejecutar ciertos bloques de código solo cuando se cumpla una condición específica (fundamental para validar si un dato es correcto antes de procesarlo).

---

## 1\. Operadores de Comparación

Para evaluar condiciones usamos operadores que comparan dos valores y siempre devuelven un valor booleano (`True` o `False`):

| Operador | Significado       | Ejemplo      | Resultado |
| -------- | ----------------- | ------------ | --------- |
| `==`     | Igual a           | `10 == 10`   | `True`    |
| `!=`     | Distinto de       | `"A" != "B"` | `True`    |
| `>`      | Mayor que         | `15 > 20`    | `False`   |
| `<`      | Menor que         | `5 < 10`     | `True`    |
| `>=`     | Mayor o igual que | `10 >= 10`   | `True`    |
| `<=`     | Menor o igual que | `8 <= 3`     | `False`   |

---

## 2\. Operadores Lógicos (`and`, `or`, `not`)

Nos permiten combinar múltiples condiciones en una sola expresión:

* **and**: Devuelve `True` **solo si ambas condiciones son verdaderas**.
* **or**: Devuelve `True` **si al menos una de las condiciones es verdadera**.
* **not**: Invierte el valor (transforma `True` en `False` y viceversa).

```
monto = 1500
estado = "COMPLETADA"

# Ambas condiciones deben cumplirse
es_valido = (monto > 0) and (estado == "COMPLETADA") # True

```

---

## 3\. La Estructura `if`, `elif` y `else`

En Python, la **sangría / indentación** (4 espacios hacia la derecha) es obligatoria: le indica a Python qué líneas están "adentro" de cada condición.

```
monto_transaccion = -50.0

if monto_transaccion > 0:
    print("🟢 Transacción válida. Registrando pago...")
elif monto_transaccion == 0:
    print("🟡 Advertencia: El monto registrado es $0.00.")
else:
    print("🔴 ERROR: El monto no puede ser negativo. Registro descartado.")

```

---

## 🏋️‍♂️ Práctica de la Lección 03

1. Creá el archivo `ej_03_condicionales.py` dentro de la carpeta `leccion_03/`.
2. Escribí un script de **validación de ingesta de datos**:
  * Definí la variable `cliente_activo = True` (booleano).
  * Definí la variable `monto_compra = 2500.0` (float).
  * Definí la variable `codigo_pais = "AR"` (string).
  * **Reglas de Negocio a evaluar**:
    * Si el cliente NO está activo (`cliente_activo == False`), imprimir: `"🔴 Cliente inactivado. Transacción rechazada."`
    * Si el cliente está activo, pero el monto es menor o igual a 0, imprimir: `"🔴 Monto inválido."`
    * Si el cliente está activo y el monto es mayor a 0:
      * Si el `codigo_pais` es `"AR"` o `"CL"`, aplicar un recargo del 10% e imprimir el total a cobrar usando una f-string.
      * Si es de cualquier otro país, no aplicar recargo e imprimir el total sin cambios.
3. Ejecutá tu script en la terminal: `python3 leccion_03/ej_03_condicionales.py`