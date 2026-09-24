# 🏗️ Lección 01.B (Módulo 08): Infrastructure as Code (IaC) con Terraform para Plataformas de Datos

> **Propósito**: Dominar el aprovisionamiento declarativo de infraestructura en la nube para plataformas de datos utilizando **Terraform (HCL2)**, implementando gestión remota de estado con *State Locking*, módulos reutilizables para Data Lakes/Lakehouses, y patrones de seguridad e inmutabilidad de nivel producción.

---

## 📌 1. Paradigm Shift: De ClickOps a Infrastructure as Code (IaC)

En arquitecturas de datos tradicionales, la infraestructura se configuraba manualmente desde la consola del proveedor cloud (**ClickOps**). Este enfoque introduce vulnerabilidades críticas en entornos enterprise:

* **Deriva de Configuración (*Configuration Drift*)**: Cambios manuales no registrados que provocan discrepancias entre entornos (`dev`, `staging`, `prod`).
* **Falta de Trazabilidad y Auditoría**: Imposibilidad de saber quién modificó un bucket S3, una regla de IAM o el escalado de un clúster EMR/Databricks.
* **Incapacidad de Recuperación ante Desastres (DR)**: Reconstruir una plataforma de datos desde cero tras un fallo catastrófico puede tomar días.

```
❌ CLICKOPS (Manual):
[ Ingeniero ] ──> Clics en Consola AWS/GCP ──> Configuración no documentada ──> Drift & Errores

✅ IaC DECLARATIVO (Terraform):
[ Código HCL2 ] ──> [ Code Review / PR ] ──> [ CI/CD Plan & Apply ] ──> Infraestructura Reproducible
```

### Principios Clave de Terraform:
1. **Declarativo vs. Imperativo**: En lugar de escribir scripts paso a paso ("crea un bucket, luego agrega un rol"), describes el **estado final deseado** en HCL2 (*HashiCorp Configuration Language*). Terraform calcula el grafo de dependencias y la secuencia óptima de operaciones.
2. **Inmutabilidad**: La infraestructura no se modifica en caliente de forma desordenada; se actualiza o se reemplaza a través de código versionado en Git.

---

## 🔬 2. Arquitectura Interna de Terraform & Gestión del Estado (`tfstate`)

El archivo de estado (**`terraform.tfstate`**) es el corazón de Terraform. Mantiene el mapeo exacto entre los recursos declarados en tus archivos `.tf` y los recursos reales desplegados en la nube.

```
                  ┌──────────────────────────────┐
                  │   Archivos de Código (.tf)   │
                  └──────────────┬───────────────┘
                                 │
                                 ▼
┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│ terraform plan   │──>│  State Manager   │<──│ Provider API     │
│ (Calcula DAG de  │   │  (tfstate real)  │   │ (AWS / GCP / DB) │
│  diferencias)    │   └──────────────────┘   └──────────────────┘
└──────────────────┘
```

### El Peligro del Estado Local y la Necesidad de Remote Backend + Locking:
Si dos ingenieros ejecutan `terraform apply` simultáneamente trabajando con un archivo de estado local, el archivo se corromperá, destruyendo recursos o creando duplicados.

Para producción, es obligatorio configurar un **Remote Backend** con **State Locking**:
* **AWS**: S3 Bucket (almacenamiento encriptado del `.tfstate`) + DynamoDB Table (bloqueo de estado mediante *Partition Key* `LockID`).
* **GCP**: Google Cloud Storage (GCS) con prevención de concurrencia nativa.

```hcl
# backend.tf - Configuración del Backend Remoto Seguro
terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket         = "company-data-platform-tfstate-prod"
    key            = "infrastructure/data-lake/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-state-locks"
    encrypt        = true
  }
}
```

---

## 🛠️ 3. Aprovisionamiento Modular de Data Lakes (Bronze, Silver, Gold)

Un módulo de Terraform es un conjunto organizado de archivos HCL2 que encapsula recursos relacionados para promover la reutilización y estandarización.

### Estructura de Directorios Estándar de Producción:

```
terraform-data-platform/
├── modules/
│   └── s3_medallion_bucket/
│       ├── main.tf          # Definición de recursos S3
│       ├── variables.tf     # Parámetros de entrada
│       └── outputs.tf       # Valores exportados (ARNs, IDs)
└── environments/
    └── prod/
        ├── main.tf          # Invocación de módulos
        ├── backend.tf       # Estado remoto S3/DynamoDB
        ├── terraform.tfvars # Valores concretos de variables
        └── outputs.tf
```

### Reglas de Hardening para Buckets de Datos:
1. **Public Access Block**: Bloqueo absoluto de acceso público a nivel de API.
2. **SSE-KMS Encryption**: Cifrado en reposo con claves administradas por el cliente (KMS Customer Managed Keys).
3. **Bucket Versioning**: Habilitado para protección contra eliminaciones accidentales.
4. **Lifecycle Rules**: Transición automática de datos antiguos a clases de almacenamiento frías (S3 Glacier / GCS Coldline) para optimizar FinOps.

---

## 🏋️‍♂️ Ejercicio Práctico Hands-On: Módulo de Data Lake Medallion en AWS S3

Construiremos el código HCL2 listo para producción que aprovisiona las capas **Bronze, Silver y Gold** con cifrado KMS y bloqueo de acceso público.

### 1. `modules/s3_medallion_bucket/variables.tf`

```hcl
variable "bucket_name" {
  description = "Nombre globalmente único del bucket S3"
  type        = string
}

variable "environment" {
  description = "Entorno de despliegue (dev, staging, prod)"
  type        = string
}

variable "layer" {
  description = "Capa de la arquitectura Medallion (bronze, silver, gold)"
  type        = string
}

variable "kms_key_arn" {
  description = "ARN de la clave KMS para cifrado SSE-KMS"
  type        = string
}

variable "glacier_transition_days" {
  description = "Días para mover datos no actuales a S3 Glacier"
  type        = number
  default     = 90
}
```

### 2. `modules/s3_medallion_bucket/main.tf`

```hcl
# Bucket S3 Principal
resource "aws_s3_bucket" "this" {
  bucket        = var.bucket_name
  force_destroy = false # Previene eliminación accidental en producción

  tags = {
    Environment = var.environment
    Layer       = var.layer
    ManagedBy   = "Terraform"
  }
}

# Control de Versiones
resource "aws_s3_bucket_versioning" "this" {
  bucket = aws_s3_bucket.this.id
  versioning_configuration {
    status = "Enabled"
  }
}

# Cifrado SSE-KMS en Reposo
resource "aws_s3_bucket_server_side_encryption_configuration" "this" {
  bucket = aws_s3_bucket.this.id

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = var.kms_key_arn
      sse_algorithm     = "aws:kms"
    }
    bucket_key_enabled = true # Reduce costos de llamadas a KMS API en un 99%
  }
}

# Bloqueo de Acceso Público (Hardening)
resource "aws_s3_bucket_public_access_block" "this" {
  bucket = aws_s3_bucket.this.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Reglas de Ciclo de Vida (FinOps)
resource "aws_s3_bucket_lifecycle_configuration" "this" {
  bucket = aws_s3_bucket.this.id

  rule {
    id     = "archive-old-versions"
    status = "Enabled"

    noncurrent_version_transition {
      noncurrent_days = var.glacier_transition_days
      storage_class   = "GLACIER"
    }

    noncurrent_version_expiration {
      noncurrent_days = var.glacier_transition_days + 180
    }
  }
}
```

### 3. Invocación en `environments/prod/main.tf`

```hcl
provider "aws" {
  region = "us-east-1"
}

# Clave KMS dedicada para la Plataforma de Datos
resource "aws_kms_key" "data_lake_key" {
  description             = "KMS Key para cifrado del Data Lake Medallion"
  deletion_window_in_days = 30
  enable_key_rotation     = true

  tags = {
    Environment = "prod"
    ManagedBy   = "Terraform"
  }
}

# Instanciación de Capas Medallion
module "bronze_bucket" {
  source      = "../../modules/s3_medallion_bucket"
  bucket_name = "corp-data-lake-bronze-prod-us-east-1"
  environment = "prod"
  layer       = "bronze"
  kms_key_arn = aws_kms_key.data_lake_key.arn
}

module "silver_bucket" {
  source      = "../../modules/s3_medallion_bucket"
  bucket_name = "corp-data-lake-silver-prod-us-east-1"
  environment = "prod"
  layer       = "silver"
  kms_key_arn = aws_kms_key.data_lake_key.arn
}

module "gold_bucket" {
  source      = "../../modules/s3_medallion_bucket"
  bucket_name = "corp-data-lake-gold-prod-us-east-1"
  environment = "prod"
  layer       = "gold"
  kms_key_arn = aws_kms_key.data_lake_key.arn
}
```

---

## 🧠 Checkpoint de Autoevaluación

1. ¿Por qué el enfoque *Declarativo* de Terraform es superior a los scripts *Imperativos* para la gestión de infraestructura de datos?
2. ¿Qué ocurre si dos pipelines de CI/CD ejecutan `terraform apply` al mismo tiempo sobre un estado remoto sin tabla de *State Locking*?
3. ¿Por qué la propiedad `bucket_key_enabled = true` en la configuración de cifrado S3 es una práctica recomendada de FinOps?
4. ¿Cuál es el propósito de separar el código en *Módulos* reutilizables frente a escribir un único archivo `.tf` gigante?

---

🚀 ¿Avanzamos con la **`modulo_08_leccion_02_B`** (*Arquitectura Cloud & Seguridad IAM: Principle of Least Privilege, Roles de Servicio, S3/GCS Bucket Policies y patrones Serverless*)?
