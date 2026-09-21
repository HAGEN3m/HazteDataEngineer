# 🐍 Lección 13: Módulos, Paquetes e Importación (`import`, `from ... import ...`)

En las lecciones anteriores vimos cómo escribir funciones para no repetir código. Sin embargo, tener todo el código dentro de un único archivo gigante de mil líneas es inviable en proyectos reales.

En esta lección aprenderemos a **modularizar**: separar nuestro código en múltiples archivos y carpetas interconectados usando **Módulos** y **Paquetes**, el estándar indiscutido para estructurar pipelines de Ingeniería de Datos.

---

## 1\. Conceptos Fundamentales: Módulo vs. Paquete

* **Módulo**: Es simplemente un archivo `.py` que contiene funciones, variables o clases reutilizables.
* **Paquete**: Es una carpeta que agrupa varios módulos relacionados entre sí. Tradicionalmente incluye un archivo especial llamado `__init__.py` (que le indica a Python que la carpeta debe ser tratada como un paquete).

---

## 2\. La Librería Estándar de Python

Python viene "con baterías incluidas": incluye docenas de módulos nativos listos para usar sin instalar nada extra.

### Módulos nativos más usados en Data Engineering:

* **os** **/** **sys**: Interacción con el sistema operativo y argumentos de consola.
* **datetime**: Manipulación de fechas, timestamps y zonas horarias.
* **math**: Operaciones matemáticas avanzadas.
* **random**: Generación de datos aleatorios o muestras (*sampling*).
* **json**: Procesamiento de archivos y respuestas de APIs JSON.

---

## 3\. Formas de Importar en Python

Existen tres formas principales de importar código:

### A. Importar el módulo completo

```
import math

resultado = math.sqrt(16) # Se accede usando el prefijo 'math.'

```

### B. Importar funciones o clases específicas

```
from datetime import datetime, timedelta

ahora = datetime.now()
ayer = ahora - timedelta(days=1)

```

### C. Usar Alias con `as` (Muy común en librerías de datos)

```
import os as sistema_op

ruta = sistema_op.getcwd()

```

---

## 4\. Crear e Importar tus Propios Módulos

Imaginá la siguiente estructura en tu proyecto:

```
mi_pipeline/
├── src/
│   ├── __init__.py
│   └── formateador.py
└── main.py

```

Si el archivo `src/formateador.py` tiene la función:

```
# src/formateador.py
def limpiar_texto(texto: str) -&gt; str:
    return texto.strip().lower()

```

Podés importarla y usarla desde `main.py` de la siguiente manera:

```
# main.py
from src.formateador import limpiar_texto

texto_sucio = "  VENTAS_2026.CSV  "
print(limpiar_texto(texto_sucio)) # "ventas_2026.csv"

```

---

## 5\. El Guardián de Ejecución: `if __name__ == "__main__":`

Cuando importás un módulo, Python ejecuta todo el código que esté en la raíz de ese archivo. Para evitar que se ejecuten pruebas o scripts secundarios al importar un módulo, usamos el bloque **if \_\_name\_\_ == "\_\_main\_\_":**.

```
def procesar_datos():
    print("⚙️ Procesando datos...")

# Todo lo que esté adentro de este 'if' SOLO se ejecuta si corrés este archivo directamente
# Si otro archivo importa este script, estas líneas NO se ejecutan.
if __name__ == "__main__":
    print("🚀 Ejecutando script de prueba local...")
    procesar_datos()

```

---

## 🏋️‍♂️ Práctica de la Lección 13

1. Creá el archivo `transformaciones.py` dentro de la carpeta `practica/`:
  * Definí una función `limpiar_monto_str(monto_raw: str) -&gt; float` que:
    * Elimine los símbolos `$` y comas `,`.
    * Convierta el texto resultante a `float`.
    * Si ocurre un error, capture el `ValueError` y devuelva `0.0`.
2. Creá el archivo `ej_13_modulos.py` dentro de la carpeta `practica/`:
  * Importá la función `limpiar_monto_str` desde `transformaciones.py` usando `from transformaciones import limpiar_monto_str`.
  * Importá también el módulo nativo `datetime` con `from datetime import datetime`.
  * Dentro de un bloque `if __name__ == "__main__":`:
    * Procesá la lista de datos sucios: `["$1,500.50", "$200.00", "INVALIDO", "$3,450.75"]`.
    * Imprimí cada monto convertido junto con la fecha y hora actual formateada (`datetime.now().strftime("%Y-%m-%d %H:%M:%S")`).
3. Ejecutá tu script desde la terminal: `python3 practica/ej_13_modulos.py`