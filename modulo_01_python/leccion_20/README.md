# 🐍 Lección 20: Polimorfismo y Clases Abstractas (`abc.ABC` y `@abstractmethod`)

¡Llegamos a la lección de cierre del **Bloque 2: Programación Modular y Robusta**!

Cuando diseñamos frameworks o arquitecturas de datos para un equipo, queremos asegurar que todos los conectores o transformadores sigan exactamente las mismas reglas. En esta lección aprenderemos a usar **Clases Abstractas** e **Interfaces** mediante el módulo nativo `abc` (*Abstract Base Classes*), lo que nos permite implementar el concepto de **Polimorfismo**.

---

## 1\. ¿Qué es una Clase Abstracta y un Contrato de Interfaz?

Una **Clase Abstracta** es una clase base que **no está pensada para ser instanciada directamente**, sino para servir como "contrato" o plantilla obligatoria para sus clases hijas.

Si definimos un método decorado con **@abstractmethod**, obligamos a cualquier clase hija a implementar ese método. Si la clase hija no lo implementa, Python no nos dejará instanciar el objeto y lanzará un error `TypeError` inmediatamente.

```
from abc import ABC, abstractmethod

# Clase Abstracta (Contrato Base)
class ExtractorBase(ABC):
    
    @abstractmethod
    def extraer() -&gt; list:
        """Método abstracto obligatorio para todos los extractores."""
        pass
    
    @abstractmethod
    def Validar_conexion() -&gt; bool:
        """Verifica la conectividad con el origen."""
        Pass

```

---

## 2\. Polimorfismo en Pipelines de Datos

El **Polimorfismo** (*muchas formas*) es la capacidad de tratar diferentes clases hijas a través de una misma interfaz común.

Imaginá que tenés un pipeline que procesa datos de tres orígenes distintos (Postgres, API REST y archivos S3). En lugar de escribir un `if/elif` gigante para cada fuente, usás polimorfismo para recorrer una lista de extractores y llamar a `.extraer()` en todos de la misma forma:

```
class ExtractorPostgres(ExtractorBase):
    Def extraer(self) -&gt; list:
        Print("🐘 Extrayendo filas desde tabla SQL...")
        Return [{"id": 1, "origen": "sql"}]
        
    Def validar_conexion(self) -&gt; bool:
        Return True

Class ExtractorS3(ExtractorBase):
    Def extraer(self) -&gt; list:
        Print("☁️ Descargando objetos desde AWS S3...")
        Return [{"id": 2, "origen": "s3"}]
        
    Def validar_conexion(self) -&gt; bool:
        Return True

# ⚡ POLIMORFISMO EN ACCIÓN:
# Recorremos fuentes heterogéneas tratándolas con la misma interfaz
Fuentes: list[ExtractorBase] = [ExtractorPostgres(), ExtractorS3()]

For fuente in fuentes:
    If fuente.validar_conexion():
        Datos = fuente.extraer()
        Print(f"Registros obtenidos: {len(datos)}")

```

---

## 3\. ¿Por qué es Vital para Ingenieros de Datos Senior?

* **Extensibilidad**: Si el mes que viene agregás una nueva fuente (ej. *MongoDB*), solo creás una clase `ExtractorMongo` que implemente `ExtractorBase`. **No tenés que tocar ni una sola línea del motor principal del pipeline.**
* **Estandarización**: Garantiza que todo el equipo nombre los métodos de la misma forma (evita que un desarrollador use `obtener_datos()`, otro `read_data()` y otro `fetch_rows()`).

---

## 🏋️‍♂️ Práctica de la Lección 20

1. Creá el archivo `ej_20_polimorfismo.py` dentro de la carpeta `practica/`.
2. Escribí una arquitectura extensible de **Cargadores de Datos (** **Loaders** **)**:
  * Importá `ABC` y `abstractmethod` desde `abc`.
  * Definí la clase abstracta `CargadorBase(ABC)`:
    * Métodos abstractos obligatorios:
      * `cargar(datos: list) -&gt; bool`
      * `obtener_destino() -&gt; str`
  * Definí la clase hija `CargadorDatabase(CargadorBase)`:
    * Implementá `cargar`: Imprime `"📥 Insertando