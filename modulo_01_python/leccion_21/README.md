# 🐍 Lección 21: Decoradores (`@decorador`), Funciones de Orden Superior y Medición de Tiempos

¡Damos inicio al **Bloque 3: Python Avanzado y Entornos de Desarrollo**!

En la Ingeniería de Datos de producción, es muy común querer agregar funcionalidades transversales a nuestras funciones sin modificar su código interno. Por ejemplo: **medir cuánto tarda en ejecutarse un pipeline**, **reintentar una conexión si falla**, **auditar entradas y salidas** o **validar credenciales**.

Para lograr esto de forma limpia y reutilizable en Python, usamos **Funciones de Orden Superior** y **Decoradores** (representados con el símbolo `@`).

---

## 1\. Funciones de Orden Superior

En Python, las funciones son objetos de "primer orden" (*first-class citizens*). Esto significa que podés:

1. Guardar una función dentro de una variable.
2. Pasar una función como argumento dentro de otra función.
3. Retornar una función desde dentro de otra función.

```
def aplicar_transformacion(lista_datos: list, funcion_transformadora) -&gt; list:
    """Recibe una función como argumento y la aplica a cada elemento."""
    return [funcion_transformadora(x) for x in lista_datos]

def duplicar(valor: float) -&gt; float:
    return valor * 2

numeros = [10.0, 20.0, 30.0]
# Pasamos la función 'duplicar' como argumento
resultado = aplicar_transformacion(numeros, duplicar)
print(resultado) # [20.0, 40.0, 60.0]

```

---

## 2\. Anotomía de un Decorador (`@decorador`)

Un **Decorador** es simplemente una función que recibe como entrada otra función, le agrega una capa de funcionalidad antes y/o después de su ejecución, y devuelve una nueva función envuelta.

Para preservar el nombre y la documentación original de la función decorada, es una **regla de oro** utilizar el decorador **@functools.wraps**.

```
import time
from functools import wraps

def medir_tiempo_ejecucion(func):
    """Decorador que mide e imprime el tiempo de ejecución de cualquier función."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        inicio = time.time()
        print(f"⏱️ Iniciando ejecución de '{func.__name__}'...")
        
        # Ejecutamos la función original
        resultado = func(*args, **kwargs)
        
        fin = time.time()
        duracion = fin - inicio
        print(f"✅ '{func.__name__}' finalizó en {duracion:.4f} segundos.")
        return resultado
        
    return wrapper

```

---

## 3\. Aplicar el Decorador con la Sintaxis `@`

Al colocar `@medir_tiempo_ejecucion` justo arriba de la definición de una función, Python envuelve automáticamente esa función:

```
@medir_tiempo_ejecucion
def procesar_lote_pesado(cantidad_registros: int) -&gt; list:
    """Simula un procesamiento intensivo de datos."""
    time.sleep(1.5) # Simula una demora de 1.5 segundos
    return [{"id": i} for i in range(cantidad_registros)]

# Al llamar a la función, el decorador se ejecuta automáticamente
lote = procesar_lote_pesado(1000)

```

**Salida en pantalla:**

```
⏱️ Iniciando ejecución de 'procesar_lote_pesado'...
✅ 'procesar_lote_pesado' finalizó en 1.5021 segundos.

```

---

## 4\. Decorador con Parámetros (Ejemplo: Reintentos de API)

También podés crear decoradores que acepten parámetros (como la cantidad de reintentos permitidos):

```
import time
from functools import wraps

def reintentar(max_intentos: int = 3, espera_segundos: float = 1.0):
    """Decorador que reintenta ejecutar una función si lanza una excepción."""
    def decorador(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            intentos = 0
            while intentos &lt; max_intentos:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    intentos += 1
                    print(f"⚠️ Intento {intentos}/{max_intentos} falló en '{func.__name__}': {e}")
                    if intentos &lt; max_intentos:
                        time.sleep(espera_segundos)
            raise ConnectionError(f"🔴 '{func.__name__}' falló tras {max_intentos} intentos.")
        return wrapper
    return decorador

```

---

## 🏋️‍♂️ Práctica de la Lección 21

1. Creá el archivo `ej_21_decoradores.py` dentro de la carpeta `practica/`.
2. Escribí un script para **auditar e inspeccionar la ejecución de transformaciones**:
  * Importá `time`, `logging` y `wraps` desde `functools`.
  * Configurá `logging.basicConfig(level=logging.INFO)`.
  * Creá el decorador `auditar_transaccion(func)`:
    * Debe registrar con `logging.info` los argumentos (`*args`, `**kwargs`) recibidos por la función antes de ejecutarla.
    * Debe medir el tiempo de ejecución.
    * Debe capturar el valor retornado por la función e informar con `logging.info` que la función terminó con éxito mostrando el tiempo de ejecución.
    * Debe retornar el resultado de la función intacto.
  * Creá la función `transformar_monto_moneda(monto: float, tasa_cambio: float = 1200.0) -&gt; float` decorada con `@auditar_transaccion`:
    * Simulá una demora de `0.5` segundos usando `time.sleep(0.5)`.
    * Retorná `monto * tasa_cambio`.
3. En el bloque `if __name__ == "__main__":`:
  * Ejecutá la función pasando un monto de `150.0` y observá cómo el decorador imprime automáticamente los logs de auditoría sin haber ensuciado el código de la función.
4. Ejecutá tu script desde la terminal: `python3 practica/ej_21_decoradores.py`