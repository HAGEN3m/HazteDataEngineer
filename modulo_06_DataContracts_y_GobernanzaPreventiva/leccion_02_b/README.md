# ⚡ Lección 02.B (Módulo 06): Productores &amp; Consumidores Avanzados: Consumer Groups, Rebalanceo, EOS e Idempotencia

&gt; **Propósito**: Dominar la resiliencia y semánticas de entrega en Apache Kafka a nivel de producción, comprendiendo la configuración de productores idempotentes (`enable.idempotence`), los algoritmos de rebalanceo de *Consumer Groups* (*Eager* vs *Cooperative Sticky*), las transacciones *Exactly-Once Semantics* (EOS) y el manejo defensivo de errores mediante *Dead Letter Queues* (DLQ).

---

## 📌 1\. Productores Avanzados, Confirmaciones (Acks) e Idempotencia

En sistemas distribuidos, las fallas de red son inevitables. Cuando un productor envía un mensaje a un broker de Kafka y la red se interrumpe antes de recibir la confirmación (*Acknowledge* / ACK), el productor reintentará el envío.

```
Escenario Sin Idempotencia (Duplicados por Reintentos):
[ Producer ] ─── (Mensaje A) ───&gt; [ Leader Broker ] (Guarda A)
[ Producer ] &lt;── (ACK Perdido) ─── [ Network Failure ]
[ Producer ] ─── (Reintento A) ─&gt; [ Leader Broker ] (Guarda A otra vez -&gt; DUPLICADO)

Escenario Con Idempotencia (`enable.idempotence=true`):
[ Producer ] ─── (PID: 101, Seq: 0) ───&gt; [ Leader Broker ] (Guarda PID:101, Seq:0)
[ Producer ] ─── (PID: 101, Seq: 0) ───&gt; [ Leader Broker ] (Detecta Seq:0 duplicado -&gt; DESCARTA)

```

### Configuración del Productor:

* **`acks=0`**: El productor no espera confirmación. Máximo rendimiento, riesgo de pérdida de datos.
* **`acks=1`**: Espera la confirmación del nodo Líder. Protege contra fallas simples, pero si el líder cae antes de replicar, los datos se pierden.
* **`acks=all` (o `-1`)**: Espera confirmación del Líder y de todas las réplicas síncronas (`min.insync.replicas`). **Estándar de producción**.

### Productor Idempotente (`enable.idempotence=true`)

Al activar la idempotencia, el broker asigna a cada productor un **Producer ID (PID)** y asigna un **número de secuencia creciente** a cada mensaje por partición. Si el broker recibe un número de secuencia que ya procesó, descarta el duplicado a nivel de almacenamiento sin lanzar error al cliente.

---

## 🔬 2\. Consumer Groups &amp; Protocolos de Rebalanceo

Un **Consumer Group** permite escalar la lectura de un topic repartiendo las particiones entre múltiples instancias de consumidores.

```
Topic: 'transacciones_bancarias' (4 Particiones)

Consumer Group 'fraud_detection_group':
┌───────────────────────┬───────────────────────┐
│ Consumidor 1          │ Consumidor 2          │
│  ├── Partición 0      │  ├── Partición 2      │
│  └── Partición 1      │  └── Partición 3      │
└───────────────────────┴───────────────────────┘

```

&gt; ⚠️ **REGLA DE PARALELISMO**: Si tienes 4 particiones en un topic, el número máximo de consumidores activos en el grupo es **4**. Un quinto consumidor quedará en estado *idle* (inactivo) como respaldo.

### Algoritmos de Rebalanceo:

Cuando un consumidor se une, abandona o colapsa, ocurre un **Rebalanceo** para redistribuir las particiones:

1. **Eager Rebalance (Stop-the-World)**:  
  * Todos los consumidores pausan su lectura, liberan sus particiones asignadas y vuelven a solicitar la asignación completa. Produce pausas considerables en la ingesta.
2. **Cooperative Sticky Rebalance (Moderno)**:  
  * Rebalanceo incremental. Los consumidores continúan leyendo de las particiones no afectadas y solo se reasignan dinámicamente las particiones que sufrieron cambios.

### Parámetros Clave para Evitar Rebalanceos Falsos:

* `session.timeout.ms` (ej. 45000ms): Tiempo límite sin recibir *heartbeats* antes de considerar muerto a un consumidor.
* `max.poll.interval.ms` (ej. 300000ms): Tiempo máximo permitido entre llamadas a `.poll()`. Si el procesamiento de un batch de Python/Java tarda más de este tiempo, el broker asume que el consumidor colapsó y fuerza un rebalanceo.

---

## 🛠️ 3\. Semánticas de Entrega &amp; Exactly-Once Semantics (EOS)

| Semántica                                    | Descripción                                                                         | Configuración Típica                                            |
| -------------------------------------------- | ----------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| **At-Most-Once** (Como máximo una vez)       | Los datos se procesan pero pueden perderse. Nunca hay duplicados.                   | Auto-commit de offsets ANTES de procesar el registro.           |
| **At-Least-Once** (Al menos una vez)         | Los datos nunca se pierden, pero pueden procesarse duplicados si hay rebalanceo.    | Commit manual de offsets DESPUÉS de procesar con éxito.         |
| **Exactly-Once (EOS)** (Exactamente una vez) | Los datos se procesan exactamente una vez en todo el pipeline (Read-Process-Write). | Productores Transaccionales + `isolation.level=read_committed`. |

### El Protocolo Transaccional en Kafka (EOS)

Permite leer de un topic A, transformar el registro y escribir en un topic B garantizando que la escritura del mensaje y el commit del offset ocurran en una **única transacción atómica**:

1. El cliente inicia la transacción con un `transactional.id`.
2. El **Transaction Coordinator** en el broker escribe un registro en el topic interno `__transaction_state`.
3. Al finalizar, el cliente llama a `commitTransaction()`. Se escribe un marcador *Commit Marker* en los log segments.
4. Los consumidores leen en modo `isolation.level=read_committed` y solo ven mensajes cuyos marcadores hayan sido confirmados.

---

## ⚡ 4\. Manejo Defensivo de Errores: Retry Topics y Dead Letter Queue (DLQ)

Cuando un mensaje llega corrupto (*Poison Pill*) o falla la lógica de negocio, **reintentar indefinidamente bloquea el procesamiento de toda la partición**.

```
[ Topic Principal ] ───(Falla procesamiento)───&gt; [ Retry Topic (Delay Exponencial) ]
                                                              │
                                                   (Si supera max reintentos)
                                                              ▼
                                                 [ Dead Letter Queue (DLQ) ]
                                                 (Notifica a Alertas / SRE)

```

### Estrategia de Producción:

1. **Intento 1**: Procesamiento en el topic principal. Si falla, publicar en `topic.RETRY_1`.
2. **Intento 2**: Consumir de `topic.RETRY_1` con un delay de espera (ej. 5 segundos). Si vuelve a fallar, publicar en `topic.RETRY_2`.
3. **Fallo Definitivo**: Enviar el mensaje intacto con sus headers de error a `topic.DLQ` para análisis post-mortem e intervención manual.

---

## 🏋️‍♂️ Ejercicio Práctico Hands-On: Productor Idempotente y Consumidor Resiliente en Python

Crea el archivo `kafka_advanced_pipeline.py` usando `confluent-kafka` (librería basada en `librdkafka` C/C++):

```
import json
from confluent_kafka import Producer, Consumer, KafkaError

# 1. Configuración de Productor Idempotente de Alta Disponibilidad
producer_conf = {
    'bootstrap.servers': 'localhost:9092',
    'enable.idempotence': True,          # Activa PID y números de secuencia
    'acks': 'all',                        # Espera confirmación de todas las réplicas ISR
    'retries': 5,                        # Reintentos automáticos
    'max.in.flight.requests.per.connection': 5 # Garantiza orden manteniendo rendimiento
}

producer = Producer(producer_conf)

def delivery_report(err, msg):
    if err is not None:
        print(f"❌ Falló el envío del mensaje: {err}")
    else:
        print(f"✅ Mensaje entregado a {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")

# Enviar evento de prueba
payload = {"evento_id": "evt_9981", "monto": 1450.50, "moneda": "USD"}
producer.produce(
    topic="transacciones",
    key="evt_9981",
    value=json.dumps(payload),
    callback=delivery_report
)
producer.flush()

# 2. Configuración de Consumidor Resiliente (Cooperative Sticky + Read Committed)
consumer_conf = {
    'bootstrap.servers': 'localhost:9092',
    'group.id': 'fraude_processor_group',
    'auto.offset.reset': 'earliest',
    'enable.auto.commit': False,         # Commit manual defensivo
    'partition.assignment.strategy': 'cooperative-sticky', # Rebalanceo incremental
    'isolation.level': 'read_committed'  # Solo lee transacciones confirmadas (EOS)
}

consumer = Consumer(consumer_conf)
consumer.subscribe(['transacciones'])

print("\n🎧 Consumidor listo en modo 'read_committed'. Esperando mensajes...")
# Descomentar para bucle de lectura
# try:
#     while True:
#         msg = consumer.poll(timeout=1.0)
#         if msg is None: continue
#         if msg.error():
#             print(f"Error de lectura: {msg.error()}")
#             continue
#  
#         # Procesar negocio...
#         print(f"Procesado: {msg.value().decode('utf-8')}")
#         consumer.commit(asynchronous=False) # Commit manual exitoso
# finally:
#     consumer.close()

```

---

## 🧠 Checkpoint de Autoevaluación

1. ¿Cómo evita la propiedad `enable.idempotence=true` la duplicación de registros cuando un productor sufre una desconexión de red?
2. ¿Cuál es la ventaja fundamental del protocolo de rebalanceo *Cooperative Sticky* frente al enfoque *Eager* tradicional en un Consumer Group?
3. ¿Por qué es necesario configurar `isolation.level=read_committed` en los consumidores cuando se implementa *Exactly-Once Semantics* (EOS)?
4. ¿Qué es un *Poison Pill* en un stream de eventos y por qué el patrón *Dead Letter Queue* (DLQ) previene el bloqueo de la partición?