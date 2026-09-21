# 🐍 Lección 19: POO Avanzada (Herencia, Encapsulamiento y Métodos Especiales)

En la Lección 18 creamos nuestras primeras clases básicas. En la **Ingeniería de Datos**, es común trabajar con familias de componentes similares: por ejemplo, distintos conectores para extraer datos desde Postgres, MySQL, APIs REST o S3.

En esta lección aprenderemos tres pilares avanzados de la **Programación Orientada a Objetos (POO)**: **Herencia**, **Encapsulamiento** y **Métodos Especiales (** **Dunder Methods** **)**.

---

## 1\. Herencia: Reutilización de Código entre Clases

La **Herencia** permite crear una clase hija que hereda automáticamente los atributos y métodos de una clase padre (o clase base).

* **Clase Padre (Base)**: Contiene la lógica común a todos los conectores (por ejemplo, guardar la URL de conexión y el contador de registros).
* **Clase Hija**: Extiende o personaliza el comportamiento para una fuente específica (por ejemplo, Postgres o S3) reutilizando el constructor del padre con **super().\_\_init\_\_()**.

```
# Clase Padre
class ConectorBase:
    def __init__(self, nombre_fuente: str):
        self.nombre_fuente = nombre_fuente
        self.conectado = False

    def conectar(self) -&gt; None:
        self.conectado = True
        print(f"🔌 [Base] Conexión abierta con: {self.nombre_fuente}")

# Clase Hija que hereda de ConectorBase
class ConectorPostgres(ConectorBase):
    def __init__(self, host: str, base_datos: str):
        # Llamamos al constructor de la clase padre
        super().__init__(nombre_fuente=f"PostgreSQL ({base_datos})")
        self.host = host

    # Método propio de la clase hija
    def ejecutar_query(self, query_sql: str) -&gt; list:
        if not self.conectado:
            raise ConnectionError("🔴 No se puede ejecutar query sin conexión activa.")
        print(f"⚡ Ejecutando en {self.host}: {query_sql}")
        return [{"id": 1, "resultado": "ok"}]

```

---

## 2\. Encapsulamiento: Proteger Atributos Sensibles

El **Encapsulamiento** consiste en ocultar o restringir el acceso directo a ciertos atributos internos para evitar que se modifiquen por error desde afuera.

En Python, el encapsulamiento es una convención de nombrado:

* **Público (** **atributo** **)**: Se puede leer y modificar libremente desde cualquier lugar.
* **Protegido (** **\_atributo** **)**: Un guion bajo inicial indica que es de uso interno de la clase o sus hijas.
* **Privado (** **\_\_atributo** **)**: Dos guiones bajos iniciales activan el *Name Mangling* de Python, haciendo muy difícil acceder al atributo fuera de la clase.

```
class ClienteAPI:
    def __init__(self, endpoint: str, api_key: str):
        self.endpoint = endpoint      # Atributo Público
        self.__api_key = api_key     # Atributo Privado (sensible)

    def obtener_token_oculto(self) -&gt; str:
        # Método público seguro para mostrar la clave de forma enmascarada
        return f"{self.__api_key[:4]}****"

```

---

## 3\. Métodos Especiales (*Dunder Methods*)

Los métodos especiales (que empiezan y terminan con doble guion bajo `__`) le enseñan a Python cómo comportarse al usar funciones nativas como `print()`, `str()` o `len()` con tus propios objetos.

Los dos más importantes son:

* **\_\_str\_\_(self)**: Define cómo se muestra el objeto cuando lo imprimís con `print()` o en un log (orientado al usuario final).
* **\_\_repr\_\_(self)**: Define la representación técnica del objeto (orientado al desarrollador para depuración).

```
class MetricaPipeline:
    def __init__(self, nombre: str, valor: float):
        self.nombre = nombre
        self.valor = valor

    def __str__(self) -&gt; str:
        # Salida amigable para usuarios
        return f"Métrica '{self.nombre}': {self.valor}"

    def __repr__(self) -&gt; str:
        # Representación técnica ejecutable
        return f"MetricaPipeline(nombre='{self.nombre}', valor={self.valor})"

m = MetricaPipeline("filas_procesadas", 10500.0)
print(m)        # Ejecuta __str__: "Métrica 'filas_procesadas': 10500.0"
print(repr(m))  # Ejecuta __repr__: "MetricaPipeline(nombre='filas_procesadas', valor=10500.0)"

```

---

## 🏋️‍♂️ Práctica de la Lección 19

1. Creá el archivo `ej_19_poo_avanzada.py` dentro de la carpeta `practica/`.
2. Escribí un script con una jerarquía de conectores de almacenamiento:
  * **Clase Base** **AlmacenamientoBase**:
    * Atributos en `__init__`: `nombre_servicio` (`str`) y atributo privado `__clave_acceso` (`str`).
    * Método `mostrar_credencial_segura()`: Retorna los primeros 3 caracteres de `__clave_acceso` seguidos de `"***"`.
    * Método `__str__()`: Retorna `"Servicio de Almacenamiento: