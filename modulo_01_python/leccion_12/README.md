# 🐍 Lección 12: Anotaciones de Tipo (Type Hinting) y Documentación (Docstrings)

A medida que los pipelines de datos crecen y son mantenidos por equipos enteros de ingenieros, escribir código legible y autofirmado se vuelve un requisito crítico de producción.

En esta lección aprenderemos a usar **Type Hinting** (pistas de tipo) para especificar qué tipo de datos espera y devuelve cada función, y **Docstrings** para documentar profesionalmente su comportamiento.

---

## 1\. Anotaciones de Tipo (Type Hinting)

Python es un lenguaje de tipado dinámico, lo que significa que no exige declarar el tipo de variable. Sin embargo, desde Python 3.5 podemos agregar **pistas de tipo** explícitas usando dos puntos `:` en los parámetros y `-&gt;` para el valor de retorno.

```
# Sintaxis básica: variable: tipo -&gt; tipo_retorno
def calcular_iva(monto: float, porcentaje: int = 21) -&gt; float:
    return monto * (porcentaje / 100)

```

### ¿Por qué es fundamental en Ingeniería de Datos?

* **Autocompletado e IntelliSense**: Tu editor de código (VS Code) sabe exactamente qué métodos sugerirte.
* **Detección temprana de errores**: Herramientas de análisis estático (como `mypy`) pueden avisarte si le estás pasando un `str` a una función que esperaba un `float` antes de ejecutar el código.

---

## 2\. Tipos Complejos y el Módulo `typing`

Para anotar estructuras de datos más avanzadas (listas de diccionarios, valores opcionales o múltiples tipos posibles), utilizamos el módulo nativo `typing` (o la sintaxis moderna de Python 3.10+):

```
from typing import List, Dict, Optional, Union

# List[float]: Una lista que contiene floats
# Optional[float]: Puede ser float o None
def procesar_lote_montos(registros: List[Dict[str, Union[int, float]]]) -&gt; Optional[float]:
    if not registros:
        return None
    
    total = sum(item["monto"] for item in registros)
    return float(total)

```

&gt; 💡 **En Python 3.10+**: Podés usar `list[float]` en minúscula y el operador `|` para uniones (ej: `float | None` en lugar de `Optional[float]`).

---

## 3\. Documentación Profesional con Docstrings

Un **Docstring** es una cadena de texto encerrada entre triples comillas `"""` ubicada en la primera línea dentro de una función, clase o módulo.

Sirve para explicar qué hace la función, qué parámetros recibe, qué devuelve y qué excepciones puede lanzar. El estándar más extendido en la industria es el estilo de **Google**:

```
def transformar_registro_cliente(
    cliente_id: str, 
    monto_usd: float, 
    es_vip: bool = False
) -&gt; Dict[str, Union[str, float]]:
    """Transforma y aplica descuentos a un registro de cliente.

    Args:
        cliente_id (str): Identificador único del cliente (ej: 'C-101').
        monto_usd (float): Monto bruto de la transacción en USD.
        es_vip (bool, optional): Indica si aplica descuento especial del 15%. Defaults to False.

    Returns:
        Dict[str, Union[str, float]]: Diccionario estructurado con el id y el monto final ajustado.

    Raises:
        ValueError: Si monto_usd es menor o igual a cero.
    """
    if monto_usd &lt;= 0:
        raise ValueError("El monto debe ser estrictamente positivo.")

    monto_final = monto_usd * 0.85 if es_vip else monto_usd

    return {
        "cliente_id": cliente_id,
        "monto_final": round(monto_final, 2)
    }

```

---

## 🏋️‍♂️ Práctica de la Lección 12

1. Creá el archivo `ej_12_type_hinting_docstrings.py` dentro de la carpeta `practica/`.
2. Escribí una función modular para **filtrar y calcular métricas de ingesta**:
  * Nombre de la función: `filtrar_y_promediar_ventas`.
  * **Parámetros con Type Hints**:
    * `ventas`: Una lista de diccionarios, donde cada diccionario representa una venta (`List[Dict[str, Union[str, float]]]`).
    * `estado_filtro`: Cadena de texto con el estado a filtrar, con valor por defecto `"COMPLETADA"` (`str`).
  * **Tipo de retorno**: `Optional[float]` (devuelve un `float` o `None`).
  * **Docstring estilo Google**: Escribí la documentación completa incluyendo `Args:`, `Returns:` y la descripción del proceso.
  * **Lógica interna**:
    * Filtrá solo las ventas cuyo campo `"estado"` sea igual a `estado_filtro` y cuyo `"monto"` sea mayor a 0.
    * Si no hay ventas válidas que cumplan el criterio, retorná `None`.
    * Si hay ventas válidas, retorná el promedio redondeado a 2 decimales.
3. Fuera de la función, probá ejecutarla con el siguiente dataset y mostrá el resultado en pantalla:

```
dataset_test = [
    {"id": "101", "monto": 150.0, "estado": "COMPLETADA"},
    {"id": "102", "monto": -50.0, "estado": "COMPLETADA"},
    {"id": "103", "monto": 300.0, "estado": "PENDIENTE"},
    {"id": "104", "monto": 250.0, "estado": "COMPLETADA"}
]

```

1. Ejecutá tu script desde la terminal: `python3 practica/ej_12_type_hinting_docstrings.py`