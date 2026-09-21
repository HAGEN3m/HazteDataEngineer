# 🐍 Lección 25: Pruebas Automatizadas Básicas con `pytest` y Aserciones (`assert`)

En las lecciones anteriores aprendimos a crear funciones, modularizar nuestro código, manejar excepciones, registrar logs con `logging` y aislar nuestras dependencias en entornos virtuales (`venv`).

Sin embargo, en la **Ingeniería de Datos**, surge una pregunta crítica antes de desplegar un pipeline a producción: **¿Cómo estamos 100% seguros de que una función de limpieza o un cálculo financiero sigue funcionando correctamente después de modificar el código?**

Probar manualmente un script ejecutándolo y mirando la consola es lento, propenso a errores humanos e inviable a gran escala. La solución profesional es escribir **Pruebas Unitarias Automatizadas (** **Unit Tests** **)** utilizando **pytest**.

---

## 1\. La Sentencia Nativa `assert` (Aserciones)

En Python, la palabra clave **assert** evalúa una condición booleana.

* Si la condición es `True`, el código continúa sin interrupciones.
* Si es `False`, Python lanza inmediatamente una excepción de tipo **AssertionError**, deteniendo la ejecución.

```
# Sintaxis: assert condicion_esperada, "Mensaje de error opcional"

monto_calculado = 120.0
monto_esperado = 120.0

# Pasa silenciosamente porque la condición es True
assert monto_calculado == monto_esperado 

# Si falla, lanza AssertionError con el mensaje especificado
# assert monto_calculado == 150.0, "Error: El monto no coincide con el valor esperado"

```

---

## 2\. Introducción a `pytest` y Convenciones de Nombrado

**pytest** es el framework de testing más popular y utilizado en el ecosistema de Python. Para que `pytest` descubra y ejecute tus pruebas de forma automática, debes seguir dos convenciones de nombrado fundamentales:

1. **Archivos de prueba**: Deben comenzar con `test_` (ejemplo: `test_transformaciones.py` o `ej_25_test.py`).
2. **Funciones de prueba**: Sus nombres deben comenzar obligatoriamente con `test_` (ejemplo: `def test_limpiar_monto_valido():`).

### Instalación en tu entorno virtual:

```
pip install pytest

```

---

## 3\. La Estructura AAA (*Arrange, Act, Assert*)

Para escribir pruebas limpias, mantenibles y profesionales, aplicamos el patrón estándar **AAA**:

* **Arrange (Preparar)**: Configuramos las variables de entrada y el estado inicial necesario para la prueba.
* **Act (Ejecutar)**: Llamamos a la función o transformación que queremos probar.
* **Assert (Verificar)**: Comprobamos con `assert` que el resultado obtenido sea exactamente igual al resultado esperado.

```
# Archivo: test_transformaciones.py

def calcular_impuesto_pais(monto: float, tasa: float = 0.21) -&gt; float:
    if monto &lt;= 0:
        return 0.0
    return round(monto * tasa, 2)

# --- FUNCIÓN DE PRUEBA UNITARIA ---
def test_calcular_impuesto_monto_positivo():
    # 1. Arrange (Preparar)
    monto_input = 100.0
    tasa_input = 0.21
    esperado = 21.0

    # 2. Act (Ejecutar)
    resultado = calcular_impuesto_pais(monto_input, tasa_input)

    # 3. Assert (Verificar)
    assert resultado == esperado

def test_calcular_impuesto_monto_negativo():
    # Arrange &amp; Act
    resultado = calcular_impuesto_pais(-50.0)

    # Assert
    assert resultado == 0.0

```

---

## 4\. Probar Excepciones Esperadas con `pytest.raises()`

En Ingeniería de Datos no solo probamos el "camino feliz" (*happy path*), sino también el comportamiento defensivo: debemos verificar que una función **lance la excepción correcta** cuando recibe datos corruptos o inválidos.

Para verificar que se lance una excepción específica usamos el administrador de contexto **pytest.raises()**:

```
import pytest

def validar_id_cliente(cliente_id: str) -&gt; bool:
    if not cliente_id.startswith("CLI-"):
        raise ValueError("El ID de cliente debe comenzar con el prefijo 'CLI-'")
    return True

def test_validar_id_cliente_invalido_lanza_exception():
    # Verificamos que la función lance un ValueError al recibir un ID inválido
    with pytest.raises(ValueError) as exc_info:
        validar_id_cliente("12345")
    
    # Comprobamos el mensaje exacto de la excepción
    assert "prefijo 'CLI-'" in str(exc_info.value)

```

---

## 5\. Ejecutar los Tests desde la Terminal

Para correr todas las pruebas automatizadas de tu proyecto, simplemente ejecutas el comando `pytest` en la raíz de la carpeta de trabajo:

```
# Ejecutar todas las pruebas del proyecto
pytest

# Ejecutar con detalles paso a paso (-v = verbose)
pytest -v

# Ejecutar un archivo específico
pytest practica/test_ej_25.py

```

### Ejemplo de salida exitosa en consola:

```
============================= test session starts ==============================
collected 3 items

practica/test_ej_25.py ::test_calcular_impuesto_monto_positivo PASSED   [ 33%]
practica/test_ej_25.py ::test_calcular_impuesto_monto_negativo PASSED   [ 66%]
practica/test_ej_25.py ::test_validar_id_cliente_invalido_lanza_exception PASSED [100%]

============================== 3 passed in 0.05s ===============================

```

---

## 🏋️‍♂️ Práctica de la Lección 25

1. Asegúrate de tener activado tu entorno virtual (`venv`) e instala `pytest`: `pip install pytest`
2. Creá el archivo `test_ej_25_pytest.py` dentro de la carpeta `practica/`.
3. Escribí la función de negocio a probar:

```
def normalizar_columna_pais(pais_raw: str) -&gt; str:
    if not pais_raw or not isinstance(pais_raw, str):
        raise TypeError("El país ingresado debe ser una cadena de texto no vacía.")
    
    pais_limpio = pais_raw.strip().upper()
    mapa_paises = {"ARG": "ARGENTINA", "AR": "ARGENTINA", "CL": "CHILE", "CHILE": "CHILE"}
    return mapa_paises.get(pais_limpio, "DESCONOCIDO")

```

1. En el mismo archivo, escribí **3 funciones de prueba unitarias** utilizando la estructura AAA y `assert`:
  * `test_normalizar_pais_valido()`: Verifica que `" ar "` devuelva `"ARGENTINA"`.
  * `test_normalizar_pais_desconocido()`: Verifica que `"MEXICO"` devuelva `"DESCONOCIDO"`.
  * `test_normalizar_pais_tipo_invalido()`: Usa `pytest.raises(TypeError)` para verificar que pasar un número (ej: `123` o `None`) lance un `TypeError`.
2. Ejecutá la suite de pruebas desde la terminal: `pytest -v practica/test_ej_25_pytest.py`