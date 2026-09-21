# 🐍 Lección 05: Repetir Tareas con Bucles (`for` y `while`)

En la **Ingeniería de Datos**, rara vez procesamos un solo dato a la vez. Lo habitual es procesar miles o millones de registros: leer fila por fila una tabla, recorrer una lista de archivos CSV o reintentar una conexión a una base de datos.

Para evitar repetir código manualmente, usamos **bucles (loops)**, que nos permiten ejecutar un bloque de código múltiples veces de forma automática.

---

## 1\. El Bucle `for` (Iterar sobre colecciones)

El bucle `for` se usa cuando **sabemos de antemano cuántas veces queremos repetir una acción** o cuando queremos **recorrer cada elemento de una lista**.

### Recorrer una lista elemento por elemento

```
archivos = ["ventas_ene.csv", "ventas_feb.csv", "ventas_mar.csv"]

for archivo in archivos:
    print(f"🔄 Procesando archivo: {archivo}")

```

**Salida en consola:**

```
🔄 Procesando archivo: ventas_ene.csv
🔄 Procesando archivo: ventas_feb.csv
🔄 Procesando archivo: ventas_mar.csv

```

### Repetir un número exacto de veces (`range()`)

La función `range(n)` genera una secuencia de números desde `0` hasta `n-1`:

```
# Se ejecuta 3 veces (i toma los valores 0, 1, 2)
for i in range(3):
    print(f"Ejecutando intento número {i + 1}")

```

---

## 2\. El Bucle `while` (Repetir mientras se cumpla una condición)

El bucle `while` se ejecuta **mientras una condición booleana sea verdadera (** **True** **)**. Se usa principalmente cuando **no sabemos exactamente cuántas iteraciones tomará** una tarea (por ejemplo, esperar a que un servidor responda).

```
intentos = 0
max_intentos = 3

while intentos &lt; max_intentos:
    intentos += 1
    print(f"📡 Conectando a la base de datos... (Intento {intentos})")

print("⚡ Proceso de conexión finalizado.")

```

&gt; ⚠️ **Cuidado con los bucles infinitos**: Si la condición del `while` nunca pasa a `False`, el programa se quedará colgado para siempre. Asegurate siempre de actualizar la variable de control dentro del bucle.

---

## 3\. Control de Bucles (`break` y `continue`)

* **break**: Interrumpe y sale del bucle inmediatamente.
* **continue**: Saltea el resto de la iteración actual y pasa directamente a la siguiente.

```
registros = [100, -50, 200, None, 300]

for monto in registros:
    if monto is None:
        print("⚠️ Registro nulo detectado. Salteando...")
        continue # Saltea el None y sigue con el próximo
    if monto &lt; 0:
        print(f"🔴 Error crítico: Monto negativo ({monto}). Deteniendo proceso.")
        break # Detiene el bucle por completo
    print(f"🟢 Monto procesado: ${monto}")

```

---

## 🏋️‍♂️ Práctica de la Lección 05

1. Creá el archivo `ej_05_bucles.py` dentro de la carpeta `practica/`.
2. Escribí un script que simule el **procesamiento y acumulación de un lote de transacciones**:
  * Definí una lista de montos: `transacciones = [150.0, 200.5, -20.0, 310.0, 0.0, 500.0]`.
  * Definí dos variables acumuladoras en `0`: `monto_total_valido = 0.0` y `cantidad_invalidas = 0`.
  * Usá un bucle `for` para recorrer la lista de transacciones:
    * Si el monto es menor o igual a `0`, incrementá `cantidad_invalidas` en `1`, mostrá un aviso con `print()` y usá `continue` para no sumarlo.
    * Si el monto es positivo, sumalo a `monto_total_valido` e imprimí un mensaje confirmando el procesamiento del monto.
  * Al finalizar el bucle, mostrá un resumen en pantalla usando un f-string: `"Procesamiento finalizado | Total acumulado: $960.5 | Transacciones descartadas: 2"`
3. Ejecutá tu script en la terminal: `python3 practica/ej_05_bucles.py`