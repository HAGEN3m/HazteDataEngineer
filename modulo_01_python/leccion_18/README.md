# 🐍 Lección 18: Programación Orientada a Objetos para Pipelines (`class` e `__init__`)

En la Ingeniería de Datos moderna, la **Programación Orientada a Objetos (POO)** es la estructura dominante para construir conectores a bases de datos, clientes de APIs REST, abstracciones de almacenamiento en la nube (S3, GCS, Blob Storage) y componentes de frameworks distribuidos como PySpark.

Una **Clase** es un molde o plantilla que define propiedades (atributos) y comportamientos (métodos). Un **Objeto** (o instancia) es un ejemplar concreto creado en memoria a partir de esa clase.

---

## 1\. ¿Por qué usar POO en Data Engineering?

En lugar de pasar 10 parámetros sueltos entre funciones para manejar una conexión o un conector de datos, una Clase agrupa en una sola entidad:

* **Estado (Atributos)**: Credenciales, host, puerto, estado de la conexión, contador de filas procesadas.
* **Comportamiento (Métodos)**: `conectar()`, `extraer_lote()`, `transformar()`, `desconectar()`.

---

## 2\. Definir una Clase e Inicializador (`__init__` y `self`)

* **class**: Palabra clave para definir la plantilla.
* **\_\_init\_\_**: Es el **constructor** o método especial que se ejecuta automáticamente cuando creás un nuevo objeto. Se utiliza para inicializar los atributos de la instancia.
* **self**: Representa a la instancia específica que se está creando o manipulando. Siempre debe ser el primer parámetro de todos los métodos dentro de una clase.

```
class ConectorDatabase:
    """Clase para gestionar conexiones a bases de datos relacionales."""
    
    def __init__(self, host: str, puerto: int, base_datos: str):
        # Atributos de instancia
        self.host = host
        self.puerto = puerto
        self.base_datos = base_datos
        self.esta_conectado = False

    def conectar(self) -&gt; None:
        """Simula la apertura de la conexión."""
        print(f"🔌 Conectando a {self.base_datos} en {self.host}:{self.puerto}...")
        self.esta_conectado = True
        print("🟢 Conexión establecida con éxito.")

    def desconectar(self) -&gt; None:
        """Cierra la conexión activa."""
        if self.esta_conectado:
            self.esta_conectado = False
            print("🔴 Conexión cerrada.")

```

---

## 3\. Crear Instancias (Objetos) y Llamar Métodos

A partir de una misma clase podés instanciar múltiples objetos aislados, cada uno con su propio estado:

```
# Instanciamos dos conectores independientes
db_prod = ConectorDatabase("prod-db.internal", 5432, "dw_ventas")
db_stage = ConectorDatabase("localhost", 5432, "dw_test")

# Cada objeto mantiene su propio estado interno
db_prod.conectar()

print(f"Estado DB Prod: {db_prod.esta_conectado}")   # True
print(f"Estado DB Stage: {db_stage.esta_conectado}") # False

```

---

## 4\. Métodos con Retorno y Lógica de Negocio

Los métodos pueden leer y modificar los atributos internos mediante `self.atributo` para llevar la cuenta de métricas o controlar el flujo de trabajo:

```
class ExtractorAPI:
    def __init__(self, api_url: str, api_key: str):
        self.api_url = api_url
        self.api_key = api_key
        self.registros_extraidos = 0

    def extraer_lote(self, limite: int = 100) -&gt; list:
        if not self.api_key:
            raise ValueError("🔴 Error: API Key no configurada.")
            
        print(f"📡 Extrayendo hasta {limite} registros de {self.api_url}...")
        # Simulación de extracción de datos
        lote_simulado = [{"id": i, "valor": i * 10} for i in range(1, limite + 1)]
        self.registros_extraidos += len(lote_simulado)
        return lote_simulado

```

---

## 🏋️‍♂️ Práctica de la Lección 18

1. Creá el archivo `ej_18_poo.py` dentro de la carpeta `practica/`.
2. Escribí un script que implemente la clase `PipelineIngesta`:
  * **Atributos en** **\_\_init\_\_**:
    * `nombre_pipeline` (`str`).
    * `fuente_datos` (`str`).
    * `registros_procesados` (`int`, inicia en `0`).
    * `estado` (`str`, inicia en `"DETENIDO"`).
  * **Métodos**:
    * `iniciar()`: Cambia `estado` a `"EN_EJECUCION"` e imprime un mensaje indicando el inicio del pipeline.
    * `procesar_lote(lote: list)`:
      * Si `estado` no es `"EN_EJECUCION"`, imprime una advertencia: `"⚠️ No se puede procesar: El pipeline está detenido."` y termina el método.
      * Si está en ejecución, suma la cantidad de elementos de `lote` a `registros_procesados` e imprime cuántos registros se procesaron en el lote y el acumulado actual.
    * `finalizar()`: Cambia `estado` a `"FINALIZADO"` e imprime un resumen con el total histórico de `registros_procesados`.
3. En el bloque `if __name__ == "__main__":`:
  * Instanciá la clase: `pipeline = PipelineIngesta("Ingesta_Clientes", "api_crm_v2")`.
  * Intentá procesar un lote antes de iniciar para comprobar la validación del estado.
  * Llamá a `iniciar()`.
  * Procesá dos lotes de prueba: `[101, 102, 103]` y `[104, 105, 106, 107]`.
  * Llamá a `finalizar()`.
4. Ejecutá tu script desde la terminal: `python3 practica/ej_18_poo.py`