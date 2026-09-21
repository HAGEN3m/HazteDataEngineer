# 🐍 Lección 26: Testing Avanzado con `pytest` (Fixtures, Parametrización y Cobertura)

En la **Lección 25** aprendimos los fundamentos de `pytest`, la sintaxis de `assert` y la estructura AAA (*Arrange, Act, Assert*)[1][2].

A medida que los pipelines de datos crecen en complejidad, escribir los mismos datos de prueba (*mock datasets*) una y otra vez en cada función genera duplicación de código. Además, probar múltiples escenarios (casos límite o *edge cases*) puede requerir decenas de funciones de test casi idénticas.

En esta lección aprenderemos a dominar **Fixtures**, **Parametrización de Tests** y **Medición de Cobertura de Código (** **Code Coverage** **)**, las tres herramientas clave para construir suites de pruebas de nivel profesional[1][3].

---

## 1\. Fixtures en `pytest` (`@pytest.fixture`)

Una **Fixture** es una función decorada con `@pytest.fixture` que prepara y entrega un recurso compartido (un DataFrame simulado, una conexión a base de datos de prueba, un diccionario de configuración) a las funciones de test que lo necesiten.

### Ventajas de usar Fixtures:

* **Principio DRY**: Definís el dataset de prueba una sola vez y lo inyectás en múltiples tests.
* **Aislamiento**: Cada función de prueba recibe una copia o instancia limpia de la fixture, garantizando que un test no altere el estado de los demás.

```
import pytest
from typing import List, Dict, Union

# 1. DEFINICIÓN DE LA FIXTURE
@pytest.fixture
def dataset_ventas_mock() -&gt; List[Dict[str, Union[str, float]]]:
    """Provee un lote de transacciones simulado para pruebas."""
    return [
        {"id": "T-101", "monto": 100.0, "estado": "COMPLETADA"},
        {"id": "T-102", "monto": -50.0, "estado": "RECHAZADA"},
        {"id": "T-103", "monto": 250.0, "estado": "COMPLETADA"},
        {"id": "T-104", "monto": 0.0, "estado": "PENDIENTE"}
    ]

# 2. INYECCIÓN DE LA FIXTURE EN EL TEST
# Simplemente pasamos el nombre de la fixture como parámetro del test
def test_contar_ventas_completadas(dataset_ventas_mock):
    completadas = [v for v in dataset_ventas_mock if v["estado"] == "COMPLETADA"]
    assert len(completadas) == 2

def test_sumar_montos_positivos(dataset_ventas_mock):
    total = sum(v["monto"] for v in dataset_ventas_mock if v["monto"] &gt; 0)
    assert total == 350.0

```

---

## 2\. Parametrización de Tests (`@pytest.mark.parametrize`)

¿Qué pasa si querés probar una función de validación contra 10 entradas distintas (p. ej., cadenas vacías, nulos, textos con espacios, caracteres especiales)? Escribir 10 funciones `test_...` separadas es ineficiente.

Con **@pytest.mark.parametrize**, podés ejecutar la **misma función de test múltiples veces** con diferentes combinaciones de argumentos de entrada y resultados esperados.

```
import pytest

def limpiar_codigo_moneda(codigo_raw: str) -&gt; str:
    """Normaliza códigos de moneda a 3 letras mayúsculas."""
    if not codigo_raw or not isinstance(codigo_raw, str):
        return "USD"  # Valor por defecto
    
    codigo_clean = codigo_raw.strip().upper()
    return codigo_clean if len(codigo_clean) == 3 else "USD"

# --- TEST PARAMETRIZADO ---
# Sintaxis: @pytest.mark.parametrize("param1, param2, ...", [(val1, exp1), (val2, exp2)...])
@pytest.mark.parametrize(
    "entrada_raw, valor_esperado",
    [
        ("  ars  ", "ARS"),       # Minúsculas con espacios
        ("usd", "USD"),           # Minúsculas sin espacios
        ("eur", "EUR"),           # Código estándar
        ("INVALIDO", "USD"),      # Más de 3 caracteres
        ("", "USD"),              # String vacío
        (None, "USD"),            # Tipo None
        (123, "USD")              # Tipo entero
    ]
)
def test_limpiar_codigo_moneda_casos_borde(entrada_raw, valor_esperado):
    resultado = limpiar_codigo_moneda(entrada_raw)
    assert resultado == valor_esperado

```

### Salida en consola de `pytest -v`:

`pytest` ejecuta cada tupla como un sub-test independiente:

```
test_transformaciones.py::test_limpiar_codigo_moneda_casos_borde[  ars  -ARS] PASSED
test_transformaciones.py::test_limpiar_codigo_moneda_casos_borde[usd-USD] PASSED
test_transformaciones.py::test_limpiar_codigo_moneda_casos_borde[eur-EUR] PASSED
test_transformaciones.py::test_limpiar_codigo_moneda_casos_borde[INVALIDO-USD] PASSED
test_transformaciones.py::test_limpiar_codigo_moneda_casos_borde[-USD] PASSED
test_transformaciones.py::test_limpiar_codigo_moneda_casos_borde[None-USD] PASSED
test_transformaciones.py::test_limpiar_codigo_moneda_casos_borde[123-USD] PASSED

```

---

## 3\. Cobertura de Código (*Code Coverage*) con `pytest-cov`

La **Cobertura de Código** es una métrica porcentual que indica qué proporción de tu código de producción fue efectivamente ejecutada durante las pruebas unitarias.

### Instalación de `pytest-cov`:

```
pip install pytest-cov

```

### Ejecutar tests con reporte de cobertura en consola:

```
# Sintaxis: pytest --cov=