# 🛡️ Lección 02.B (Módulo 08): Arquitectura Cloud &amp; Seguridad IAM: Principle of Least Privilege, Roles de Servicio, S3/GCS Bucket Policies y Patrones Serverless

&gt; **Propósito**: Dominar los patrones de arquitectura en la nube con un enfoque defensivo (*Security-First*), aplicando el Principio de Menor Privilegio (*Principle of Least Privilege - PoLP*), la autenticación sin llaves estáticas vía OIDC/Roles de servicio, politicas defensivas de S3/GCS y patrones de ingesta/procesamiento serverless para Data Lakes de producción.

---

## 📌 1\. Identity &amp; Access Management (IAM) &amp; Principle of Least Privilege (PoLP)

En arquitectura de datos moderna, la seguridad no es una capa superficial; es la columna vertebral de la infraestructura. El vector de ataque y fuga de información más común en Data Lakes no son los exploits complejos de software, sino **credenciales estáticas expuestas** (`AWS_ACCESS_KEY_ID` / `SECRET_ACCESS_KEY`) o políticas IAM demasiado permisivas (`Action: "*", Resource: "*"`).

### ❌ El Antipatrón de las Llaves Estáticas

Guardar Access Keys en archivos `.env`, secretos de GitHub Actions o variables de entorno de orquestadores presenta riesgos severos:

* **Fuga involuntaria**: Inclusión accidental en repositorios Git públicos o logs de ejecución.
* **Falta de rotación**: Las llaves permanentes rara vez se rotan automáticamente.
* **Imposibilidad de auditoría granular**: Dificulta rastrear qué proceso específico realizó una acción no autorizada.

### ✅ Autenticación Basada en Roles &amp; OIDC (OpenID Connect)

En lugar de llaves estáticas, la arquitectura moderna utiliza **Federación de Identidad y Roles Asumibles**:

```
[ GitHub Actions / Kubernetes / Airflow ]
                 │
                 ▼ (1. Solicita Token JWT firmado)
     [ ID Provider (OIDC) ]
                 │
                 ▼ (2. Presenta JWT al Cloud STS)
    [ AWS STS / GCP Workload Identity ]
                 │
                 ▼ (3. Retorna Credenciales Temporales - Válidas 1h)
   [ Acceso a S3 / Glue / BigQuery / Redshift ]

```

* **AWS STS (`AssumeRoleWithWebIdentity`)**: Otorga tokens de seguridad temporales con vida útil limitada (ej. 15 a 60 minutos).
* **GCP Workload Identity Federation**: Permite a cargas de trabajo externas (ej. GitHub Actions o pods en Kubernetes) autenticarse ante Google Cloud sin descargar claves de cuenta de servicio (`service-account-key.json`).

---

## 🔒 2\. Hardening de S3/GCS: Bucket Policies, Cifrado KMS y VPC Endpoints

El almacenamiento de objetos es el corazón del Lakehouse. Garantizar que ningún dato pueda ser leído o alterado sin autorización requiere tres capas de hardening defensivo:

### A. Cifrado Obligatorio en Tránsito y Reposo

1. **En Tránsito (TLS 1.3)**: Todas las solicitudes deben viajar encriptadas vía HTTPS. Las llamadas HTTP no cifradas deben ser explícitamente denegadas por el Bucket Policy.
2. **En Reposo (SSE-KMS / CMK)**: Cifrado en el servidor utilizando llaves administradas por el cliente (*Customer Managed Keys - CMK*) en AWS KMS o Cloud KMS.

### B. Restricción de Red vía VPC Endpoints

Para evitar que los datos viajen por el Internet público al comunicarse entre la red privada (VPC) y S3/GCS, se configuran **VPC Endpoints (Gateway Endpoints)**.

```
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyAccessOutsideVPC",
      "Effect": "Deny",
      "Principal": "*",
      "Action": "s3:*",
      "Resource": [
        "arn:aws:s3:::medallion-lake-prod-gold",
        "arn:aws:s3:::medallion-lake-prod-gold/*"
      ],
      "Condition": {
        "StringNotEquals": {
          "aws:sourceVpce": "vpce-0123456789abcdef0"
        }
      }
    }
  ]
}

```

---

## ⚡ 3\. Patrones de Ingesta y Procesamiento Serverless

Para minimizar el costo operativo de mantener servidores encendidos 24/7 (*EC2 / Compute Engine*), los Data Engineers utilizan arquitecturas basadas en eventos (*Event-Driven Serverless*).

```
[ Fuente de Datos ] ──&gt; [ S3 Bucket (Bronze) ]
                               │
                               ▼ (Event Notification)
                        [ Amazon EventBridge ]
                               │
                               ▼
                       [ AWS SQS / DLQ ]
                               │
                               ▼
                        [ AWS Lambda ]
                               │
                               ▼
                     [ AWS Glue / EMR Serverless ]

```

### Componentes Clave:

1. **S3 Event Notifications + EventBridge**: Captura la llegada de un nuevo archivo (`ObjectCreated`) y emite un evento en milisegundos.
2. **SQS + Dead Letter Queue (DLQ)**: Actúa como un búfer para absorber picos de tráfico y aislar eventos que fallen durante el procesamiento.
3. **AWS Lambda / Cloud Functions**: Micro-cómputo ideal para archivos pequeños/medianos (&lt; 15 minutos de ejecución, validación de schemas o conversión ligera a Parquet).
4. **AWS Glue / Databricks Serverless**: Motores Spark sin servidor para transformar automáticamente grandes volúmenes de datos en las capas Silver y Gold.

---

## 🏋️‍♂️ Ejercicio Práctico Hands-On: Infraestructura IAM &amp; Bucket Policy Defensiva

A continuación implementamos una **Bucket Policy Defensiva** completa en formato JSON y una **Política IAM de Menor Privilegio** para un rol de procesamiento de ETL:

### 1\. Bucket Policy Defensiva (Deniega HTTP no cifrado y exige KMS)

```
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "EnforceTLSRequestsOnly",
      "Effect": "Deny",
      "Principal": "*",
      "Action": "s3:*",
      "Resource": [
        "arn:aws:s3:::company-datalake-silver-prod",
        "arn:aws:s3:::company-datalake-silver-prod/*"
      ],
      "Condition": {
        "Bool": {
          "aws:SecureTransport": "false"
        }
      }
    },
    {
      "Sid": "DenyUnEncryptedObjectUploads",
      "Effect": "Deny",
      "Principal": "*",
      "Action": "s3:PutObject",
      "Resource": "arn:aws:s3:::company-datalake-silver-prod/*",
      "Condition": {
        "StringNotEquals": {
          "s3:x-amz-server-side-encryption": "aws:kms"
        }
      }
    }
  ]
}

```

### 2\. Política IAM de Menor Privilegio para ETL Spark/Glue

```
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ReadBronzeWriteSilverOnly",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::company-datalake-bronze-prod",
        "arn:aws:s3:::company-datalake-bronze-prod/*"
      ]
    },
    {
      "Sid": "WriteSilverBucketOnly",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::company-datalake-silver-prod",
        "arn:aws:s3:::company-datalake-silver-prod/*"
      ]
    },
    {
      "Sid": "KMSAccessForDecryptionAndEncryption",
      "Effect": "Allow",
      "Action": [
        "kms:Decrypt",
        "kms:GenerateDataKey"
      ],
      "Resource": "arn:aws:kms:us-east-1:123456789012:key/a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d"
    }
  ]
}

```

---

## 🧠 Checkpoint de Autoevaluación

1. ¿Por qué el uso de llaves estáticas (`Access Keys`) se considera un grave riesgo de seguridad en pipelines de ingeniería de datos?
2. ¿Cómo funciona la autenticación por OIDC en herramientas de CI/CD para interactuar con la nube sin guardar credenciales en el repositorio?
3. ¿Qué condición en una Bucket Policy de S3 garantiza que los datos solo puedan transmitirse utilizando conexiones cifradas TLS (HTTPS)?
4. ¿Qué beneficio aporta un VPC Gateway Endpoint en la comunicación entre instancias EC2/EKS y un bucket S3?