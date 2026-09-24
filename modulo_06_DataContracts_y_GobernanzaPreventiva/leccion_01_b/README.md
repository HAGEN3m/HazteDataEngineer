# ☕ Lección 01.B (Módulo 06): Arquitectura Interna de Apache Kafka: Topics, Particiones, Log Segments y KRaft

&gt; **Propósito**: Comprender a fondo la arquitectura física y lógica de **Apache Kafka**, explorando el diseño de *Commit Log* inmutable append-only, la estructura de *Log Segments* e índices en disco, la transferencia de datos *Zero-Copy* mediante la llamada de sistema `sendfile()`, el protocolo de consenso **KRaft** y los parámetros críticos de replicación y durabilidad (`acks=all`, `min.insync.replicas`).

---

## 📌 1\. Event Streaming vs Message Queues Tradicionales

A diferencia de los Message Brokers tradicionales (como RabbitMQ o ActiveMQ), que eliminan los mensajes una vez que son consumidos (*Destructive Read*), **Apache Kafka** está diseñado como un **Distributed Commit Log** inmutable y persistente.

```
Message Broker Tradicional (RabbitMQ):
[Productor] ──&gt; [Queue] ──&gt; [Consumidor A] (El mensaje se borra tras ACK)

Apache Kafka (Distributed Commit Log):
[Productor] ──&gt; [Topic Partition Log (Inmutable Append-Only)]
                      ├── [Offset 0: Evento A] ──&gt; Consumidor 1 (Puntero Offset = 0)
                      ├── [Offset 1: Evento B] ──&gt; Consumidor 2 (Puntero Offset = 1)
                      └── [Offset 2: Evento C] (Persistido en disco según retención)

```

### Principios Fundamentales de Kafka:

1. **Publicación y Subscripción Múltiple**: Múltiples aplicaciones consumidoras independientes pueden leer el mismo flujo de datos a sus propios ritmos sin interferir entre sí.
2. **Rebobinado de Punteros (*Offset Replay*)**: Dado que los datos no se borran al consumirse, un consumidor puede volver a leer eventos pasados cambiando su *Offset*.
3. **Escalabilidad Horizontal**: Los *Topics* se dividen en **Particiones** distribuidas entre múltiples *Brokers* (nodos del clúster).

---

## 🔬 2\. Estructura Física en Disco: Log Segments y Sparse Indexes

En el sistema de archivos del servidor (*Broker*), cada partición de un Topic se representa como un directorio conteniendo una secuencia de archivos llamados **Log Segments**.

```
/var/lib/kafka/data/ventas-eventos-0/
├── 00000000000000000000.log        &lt;-- Datos binarios de los mensajes (Payload)
├── 00000000000000000000.index      &lt;-- Sparse Index (Offset -&gt; Posición física en bytes)
├── 00000000000000000000.timeindex  &lt;-- Timestamp Index (Timestamp -&gt; Offset)
└── leader-epoch-checkpoint

```

### Búsqueda de Mensajes con Índices Dispersos (*Sparse Indexes*):

Para no cargar índices gigantescos en memoria RAM, Kafka utiliza **Sparse Indexes**: guarda una entrada en el archivo `.index` solo cada N bytes de datos (configurable vía `index.interval.bytes`).

1. Para buscar el mensaje con `Offset = 10500`, Kafka realiza una **búsqueda binaria** $O(\\log N)$ en el archivo `.index`.
2. Encuentra la entrada de Offset más cercana (ej. `Offset 10000 -&gt; Byte 409600`).
3. Va directamente a la posición física `409600` del archivo `.log` y realiza una lectura secuencial rápida hasta dar con el registro exacto.

---

## ⚡ 3\. Cero-Copia (*Zero-Copy*) y Rendimiento I/O Extremo

¿Cómo logra Kafka transferir gigabytes por segundo con bajo consumo de CPU? La respuesta reside en la llamada de sistema de Linux `sendfile()`.

```
❌ Transferencia Tradicional (4 Copias de Memoria + 4 Cambios de Contexto):
Disco ──&gt; Kernel Page Cache ──&gt; JVM User Space ──&gt; Socket Buffer ──&gt; Tarjeta NIC

✅ Transferencia Zero-Copy con sendfile() (0 Copias en User Space):
Disco ──&gt; Kernel Page Cache ───────────────────────────────────────&gt; Tarjeta NIC

```

Al enviar datos a los consumidores, Kafka **no copia los mensajes a la memoria de la JVM**. Le ordena al Kernel de Linux que transfiera los datos directamente desde el *Page Cache* del sistema operativo hacia la tarjeta de red (*NIC*), reduciendo drásticamente la latencia y la presión sobre el Garbage Collector.

---

## 🛡️ 4\. Replicación, Durabilidad y el Protocolo KRaft

Para garantizar alta disponibilidad sin pérdida de datos ante caídas de nodos, Kafka distribuye las particiones en esquemas **Leader / Follower**:

```
           [ PRODUCER (acks=all) ]
                      │
                      ▼
            [ Leader Replica ] (Broker 1)
             /               \
 (Replicación Async/Sync)     \
           ▼                   ▼
[ Follower 1 ] (Broker 2)  [ Follower 2 ] (Broker 3)

```

### Parámetros de Durabilidad Críticos para Producción:

* **`acks=all` (`acks=-1`)**: El Productor no considera enviado el mensaje hasta que el *Leader* y **todas las réplicas en sincronía (ISR)** hayan escrito el registro en su log.
* **`min.insync.replicas`**: Número mínimo de réplicas que deben confirmar la escritura (ej. `2` en un clúster de 3 nodos).
* **`unclean.leader.election.enable=false`**: Impide que una réplica desincronizada sea elegida como nuevo Líder si el Líder actual cae, evitando pérdida de datos (*Data Loss*).

### Evolución de la Arquitectura: De ZooKeeper a KRaft

Anteriormente, Kafka dependía de **Apache ZooKeeper** para gestionar el estado del clúster. En las versiones modernas, Kafka utiliza **KRaft** (*Kafka Raft Metadata Mode*), un protocolo de consenso interno basado en Raft que permite escalar a millones de particiones sin cuellos de botella externos.

---

## 🧹 5\. Políticas de Limpieza: Retention vs. Log Compaction

Kafka ofrece dos políticas de limpieza de datos (`cleanup.policy`):

1. **`cleanup.policy=delete` (Por defecto)**:  
  * Elimina segmentos antiguos según tiempo (`log.retention.hours=168`) o espacio (`log.retention.bytes`).
2. **`cleanup.policy=compact` (Log Compaction)**:  
  * Garantiza conservar **al menos el último valor conocido para cada clave (Key)** dentro de la partición. Ideal para tablas de estado (*Key-Value Stores*), agregaciones y arquitecturas Event-Driven.
  * Si se envía un mensaje con una clave existente y valor `null` (*Tombstone*), la compactación eliminará eventualmente esa clave.

---

## 🏋️‍♂️ Ejercicio Práctico Hands-On: Simulación de Productor y Consumidor con Control de Offsets

Crea el script `kafka_internals_demo.py` para simular el comportamiento de asignación de clave/partición y commit de offsets:

```
import hashlib
import time
from typing import NamedTuple, List, Dict

class Evento(NamedTuple):
    key: str
    value: str
    timestamp: float

class SimuladorParticionKafka:
    def __init__(self, partition_id: int):
        self.partition_id = partition_id
        self.log: List[Evento] = []
        self.offset_index: Dict[int, int] = {} # Simulación de Sparse Index (Offset -&gt; Index)

    def append(self, evento: Evento) -&gt; int:
        offset = len(self.log)
        self.log.append(evento)
        if offset % 2 == 0: # Sparse Index cada 2 registros
            self.offset_index[offset] = len(self.log) - 1
        return offset

def obtener_particion(key: str, num_partitions: int) -&gt; int:
    """Simula el Default Partitioner de Kafka basado en MurmurHash2/MD5"""
    hash_bytes = hashlib.md5(key.encode('utf-8')).digest()
    hash_int = int.from_bytes(hash_bytes[:4], byteorder='big')
    return hash_int % num_partitions

# 1. Inicializar clúster simulado de 3 particiones
NUM_PARTITIONS = 3
particiones = [SimuladorParticionKafka(i) for i in range(NUM_PARTITIONS)]

# 2. Producir eventos con claves de negocio
eventos_input = [
    ("cliente_101", "TRANSACCION_INICIAL"),
    ("cliente_202", "TRANSACCION_INICIAL"),
    ("cliente_101", "ACTUALIZACION_SALDO"),
    ("cliente_303", "TRANSACCION_INICIAL"),
    ("cliente_101", "CIERRE_CUENTA"),
]

print("=== 🚀 PRODUCIONALIZANDO EVENTOS Y ASIGNACIÓN DE PARTICIÓNS ===")
for key, payload in eventos_input:
    part_idx = obtener_particion(key, NUM_PARTITIONS)
    evt = Evento(key=key, value=payload, timestamp=time.time())
    offset_asignado = particiones[part_idx].append(evt)
    print(f"Key: '{key}' -&gt; Partición: {part_idx} | Offset Asignado: {offset_asignado}")

print("\n=== 🔍 ESTADO FÍSICO DE LAS PARTICIÓNS (SIMULADO) ===")
for p in particiones:
    print(f"\n--- Partición {p.partition_id} (Total Mensajes: {len(p.log)}) ---")
    for idx, msg in enumerate(p.log):
        print(f"  [Offset {idx}] Key: {msg.key} | Value: {msg.value}")
    print(f"  Sparse Index Entries: {p.offset_index}")

```

---

## 🧠 Checkpoint de Autoevaluación

1. ¿Por qué la arquitectura de *Commit Log* inmutable de Kafka permite que múltiples consumidores lean el mismo Topic sin destruir datos?
2. Explica cómo la llamada de sistema `sendfile()` de Linux (*Zero-Copy*) optimiza la transferencia de datos desde el disco hacia los clientes consumidores.
3. ¿Qué ocurre con la disponibilidad de escrituras si un Topic está configurado con `acks=all`, `min.insync.replicas=2` y 2 de sus 3 réplicas caen repentinamente?
4. ¿Cuál es la diferencia entre la política de retención `delete` y `compact` (`Log Compaction`) en Apache Kafka?