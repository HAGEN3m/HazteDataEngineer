# 🐍 Lección 08: Reutilización de Código con Funciones (`def`)

En las lecciones anteriores escribimos scripts que ejecutaban instrucciones de forma secuencial. Sin embargo, a medida que los pipelines crecen, escribir el mismo bloque de código una y otra vez genera redundancia y facilita la aparición de errores.

Una **Función** es un bloque de código reutilizable al que le asignamos un nombre. Sigue el principio **DRY** (*Don't Repeat Yourself* \- No te repitas) y nos permite encapsular una lógica específica para ejecutarla cada vez que la necesitemos.

---

## 1\. Estructura Básica de una Función (`def`)

Para definir una función en Python usamos la palabra clave **def**, seguida del nombre de la función, paréntesis `()` y dos puntos `:`. El cuerpo de la función debe ir indentado (4 espacios).

```
# Definición de la función
def saludar_usuario():
    print("👋 ¡Bienvenido al pipeline de datos!")

# Llamada o ejecución de la función
saludar_usuario()

```

---

## 2\. Parámetros y Argumentos (Entradas)

Las funciones pueden recibir datos de entrada llamados **parámetros** para trabajar con ellos:

```
def calcular_impuesto(monto, porcentaje):
    monto_impuesto = monto * (porcentaje / 100)
    print(f"Impuesto calculado ({porcentaje}%): ${monto_impuesto}")

# Llamamos a la función pasando argumentos reales
calcular_impuesto(1000, 21) # Impuesto calculado (21%): $210.0
calcular_impuesto(500, 10)  # Impuesto calculado (10%): $50.0

```

---

## 3\. Devuelvo de Valores con `return` (Salidas)

La mayoría de las veces no queremos que la función solo imprima en pantalla, sino que **devuelva un resultado** para seguir usándolo en otras partes del programa. Para esto usamos la instrucción **return**.

&gt; 💡 **Nota**: Cuando Python llega a una línea con `return`, la función termina inmediatamente y devuelve ese valor.

```
def convertir_usd_a_ars(monto_usd, cotizacion):
    return monto_usd * cotizacion

# Guardamos el resultado devuelto en una variable
total_pesos = convertir_usd_a_ars(100, 1250.0)
print(f"Monto total en ARS: ${total_pesos}") # Monto total en ARS: $125000.0

```

---

## 4\. Parámetros por Defecto (Valores Opcionales)

Podés asignar valores predeterminados a los parámetros. Si al llamar a la función no envías ese argumento, Python usará el valor por defecto:

```
def normalizar_texto(texto, convertir_mayusculas=False):
    texto_limpio = texto.strip() # Quita espacios extra al inicio y al final
    if convertir_mayusculas:
        return texto_limpio.upper()
    return texto_limpio.lower()

print(normalizar_texto("  VENTAS_2026.CSV  "))                     # "ventas_2026.csv"
print(normalizar_texto("  ventas_2026.csv  ", convertir_mayusculas=True)) # "VENTAS_2026.CSV"

```

---

## 🏋️‍♂️ Práctica de la Lección 08

1. Creá el archivo `ej_08_funciones.py` dentro de la carpeta `leccion_08/`.
2. Escribí un script para **limpiar y validar registros de montos**:
  * Definí una función llamada `validar_y_convertir_monto(monto_raw, tasa_cambio=1.0)`:
    * El parámetro `monto_raw` puede recibir un número (`int`/`float`) o un texto (ej: `"1500.50"`).
    * Convertí `monto_raw` a `float`.
    * Si el monto resulta ser menor o igual a `0`, la función debe retornar `None`.
    * Si es mayor a `0`, debe multiplicar el monto por `tasa_cambio` y retornar el valor redondeado a 2 decimales usando `round(resultado, 2)`.
  * Fuera de la función, probá procesar esta lista usando un bucle `for`: `lote_raw = ["100.50", -50.0, "200.00", 0.0, "350.25"]`
  * Para cada elemento, llamá a la función pasando una `tasa_cambio=1200.0`.
  * Si el resultado devuelto no es `None`, imprimí: `"🟢 Monto convertido a moneda local: $..."`
  * Si es `None`, imprimí: `"🔴 Registro inválido descartado."`
3. Ejecutá tu script en la terminal: `python3 leccion_08/ej_08_funciones.py`