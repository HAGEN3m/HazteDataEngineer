# ⚡ Lección 04.B (Módulo 06): Schema Registry, Avro / Protobuf y Data Governance en Event Streams

&gt; **Propósito**: Dominar la gobernanza de datos y la evolución de esquemas en arquitecturas basadas en eventos (*Event-Driven Architectures*), comprendiendo el funcionamiento de Confluent Schema Registry, las diferencias entre formatos binarios (Avro y Protobuf), las reglas de compatibilidad (`BACKWARD`, `FORWARD`, `FULL`) y la prevención de cambios disruptivos (*breaking changes*) en producción.

---

## 📌 1\. El Problema del Breaking Change en Event Streams

En arquitecturas distribuidas orientadas a eventos, los productores y consumidores de datos están desacoplados en el tiempo y en el espacio. Si un equipo modifica el formato de los mensajes en un topic de Kafka utilizando un JSON no estructurado (por ejemplo, renombrando el campo `user_id` a `account_id` o cambiando el tipo de dato de un entero a un string), los consumidores *downstream* colapsarán inmediatamente en producción.

```
❌ SIN SCHEMA REGISTRY (Payload JSON pesado y frágil):
[ Producer ] ─── JSON: {"user_id": 101, "monto": 50.0} ───&gt; [ Kafka Topic ] ───&gt; [ Consumer ] (Explota si cambia "user_id")

✅ CON SCHEMA REGISTRY (Payload binario liviano + Contrato de Datos):
[ Producer ] ─── 5 Bytes Header + Payload Avro Binario ───&gt; [ Kafka Topic ] ───&gt; [ Consumer ]
     │                                                                                │
     └─── (Valida Schema ID en CI/CD o Runtime) ── [ Schema Registry ] ───────────────┘

```

### ¿Por qué JSON/XML son ineficientes para Event Streaming a Gran Escala?

1. **Overhead de Tamaño**: Cada mensaje incluye repetidamente las claves de los campos (`"user_id"`, `"timestamp"`), lo que multiplica por 5x a 10x el uso de ancho de banda y almacenamiento en disco.
2. **Falta de Tipado Fuerte**: No hay garantía de que un campo numérico no contenga un valor `null` o un string inesperado.
3. **Ausencia de Validación en Tiempo de Producción**: El fallo ocurre en el consumidor (*Downstream*) y no en el momento en que el productor intenta publicar el evento (*Upstream*).

---

## 🔬 2\. Formatos Binarios y Confluent Schema Registry

Para resolver este problema, los sistemas de Event Streaming utilizan formatos de serialización binaria basados en esquemas como **Apache Avro** o **Protocol Buffers (Protobuf)** junto con un servidor centralizado de gobernanza denominado **Schema Registry**.

### A. Apache Avro

* **Esquema JSON explícito**: Define la estructura de datos en un archivo `.avsc`.
* **Payload puramente binario**: El mensaje transmitido por la red solo contiene los valores, sin los nombres de los campos.
* **Separación de Metadatos**: El esquema no viaja en cada mensaje, lo que reduce drásticamente el tamaño del payload.

### B. El Wire Protocol de Confluent Schema Registry

Cuando un productor envía un mensaje serializado con Avro/Protobuf a Kafka usando el cliente de Schema Registry, antepone **5 bytes mágicos** al payload binario:

```
┌──────────────┬────────────────────────┬──────────────────────────────────────────┐
│ Byte 0       │ Bytes 1 - 4            │ Bytes 5 en adelante                      │
│ (Magic Byte) │ (Schema ID - int32)    │ Payload Binario Serializado (Avro/Proto) │
└──────────────┴────────────────────────┴──────────────────────────────────────────┘

```

1. **Byte 0 (Magic Byte)**: Siempre `0x00` para indicar el protocolo de Confluent.
2. **Bytes 1-4 (Schema ID)**: Identificador entero único (32 bits) asignado por el Schema Registry para ese esquema específico.
3. **Bytes 5+**: Los datos del evento serializados en binario.

&gt; **Flujo de Lectura del Consumidor**: Al recibir el evento, el consumidor lee los primeros 5 bytes, extrae el `Schema ID`, consulta el esquema al Schema Registry (y lo guarda en memoria en un *LRU Cache* local) y deserializa los datos binarios sin costo adicional.

---

## 🛠️ 3\. Reglas de Evolución de Esquemas (Compatibility Modes)

El Schema Registry actúa como un "guardián de la puerta" (*Gatekeeper*). Si un productor intenta registrar un nuevo esquema que viola la regla de compatibilidad configurada para el topic, la API del Registry rechaza el esquema con un error HTTP `409 Conflict`.

```
                    ┌───────────────────────────────────────────────┐
                    │               SCHEMA REGISTRY                 │
                    │ Configuración de Compatibilidad: BACKWARD      │
                    └───────────────────────┬───────────────────────┘
                                            │
   [ Productor intenta enviar V2 ] ─────────┼───────&gt; (Valida compatibilidad)
                                            │                 │
                                            │       ┌─────────┴─────────┐
                                            │       ▼                   ▼
                                            │   [ Válido ]        [ Inválido ]
                                            │   Registra ID      Error HTTP 409

```

### Modos de Compatibilidad Esenciales:

| Modo                       | Regla de Validación                                                                                                                             | Estrategia de Despliegue Recomendada                                                     |
| -------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| **`BACKWARD`** *(Default)* | El nuevo esquema (V2) puede leer datos producidos con el esquema anterior (V1). **Permite eliminar campos o agregar campos opcionales**.        | Actualizar primero los **Consumidores** a V2 y luego los Productores a V2.               |
| **`FORWARD`**              | El esquema anterior (V1) puede leer datos producidos con el nuevo esquema (V2). **Permite agregar campos nuevos o eliminar campos opcionales**. | Actualizar primero los **Productores** a V2 y luego los Consumidores a V2.               |
| **`FULL`**                 | Combinación de `BACKWARD` y `FORWARD`. V2 lee datos de V1 y V1 lee datos de V2.                                                                 | Permite actualizar consumidores y productores en cualquier orden sin detener la tubería. |
| **`NONE`**                 | Desactiva las comprobaciones de compatibilidad.                                                                                                 | ❌ **Inseguro para producción**.                                                          |

---

## ⚡ 4\. Data Governance y Data Contracts en Streams

Un **Data Contract** en Event Streaming es un acuerdo formal entre los equipos de desarrollo de software (productores de eventos) y los equipos de ingeniería/analítica de datos (consumidores) que especifica:

* **Estructura semántica**: Campos requeridos, tipos de datos y valores permitidos.
* **SLA de calidad**: Frecuencia, volumen y política de compatibilidad.
* **Punto de aplicación**: CI/CD pipeline utilizando el plugin de Maven/Gradle o la CLI de Confluent Schema Registry (`schema-registry-cli test`).

---

## 🏋️‍♂️ Ejercicio Práctico Hands-On: Serialización y Deserialización con Avro en Python

A continuación se presenta un script completo utilizando la librería `confluent-kafka` con `AvroSerializer` y `AvroDeserializer`:

```
#!/usr/bin/env python3
"""
Lección 06.04.B: Productor y Consumidor Avro con Schema Registry
Requisitos: pip install confluent-kafka fastavro
"""

import io
from confluent_kafka import Producer, Consumer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer, AvroDeserializer
from confluent_kafka.serialization import StringSerializer, StringDeserializer, SerializationContext, MessageField

# 1. Definición del Esquema Avro (Contrato de Datos V1)
USER_AVRO_SCHEMA = """
{
  "type": "record",
  "name": "UserEvent",
  "namespace": "com.company.analytics",
  "fields": [
    {"name": "user_id", "type": "int", "doc": "ID único del usuario"},
    {"name": "email", "type": "string", "doc": "Correo electrónico registrado"},
    {"name": "signup_timestamp", "type": "long", "doc": "Epoch timestamp en milisegundos"},
    {"name": "is_premium", "type": "boolean", "default": false, "doc": "Indicador de cuenta de pago"}
  ]
}
"""

# 2. Clases DTO / Funciones de Mapeo
class UserEvent:
    def __init__(self, user_id: int, email: str, signup_timestamp: int, is_premium: bool = False):
        self.user_id = user_id
        self.email = email
        self.signup_timestamp = signup_timestamp
        self.is_premium = is_premium

def user_to_dict(user: UserEvent, ctx) -&gt; dict:
    return {
        "user_id": user.user_id,
        "email": user.email,
        "signup_timestamp": user.signup_timestamp,
        "is_premium": user.is_premium,
    }

def dict_to_user(obj: dict, ctx) -&gt; UserEvent:
    return UserEvent(
        user_id=obj["user_id"],
        email=obj["email"],
        signup_timestamp=obj["signup_timestamp"],
        is_premium=obj.get("is_premium", False)
    )

def main():
    # Configuración de clientes (Apuntando a instancias locales o de pruebas)
    schema_registry_conf = {'url': 'http://localhost:8081'}
    schema_registry_client = SchemaRegistryClient(schema_registry_conf)

    # Serializador Avro
    avro_serializer = AvroSerializer(
        schema_registry_client=schema_registry_client,
        schema_str=USER_AVRO_SCHEMA,
        to_dict=user_to_dict
    )

    producer_conf = {'bootstrap.servers': 'localhost:9092'}
    producer = Producer(producer_conf)

    # Producir un evento serializado en Avro
    user_data = UserEvent(
        user_id=1054,
        email="data.engineer@company.com",
        signup_timestamp=1727150000000,
        is_premium=True
    )

    print("📤 Enviando evento Avro serializado a Kafka...")
    producer.produce(
        topic="analytics_users_v1",
        key=StringSerializer()('user_1054'),
        value=avro_serializer(user_data, SerializationContext('analytics_users_v1', MessageField.VALUE))
    )
    producer.flush()
    print("✅ Evento enviado correctamente.")

if __name__ == '__main__':
    # Nota: Este script requiere que un Broker Kafka y Schema Registry estén activos en localhost.
    print("Demostración de código de producción con Avro y Schema Registry.")

```

---

## 🧠 Checkpoint de Autoevaluación

1. ¿Por qué enviar esquemas completos dentro del payload de cada mensaje JSON es un anti-patrón de arquitectura a gran escala y cómo lo resuelve el *Wire Protocol* de Confluent Schema Registry?
2. ¿Cuál es la diferencia técnica entre el modo de compatibilidad **`BACKWARD`** y **`FORWARD`** en el Schema Registry y en qué orden se deben desplegar los productores y consumidores en cada caso?
3. ¿Qué sucede si un equipo de desarrollo intenta enviar un evento con un esquema no compatible a un topic configurado con Schema Registry?
4. ¿Qué función cumplen los primeros 5 bytes en el payload de un mensaje serializado con Avro/Schema Registry?