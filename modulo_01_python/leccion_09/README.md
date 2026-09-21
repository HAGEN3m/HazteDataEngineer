# 🐍 Lección 09: Manejo de Errores y Excepciones (`try` / `except`)

En un pipeline de producción de Ingeniería de Datos, los datos del mundo real llegan sucios, incompletos o corruptos. Si un script intenta dividir por cero, convertir un texto alfanumérico a número o abrir un archivo que no existe, Python lanza una **Excepción** y detiene el programa inmediatamente.

El **Manejo de Excepciones** nos permite capturar estos errores en tiempo de ejecución de forma controlada, registrar lo sucedido (*logging*) y permitir que el proceso continúe sin colapsar todo el sistema.

---

## 1\. Errores Comunes en Python (Excepciones)

Algunos de los errores más frecuentes con los que te vas a encontrar son:

| Excepción           | ¿Cuándo ocurre?                                               | Ejemplo                     |
| ------------------- | ------------------------------------------------------------- | --------------------------- |
| `ValueError`        | Tipo correcto pero valor inválido para la conversión.         | `int("hola")`               |
| `ZeroDivisionError` | Intento de dividir un número por cero.                        | `100 / 0`                   |
| `KeyError`          | Intento de acceder a una clave inexistente en un diccionario. | `dict_datos["clave_falsa"]` |
| `TypeError`         | Operación entre tipos de datos incompatibles.                 | `"texto" + 10`              |
| `FileNotFoundError` | Intento de abrir un archivo en una ruta donde no existe.      | `open("no_existo.csv")`     |

---

## 2\. La Estructura `try` y `except`

Con el bloque **try**, le decimos a Python: *"Intentá ejecutar este código"*. Si ocurre un error adentro, salta inmediatamente al bloque **except** sin detener la ejecución del programa.

```
monto_raw = "INVALIDO"

try:
    # Intentamos convertir el texto a número decimal
    monto_num = float(monto_raw)
    print(f"Monto convertido: ${monto_num}")
except ValueError:
    # Este bloque solo se ejecuta si ocurre un ValueError
    print(f"⚠️ No se pudo convertir '{monto_raw}' a número. Registro descartado.")

print("🚀 El script continúa ejecutándose con normalidad...")

```

---

## 3\. Capturar Múltiples Excepciones Específicas

Es una **buena práctica de producción** capturar el tipo de error específico en lugar de usar un `except:` genérico (el cual podría ocultar fallos graves del sistema).

```
def calcular_promedio(total_suma, cantidad_elementos):
    try:
        promedio = total_suma / cantidad_elementos
        return round(promedio, 2)
    except ZeroDivisionError:
        print("⚠️ Advertencia: Cantidad de elementos es 0. Evitando división por cero.")
        return 0.0
    except TypeError:
        print("🔴 Error: Los datos de entrada deben ser numéricos.")
        return None

```

---

## 4\. Cláusulas Opcionales: `else` y `finally`

* **else**: Se ejecuta **solo si el bloque** **try** **tuvo éxito** (no ocurrió ninguna excepción).
* **finally**: Se ejecuta **SIEMPRE**, haya habido error o no (muy útil para cerrar conexiones o liberar recursos).

```
try:
    numero = int("150")
except ValueError:
    print("🔴 Falló la conversión.")
else:
    print(f"🟢 Conversión exitosa. El valor es {numero}.")
finally:
    print("🧹 Limpieza finalizada: esta línea se ejecuta siempre.")

```

---

## 🏋️‍♂️ Práctica de la Lección 09

1. Creá el archivo `ej_09_excepciones.py` dentro de la carpeta `practica/`.
2. Escribí un script para **procesar defensivamente una lista de registros sucios**:
  * Definí una lista de registros mixtos: `registros_raw = ["100.5", "200.0", "INVALIDO", "0.0", None, "500.25"]`
  * Definí una función llamada `procesar_registro(valor_str)` que intente:
    1. Convertir `valor_str` a `float`.
    2. Calcular la división de `1000.0 / float(valor_str)`.
    3. Capturar específicamente:
      * `TypeError` (si el valor es `None`).
      * `ValueError` (si el texto no es numérico).
      * `ZeroDivisionError` (si el número es `0.0`).
    4. Si ocurre cualquier error, la función debe imprimir el motivo específico del fallo y devolver `0.0`.
    5. Si sale bien, debe retornar el resultado de la división redondeado a 2 decimales.
  * Recorré la lista `registros_raw` con un bucle `for`, ejecutá la función para cada elemento y acumulá los resultados válidos en una variable `suma_total`.
  * Al finalizar el bucle, imprimí la suma total acumulada.
3. Ejecutá tu script desde la terminal: `python3 practica/ej_09_excepciones.py`