# 🐍 Lección 30: Cierre del Bloque 3 — Proyecto Integrador y Refactorización Avanzada

¡Llegamos a la lección final del **Bloque 3: Python Avanzado y Entornos de Desarrollo**!

A lo largo de este bloque hemos incorporado herramientas de nivel Senior:

* **Lección 21**: Decoradores (`@decorador`) para auditoría y medición de tiempo.
* **Lección 22**: Generadores (`yield`) para procesamiento streaming eficiente en memoria.
* **Lección 23**: Comprensiones (*Comprehensions*) para transformaciones concisas y eficientes.
* **Lección 24**: Entornos virtuales (`venv`) y gestión de dependencias (`requirements.txt`).
* **Lecciones 25 y 26**: Testing automatizado con `pytest`, *Fixtures*, *Parametrización* y *Coverage*.
* **Lección 27**: Perfilado con `timeit` y `cProfile` para detectar cuellos de botella.
* **Lección 28**: Concurrencia I/O e I/O-Bound con `ThreadPoolExecutor`.
* **Lección 29**: Introspección y atributos dinámicos (`getattr`, `hasattr`).

En esta lección integraremos todos estos conceptos en un **Proyecto Integrador** que refactoriza un pipeline legacy a una arquitectura modular, concurrente, testeable y optimizada.

---

## 1\. Arquitectura del Proyecto Integrador

Imaginá un sistema legado que descargaba y procesaba transacciones de forma secuencial, consumía demasiada memoria RAM y no tenía pruebas automatizadas.

Nuestra meta es refactorizarlo aplicando un diseño avanzado de 4 capas:

```
proyecto_bloque3/
├── practica/
│   ├── pipeline_integrador.py   &lt;-- Motor del pipeline (Generadores, Decoradores, Concurrencia e Introspección)
│   └── test_integrador.py       &lt;-- Suite de pruebas con pytest y Fixtures
├── requirements.txt             &lt;-- Dependencias congeladas (pytest, pytest-cov)
└── .gitignore                   &lt;-- Protección de venv y .env

```

---

## 2\. Implementación del Motor Integrador (`pipeline_integrador.py`)

A continuación vemos cómo se combinan las herramientas avanzadas del Bloque 3 en un único script elegante y desacoplado:

```
import time
from functools import wraps
from concurrent.futures import ThreadPoolExecutor
from typing import Generator, List, Dict, Any

# 1. DECORADOR DE AUDITORÍA Y TIEMPO (Lección 21)
def auditar_ejecucion(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        inicio = time.time()
        print(f"⏱️ Iniciando '{func.__name__}'...")
        resultado = func(*args, **kwargs)
        fin = time.time()
        print(f"✅ '{func.__name__}' finalizó en {fin - inicio:.4f}s")
        return resultado
    return wrapper

# 2. MOTOR DINÁMICO CON INTROSPECCIÓN (Lección 29)
class ReglasSaneamiento:
    def regla_limpiar_monto(self, registro: Dict[str, Any]) -&gt; Dict[str, Any]:
        """Asegura que el monto sea float positivo."""
        monto_raw = registro.get("monto", 0.0)
        registro["monto_limpio"] = abs(float(monto_raw))
        return registro

    def regla_normalizar_estado(self, registro: Dict[str, Any]) -&gt; Dict[str, Any]:
        """Normaliza el estado a mayúsculas."""
        estado = str(registro.get("estado", "DESCONOCIDO")).strip().upper()
        registro["estado_limpio"] = estado
        return registro

# 3. GENERADOR DE STREAMING (Lección 22) Y COMPRENSIONES (Lección 23)
def procesar_stream_datos(
    lote_raw: List[Dict[str, Any]], 
    reglas_instancia: Any, 
    nombres_reglas: List[str]
) -&gt; Generator[Dict[str, Any], None, None]:
    """Aplica dinámicamente un conjunto de reglas en modo lazy (streaming)."""
    # Filtramos dinámicamente los métodos válidos usando introspección (getattr, hasattr)
    metodos_validos = [
        getattr(reglas_instancia, r) 
        for r in nombres_reglas 
        if hasattr(reglas_instancia, r) and callable(getattr(reglas_instancia, r))
    ]

    for item in lote_raw:
        item_procesado = item.copy()
        for metodo in metodos_validos:
            item_procesado = metodo(item_procesado)
        yield item_procesado

# 4. CONCURRENCIA PARA INGESTA SIMULADA I/O-BOUND (Lección 28)
def simular_descarga_fuente(fuente_id: int) -&gt; List[Dict[str, Any]]:
    """Simula descarga I/O concurrente desde un origen externo."""
    time.sleep(0.2) # Simula latencia de red
    return [
        {"id": f"F{fuente_id}-01", "monto": "-150.50", "estado": " completada "},
        {"id": f"F{fuente_id}-02", "monto": "300.00", "estado": "pendiente"}
    ]

@auditar_ejecucion
def ejecutar_pipeline_integrado(fuentes: List[int]) -&gt; List[Dict[str, Any]]:
    # Ingesta concurrente con ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=4) as executor:
        lotes_descargados = list(executor.map(simular_descarga_fuente, fuentes))
    
    # Aplanado de listas con List Comprehension
    registros_totales = [registro for lote in lotes_descargados for registro in lote]

    # Procesamiento streaming con generador e introspección
    instancia_reglas = ReglasSaneamiento()
    reglas_a_aplicar = ["regla_limpiar_monto", "regla_normalizar_estado"]
    
    stream_procesado = procesar_stream_datos(registros_totales, instancia_reglas, reglas_a_aplicar)
    
    # Consumo final del generador
    return list(stream_procesado)

```

---

## 3\. Suite de Pruebas Automatizadas (`test_integrador.py`)

Para garantizar la calidad de software de este pipeline refactorizado, aplicamos `pytest` con **Fixtures** y **Parametrización**:

```
import pytest
from practica.pipeline_integrador import ReglasSaneamiento, procesar_stream_datos

@pytest.fixture
def reglas():
    return ReglasSaneamiento()

@pytest.mark.parametrize(
    "monto_input, monto_esperado",
    [
        ("-100.50", 100.50),
        ("200.00", 200.00),
        (0.0, 0.0)
    ]
)
def test_regla_limpiar_monto(reglas, monto_input, monto_esperado):
    registro = {"monto": monto_input}
    res = reglas.regla_limpiar_monto(registro)
    assert res["monto_limpio"] == monto_esperado

def test_procesar_stream_datos_introspeccion(reglas):
    lote = [{"monto": "-50.0", "estado": " ok "}]
    reglas_activas = ["regla_limpiar_monto", "regla_normalizar_estado"]
    
    gen = procesar_stream_datos(lote, reglas, reglas_activas)
    resultado = list(gen)
    
    assert len(resultado) == 1
    assert resultado[0]["monto_limpio"] == 50.0
    assert resultado[0]["estado_limpio"] == "OK"

```

---

## 🏋️‍♂️ Práctica de la Lección 30 (Proyecto Integrador del Bloque 3)

1. Creá el archivo `pipeline_integrador.py` dentro de la carpeta `practica/` implementando la estructura explicada arriba.
2. Creá el archivo `test_integrador.py` dentro de la carpeta `practica/`.
3. Ejecutá la suite de pruebas con medición de cobertura desde la terminal: `pytest -v --cov=practica/ --cov-report=term-missing`
4. Verificá que:
  * Todos los tests pasen exitosamente (`PASSED`).
  * La cobertura de código en `pipeline_integrador.py` supere el **85%**.
  * El pipeline ejecute la descarga concurrente sin bloqueos de memoria.