# 💰 Lección 04.B (Módulo 08): FinOps &amp; Optimización de Costos Cloud: Instancias Spot/Graviton, S3 Lifecycle Policies, Partitioning/Clustering en BigQuery y Estimación de Costos

&gt; **Propósito**: Dominar los principios de **FinOps (Financial Operations)** aplicados a la Ingeniería de Datos. Aprenderás a diseñar pipelines y arquitecturas Data Lake/Lakehouse en la nube (AWS/GCP) optimizadas para el rendimiento y el costo, reduciendo hasta un 70% la factura cloud mediante instancias Graviton/Spot, políticas avanzadas de ciclo de vida de almacenamiento, particionamiento/clustering en Data Warehouses y monitoreo continuo de costos.

---

## 📌 1\. Principios de FinOps en Data Engineering

Tradicionalmente, la ingeniería de datos se enfocaba en la velocidad de cómputo y la latencia. En la era cloud moderna, **el costo es una métrica de diseño de primer nivel** (*Cost as a First-Class Metric*).

```
                    ┌─────────────────────────┐
                    │     Cultura FinOps      │
                    │  (Inform -&gt; Optimize)   │
                    └────────────┬────────────┘
                                 │
         ┌───────────────────────┴───────────────────────┐
         ▼                                               ▼
┌─────────────────────────────────┐             ┌─────────────────────────────────┐
│     Optimización de Cómputo     │             │  Optimización de Almacenamiento │
│  • Graviton (ARM) vs x86        │             │  • S3 Intelligent-Tiering/Glacier│
│  • Spot / Preemptible VMs       │             │  • Abort Incomplete Multipart   │
│  • Auto-termination de Clúster  │             │  • Compactación (Small Files)   │
└─────────────────────────────────┘             └─────────────────────────────────┘
                                 │
                                 ▼
                ┌─────────────────────────────────┐
                │   Optimización Data Warehouse   │
                │  • Partitioning + Clustering    │
                │  • Bytes Scanned Reduction      │
                │  • Slot Reservations / Auto-sus │
                └─────────────────────────────────┘

```

### La Rueda FinOps (Inform, Optimize, Operate):

1. **Inform (Visibilidad)**: Asignación precisa de costos mediante etiquetado obligatorio (`Environment`, `Team`, `PipelineID`, `CostCenter`). Sin *Tags*, no se puede medir el ROI de un pipeline.
2. **Optimize (Reducción de Desperdicio)**: Elección adecuada del tamaño de infraestructura (*Right-sizing*), aprovechamiento de descuentos por compromiso (Reserved Instances / Savings Plans) e instancias efímeras.
3. **Operate (Gobernanza Continua)**: Establecimiento de presupuestos (*Budgets*), alertas automatizadas de anomalías en consumo y *Circuit Breakers* de costos.

---

## ⚡ 2\. Optimización de Cómputo: ARM (Graviton), Spot Instances &amp; Auto-termination

El cómputo (Spark en EMR/Databricks, Dataflow, EC2, Kubernetes) suele representar entre el **60% y el 80%** del costo total de una infraestructura de datos.

### A. Procesadores ARM (AWS Graviton3 / Graviton4 vs. x86)

* **Ventaja**: Las instancias basadas en arquitectura ARM (ej. `m6g`, `c7g`, `r7g`) ofrecen habitualmente hasta un **20% menor costo** por hora y hasta un **40% mejor relación precio/rendimiento** que las instancias x86 equivalentes (`m5`, `c5`).
* **Implementación en Spark**: PySpark y los motores modernos de ejecución (JVM, Arrow, DuckDB) son completamente compatibles con ARM. Cambiar el tipo de nodo de un clúster EMR o Databricks a instancias Graviton es una ganancia directa e inmediata de costo.

### B. Instancias Spot (AWS) / Preemptible VMs (GCP)

Las instancias Spot ofrecen excedentes de capacidad cloud con descuentos de hasta un **70% - 90%** respecto al precio On-Demand, a cambio de la posibilidad de que la nube interrumpa la instancia con un aviso previo de 2 minutos.

```
       ESTRATEGIA DEFENSIVA EN CLÚSTERES SPARK (EMR/Databricks):

       ┌────────────────────────────────────────────────────────┐
       │ DRIVER NODE (Stateful)                                 │
       │  • Tipo: On-Demand / Reserved Instance                 │
       │  • Razón: Si cae el Driver, el Job entero muere.       │
       └────────────────────────────────────────────────────────┘
                                 │
       ┌─────────────────────────┴──────────────────────────────┐
       │                                                        │
       ▼                                                        ▼
┌───────────────────────────────────────┐    ┌───────────────────────────────────────┐
│ CORE NODES (HDFS / Local Storage)     │    │ TASK NODES (Stateless Computation)    │
│  • Tipo: On-Demand o Spot diversificado│    │  • Tipo: 100% Spot Instances          │
│  • Razón: Mantienen bloques de estado.│    │  • Razón: Solo ejecutan Tasks; si     │
│                                       │    │    caen, Spark reasigna la Task.     │
└───────────────────────────────────────┘    └───────────────────────────────────────┘

```

### C. Auto-termination (Apagado por Inactividad)

Un error clásico en entornos de desarrollo o ad-hoc es dejar clústeres de Spark o Data Warehouses encendidos 24/7 sin procesar datos.

* **Regla de Producción**: Configurar *Auto-termination* automático tras **15-20 minutos** de inactividad de CPU/Jobs.

---

## 📦 3\. Optimización de Almacenamiento: S3 Lifecycle Policies &amp; Small Files

Aunque el almacenamiento en S3/GCS es económico ($0.023/GB/mes en S3 Standard), a escala de Petabytes o con millones de archivos pequeños, los costos de almacenamiento y llamadas a la API (GET, LIST, PUT) se disparan.

### A. Jerarquía de Clases de Almacenamiento en S3:

1. **S3 Standard**: Acceso frecuente (Bronze caliente, Silver/Gold activo).
2. **S3 Intelligent-Tiering**: Monitoriza patrones de acceso y mueve automáticamente objetos entre capas de acceso frecuente, infrecuente ($0.0125/GB) y archivo sin penalizaciones de recuperación. Ideal para Data Lakes con accesos impredecibles.
3. **S3 Glacier Instant / Flexible / Deep Archive**: Almacenamiento en frío para retención regulatoria/auditoría ($0.00099/GB/mes en Deep Archive, \~95% más barato que Standard).

### B. El Peligro Oculto: Incomplete Multipart Uploads

Cuando un pipeline escribe un archivo grande o un job de Spark interrumpe una escritura en S3 mediante *Multipart Upload*, las partes subidas parcialmente quedan almacenadas ocupando espacio y facturando mensualmente de forma invisible.

* **Solución**: Configurar la regla `AbortIncompleteMultipartUpload` a los **7 días** en todos los buckets.

### C. Impacto del "Small File Problem" en Costos API

Subir 1,000,000 de archivos de 1 KB cuesta lo mismo en almacenamiento que 1 archivo de 1 GB, pero genera **1,000,000 de llamadas `PUT/LIST`** (hasta $5 USD por millón de peticiones) y destruye el rendimiento de lectura.

* **Solución**: Proceso diario de compactación (`OPTIMIZE` / Bin-packing) para empaquetar datos en archivos Parquet/Delta de 128 MB - 512 MB.

---

## 📊 4\. Optimización de Data Warehouses: BigQuery &amp; Snowflake

En Data Warehouses Serverless como Google BigQuery, el modelo de cobro por defecto se basa en **Bytes Escaneados** ($6.25 USD por TB escaneado). Un `SELECT *` sobre una tabla sin particionar puede costar cientos de dólares en una sola consulta.

### A. Particionamiento + Clustering en BigQuery

```
-- ❌ CONSULTA INEFICIENTE (Escanea toda la tabla de 2 TB -&gt; ~$12.50 USD):
SELECT user_id, SUM(amount)
FROM `my_project.analytics.raw_events`
WHERE event_date = '2026-09-24';

-- ✅ TABLA OPTIMIZADA CON PARTITION BY event_date Y CLUSTER BY user_id:
-- Solo escanea la partición del día (2 GB -&gt; ~$0.01 USD) -&gt; 99.9% DE AHORRO.
CREATE TABLE `my_project.analytics.partitioned_events`
PARTITION BY event_date
CLUSTER BY user_id AS
SELECT * FROM `my_project.analytics.raw_events`;

```

### B. Reglas de Oro para FinOps en Warehouses:

1. **Nunca usar `SELECT *`**: Seleccionar únicamente las columnas strictly necesarias para reducir el volumen de datos leídos.
2. **Usar Vistas Materializadas o Tablas Pre-agregadas**: Evitar recalcular agregaciones pesadas sobre miles de millones de filas en cada dashboard.
3. **Límites de Bytes Escaneados (*Cost Controls*)**: Configurar el parámetro `maximum_bytes_billed` en consultas o definir límites diarios de cuotas por usuario/proyecto.
4. **Snowflake Auto-suspend**: Configurar el auto-suspend de los Virtual Warehouses en **60 segundos** para no pagar cómputo ocioso.

---

## 🏋️‍♂️ Ejercicio Práctico Hands-On: Infraestructura FinOps con Terraform y Script de Auditoría

A continuación, implementaremos una política de ciclo de vida en S3 optimizada para costos con Terraform y un script en Python para auditar automáticamente buckets buscando partes incompletas y archivos pequeños.

### 1\. Configuración de S3 Lifecycle Policy en Terraform (`finops_s3.tf`):

```
# Configuración del Bucket Data Lake con estrategia de costos
resource "aws_s3_bucket" "data_lake_finops" {
  bucket = "company-data-lake-finops-prod"

  tags = {
    Environment = "Production"
    DataLayer   = "Medallion"
    CostCenter  = "DataEngineering-101"
    ManagedBy   = "Terraform"
  }
}

# Regla de Ciclo de Vida para Reducción Automática de Costos
resource "aws_s3_bucket_lifecycle_configuration" "finops_lifecycle" {
  bucket = aws_s3_bucket.data_lake_finops.id

  # Regla 1: Limpieza de Multipart Uploads Incompletos (Ahorro directo)
  rule {
    id     = "abort-incomplete-multipart-uploads"
    status = "Enabled"

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }

  # Regla 2: Transición de capas Bronze/Silver antiguas a capas frías
  rule {
    id     = "medallion-storage-tiering"
    status = "Enabled"

    filter {
      prefix = "bronze/"
    }

    # Transición a Intelligent-Tiering tras 30 días
    transition {
      days          = 30
      storage_class = "INTELLIGENT_TIERING"
    }

    # Transición a Glacier Deep Archive tras 90 días
    transition {
      days          = 90
      storage_class = "DEEP_ARCHIVE"
    }

    # Expiración/Borrado definitivo de datos temporales tras 365 días
    expiration {
      days = 365
    }
  }
}

```

### 2\. Script Python de Auditoría FinOps (`finops_auditor.py`):

```
import boto3
from datetime import datetime, timezone, timedelta

def audit_s3_bucket_costs(bucket_name: str):
    """Audita un bucket S3 en busca de ineficiencias de costos (Multipart Uploads)."""
    s3_client = boto3.client('s3')
    print(f"🔍 Iniciando auditoría FinOps en bucket: {bucket_name}\n")

    # 1. Auditoría de Incomplete Multipart Uploads
    try:
        mpu_response = s3_client.list_multipart_uploads(Bucket=bucket_name)
        uploads = mpu_response.get('Uploads', [])

        if not uploads:
            print("✅ No se encontraron Multipart Uploads incompletos pendíentes.")
        else:
            total_waste_bytes = 0
            print(f"⚠️ Se encontraron {len(uploads)} subidas incompletas:")
            for upload in uploads:
                key = upload['Key']
                upload_id = upload['UploadId']
                initiated = upload['Initiated']

                print(f"   - Archivo: {key} | Iniciado: {initiated} | UploadId: {upload_id[:12]}...")

            print("\n💡 Recomendación: Activar 'abort_incomplete_multipart_upload' en Terraform.")

    except Exception as e:
        print(f"❌ Error consultando multipart uploads: {e}")

if __name__ == "__main__":
    # Simulación de auditoría (Reemplazar con bucket real)
    audit_s3_bucket_costs("company-data-lake-finops-prod")

```

---

## 🧠 Checkpoint de Autoevaluación

1. ¿Cuáles son los tres pilares del marco de trabajo FinOps y cómo se aplican a la ingeniería de datos?
2. ¿Por qué el uso de instancias **Graviton (ARM)** y **Task Nodes Spot** en Spark reduce drásticamente el costo de ejecución sin arriesgar la estabilidad del Job?
3. ¿Qué peligro representan las cargas multipartes incompletas (*Incomplete Multipart Uploads*) en S3 y cómo se mitiga con Terraform?
4. ¿Cómo reducen el costo de consulta en BigQuery el **Particionamiento** y el **Clustering** combinados?