# 🐍 Lección 29: Metaprogramación Básica, Introspección y Atributos Dinámicos (`getattr`, `setattr`, `hasattr`)

En la Ingeniería de Datos de producción, es muy común construir **pipelines configurables**. En lugar de hardcodear en Python qué transformaciones aplicar a cada dataset, los pipelines modernos leen reglas desde un archivo de configuración (`JSON`, `YAML` o tabla SQL) y las ejecutan dinámicamente.

Para lograr esto, Python ofrece herramientas de **Introspección** (la capacidad del código de inspeccionar sus propios objetos en tiempo de ejecución) y **Metaprogramación básica** (manipulación dinámica de atributos y métodos).

---

## 1\. Introspección en Python: Inspeccionar Objetos en Tiempo de Ejecución

Antes de manipular un objeto dinámicamente, podemos inspeccionar sus propiedades internas utilizando funciones nativas:

* **type(obj)**: Devuelve el tipo o clase del objeto.
* **isinstance(obj, Clase)**: Comprueba si un objeto pertenece a una clase especificada.
* **dir(obj)**: Devuelve una lista con todos los atributos y métodos disponibles dentro del objeto.
* **callable(obj)**: Evalúa si el objeto se puede invocar como una función o método (devuelve `True` o `False`).

```
class ConectorPostgres:
    def conectar(self):
        return True

conector = ConectorPostgres()

# Inspección básica
print(isinstance(conector, ConectorPostgres))  # True
print(callable(conector.conectar))             # True (es un método ejecutable)
print(callable("texto"))                       # False

```

---

## 2\. Manipulación Dinámica de Atributos (`hasattr`, `getattr`, `setattr`, `delattr`)

En lugar de acceder a los atributos con la sintaxis habitual de punto (`objeto.atributo`), las siguientes funciones nativas nos permiten usar **cadenas de texto (** **strings** **)** para referenciar atributos:

| Función                             | Propósito                                             | Equivalente Estático                     |
| ----------------------------------- | ----------------------------------------------------- | ---------------------------------------- |
| **hasattr(obj, "nombre")**          | Verifica si el atributo o método existe en el objeto. | `try: obj.nombre except AttributeError:` |
| **getattr(obj, "nombre", default)** | Lee el valor del atributo o la referencia del método. | `valor = obj.nombre`                     |
| **setattr(obj, "nombre", valor)**   | Asigna o crea un nuevo atributo en el objeto.         | `obj.nombre = valor`                     |
| **delattr(obj, "nombre")**          | Elimina un atributo del objeto.                       | `del obj.nombre`                         |

```
class ConfigPipeline:
    def __init__(self):
        self.ambiente = "PROD"
        self.reintentos = 3

config = ConfigPipeline()

# 1. Verificar existencia
if hasattr(config, "ambiente"):
    # 2. Leer dinámicamente usando un string
    nombre_campo = "ambiente"
    valor = getattr(config, nombre_campo)
    print(f"Propiedad '{nombre_campo}': {valor}")  # "PROD"

# 3. Asignar dinámicamente un atributo no definido en la clase original
setattr(config, "timeout_segundos", 30)
print(config.timeout_segundos)  # 30

```

---

## 3\. Caso de Uso Real: Ejecución Dinámica de Reglas de Transformación

Imaginá un archivo `config.json` recibido desde una base de datos que especifica qué reglas de limpieza aplicar a un dataset:

```
config_reglas = ["limpiar_espacios", "convertir_mayusculas", "regla_inexistente"]

```

En lugar de escribir un bloque `if / elif` gigante, podemos invocar los métodos de la clase limpiadora dinámicamente:

```
class LimpiadorDatos:
    def limpiar_espacios(self, texto: str) -&gt; str:
        return texto.strip()

    def convertir_mayusculas(self, texto: str) -&gt; str:
        return texto.upper()

limpiador = LimpiadorDatos()
valor_raw = "  juan perez  "

# Ejecución dinámica de la secuencia de reglas
for regla in config_reglas:
    # Verificamos si la regla existe en nuestro limpiador
    if hasattr(limpiador, regla):
        metodo = getattr(limpiador, regla)
        if callable(metodo):
            valor_raw = metodo(valor_raw)
            print(f"✅ Regla '{regla}' aplicada: '{valor_raw}'")
    else:
        print(f"⚠️ Advertencia: La regla '{regla}' no está implementada. Omitiendo.")

```

**Salida en pantalla:**

```
✅ Regla 'limpiar_espacios' aplicada: 'juan perez'
✅ Regla 'convertir_mayusculas' aplicada: 'JUAN PEREZ'
⚠️ Advertencia: La regla 'regla_inexistente' no está implementada. Omitiendo.

```

---

## 4\. Invocación de Métodos por Patrón de Nombre (`dir()`)

También podés inspeccionar automáticamente un módulo o clase y ejecutar todos los métodos que sigan una convención de nombrado (por ejemplo, aquellos que comiencen con `transformar_`):

```
class PipelineSaneamiento:
    def transformar_nulos(self, datos):
        return [d for d in datos if d is not None]

    def transformar_tipo(self, datos):
        return [float(d) for d in datos]

    def auxiliar_internos():
        pass

pipeline = PipelineSaneamiento()
datos_raw = [10.0, None, 25.5, None, 40.0]

# Descubrimiento automático de métodos 'transformar_'
metodos_transformacion = [
    attr for attr in dir(pipeline) 
    if attr.startswith("transformar_") and callable(getattr(pipeline, attr))
]

for nombre_metodo in metodos_transformacion:
    metodo = getattr(pipeline, nombre_metodo)
    datos_raw = metodo(datos_raw)
    print(f"⚙️ Tras '{nombre_metodo}': {datos_raw}")

```

---

## 🏋️‍♂️ Práctica de la Lección 29

1. Creá el archivo `ej_29_introspeccion.py` dentro de la carpeta `practica/`.
2. Escribí un script para **ejecutar un motor dinámico de calidad de datos**:
  * Definí la clase `ReglasCalidad`:
    * Método `validar_montos_positivos(lote: list) -&gt; list`: Filtra los registros dejando solo aquellos con `monto &gt; 0`.
    * Método `validar_ids_presentes(lote: list) -&gt; list`: Filtra los registros que tengan una clave `id` no nula.
  * Definí la función `ejecutar_suite_calidad(instancia_reglas, lista_nombres_reglas: list, dataset: list) -&gt; list`:
    * Recorré la lista `lista_nombres_reglas`.
    * Usá `hasattr()` y `getattr()` para verificar si el método existe.
    * Si existe y es ejecutable (`callable`), aplicalo sobre el dataset.
    * Si no existe, emití un mensaje de advertencia.
    * Devolvé el dataset filtrado resultante.
3. En el bloque `if __name__ == "__main__":`:
  * Dataset de prueba:

```
dataset_test = [
    {"id": 101, "monto": 150.0},
    {"id": None, "monto": 200.0},
    {"id": 103, "monto": -50.0},
    {"id": 104, "monto": 300.0}
]

```

1. Lista de reglas a ejecutar recibidas como strings: `["validar_ids_presentes", "validar_montos_positivos", "regla_falsa"]`.
2. Ejecutá la función e imprimí los registros limpios resultantes.
3. Ejecutá tu script desde la terminal: `python3 practica/ej_29_introspeccion.py`