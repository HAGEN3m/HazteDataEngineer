# 🐍 Lección 39: Arquitectura y Modularización de Pipelines ETL/ELT en Python

En las lecciones anteriores del **Bloque 4** aprendimos a trabajar con formatos columnares (Parquet), consumir APIs defensivamente, realizar ingestas masivas en SQL y transformar datos a alta velocidad con Pandas y Polars.

Sin embargo, cuando estos componentes crecen en proyectos reales, existe la tentación de escribir un único script monolítico de 2,000 líneas (`pipeline_final.py`). En producción, los scripts monolíticos son difíciles de mantener, imposibles de testear unitariamente y frágiles ante cambios de requerimientos.

En esta lección aprenderemos a diseñar e implementar una **Arquitectura Modular de Software** para pipelines ETL/ELT[1][2].

---

## 1\. Scripts Monolíticos vs. Arquitectura Modular

Aplicando el **Principio de Responsabilidad Única (** **Single Responsibility Principle** **)**, cada módulo o clase de nuestro proyecto debe cumplir un único propósito bien definido:

```
┌────────────────────────────────────────────────────────┐
│                      main.py                           │  &lt;-- Entrypoint / Orquestador
└───────┬───────────────────┬────────────────────┬───────┘
        │                   │                    │
        ▼                   ▼                    ▼
┌───────────────┐   ┌────────────────┐   ┌───────────────┐
│ Extractor     │   │ Transformer    │   │ Loader        │  &lt;-- Módulos Desacoplados
│ (API / S3)    │   │ (Polars)       │   │ (Postgres)    │
└───────────────┘   └────────────────┘   └───────────────┘

```

### Ventajas de la Modularización:

* **Mantenibilidad**: Si la API externa cambia el formato de autenticación, solo modificás la clase `Extractor`, sin tocar la lógica de transformación ni la base de datos.
* **Testeabilidad**: Podés escribir pruebas unitarias con `pytest`[2] para las transformaciones pasando DataFrames de prueba, sin necesidad de conectarte a la base de datos real.
* **Reutilización**: Los componentes de extracción o carga pueden reutilizarse en múltiples pipelines de la organización.

---

## 2\. Estructura Estándar de Carpetas para un Proyecto ETL/ELT

La jerarquía recomendada en proyectos profesionales de Ingeniería de Datos es la siguiente:

```
mi_pipeline_etl/
├── config/
│   ├── __init__.py
│   └── settings.py          &lt;-- Definición de variables de entorno y dataclasses
├── src/
│   ├── __init__.py
│   ├── extractors.py        &lt;-- Clases para la ingesta (APIs, SQL, Files)
│   ├── transformers.py      &lt;-- Lógica de negocio (Polars / Pandas)
│   ├── loaders.py           &lt;-- Clases para la persistencia (DB, Data Lake)
│   └── utils.py             &lt;-- Configuración de logging y decoradores
├── tests/
│   ├── test_transformers.py &lt;-- Pruebas unitarias
│   └── test_extractors.py
├── .env.example             &lt;-- Plantilla de configuración
├── .gitignore
├── requirements.txt         &lt;-- Dependencias del proyecto
└── main.py                  &lt;-- Punto de entrada principal (Orquestación)

```

---

## 3\. Configuración Centralizada con `@dataclass` y Variables de Entorno

Evitá *hardcodear* credenciales o rutas en tus clases. Utilizá **dataclass** e **os.getenv** para cargar la configuración de forma centralizada, fuertemente tipada e inmutable:

```
# config/settings.py
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class DatabaseConfig:
    db_uri: str = os.getenv("DATABASE_URL", "sqlite:///:memory:")
    chunk_size: int = int(os.getenv("DB_CHUNK_SIZE", "5000"))

@dataclass(frozen=True)
class APIConfig:
    base_url: str = os.getenv("API_BASE_URL", "https://api.ejemplo.com/v1")
    api_key: str = os.getenv("API_KEY", "")
    timeout_segundos: float = 10.0

@dataclass(frozen=True)
class PipelineConfig:
    db: DatabaseConfig = DatabaseConfig()
    api: APIConfig = APIConfig()

```

---

## 4\. Diseño Desacoplado de Componentes (Extractor, Transformer, Loader)

A continuación construimos las tres capas esenciales usando **Polars** y **SQLAlchemy**:

### A. Capa de Extracción (`src/extractors.py`)

```
# src/extractors.py
import polars as pl

class ParquetExtractor:
    def __init__(self, ruta_archivo: str):
        self.ruta_archivo = ruta_archivo

    def extraer(self) -&gt; pl.LazyFrame:
        """Lee perezosamente un dataset Parquet."""
        print(f"📥 [Extractor] Escaneando archivo: {self.ruta_archivo}")
        return pl.scan_parquet(self.ruta_archivo)

```

### B. Capa de Transformación (`src/transformers.py`)

```
# src/transformers.py
import polars as pl

class VentasTransformer:
    def __init__(self, comision_porcentaje: float = 0.10):
        self.comision = comision_porcentaje

    def transformar(self, lazy_df: pl.LazyFrame) -&gt; pl.DataFrame:
        """Aplica reglas de negocio de forma inmutable."""
        print("⚙️ [Transformer] Aplicando transformaciones de negocio...")
        return (
            lazy_df
            .filter(pl.col("monto") &gt; 0.0)
            .with_columns(
                comision=pl.col("monto") * self.comision,
                monto_total=pl.col("monto") * 1.21
            )
            .collect() # Dispara la ejecución optimizada
        )

```

### C. Capa de Carga (`src/loaders.py`)

```
# src/loaders.py
import polars as pl
from sqlalchemy import create_engine

class SQLLoader:
    def __init__(self, db_uri: str):
        self.engine = create_engine(db_uri)

    def cargar(self, df: pl.DataFrame, nombre_tabla: str) -&gt; None:
        """Persiste el DataFrame de Polars en la Base de Datos."""
        print(f"📤 [Loader] Insertando {len(df)} registros en la tabla '{nombre_tabla}'...")
        # Convertimos eficientemente a Pandas para aprovechar to_sql con SQLAlchemy
        df.to_pandas().to_sql(
            name=nombre_tabla,
            con=self.engine,
            if_exists="append",
            index=False
        )
        print("✅ [Loader] Carga completada con éxito.")

```

---

## 5\. Punto de Entrada Principal (`main.py`)

El archivo `main.py` actúa únicamente como orquestador, instanciando la configuración y coordinando el flujo de datos:

```
# main.py
import polars as pl
from config.settings import PipelineConfig
from src.extractors import ParquetExtractor
from src.transformers import VentasTransformer
from src.loaders import SQLLoader

def run_pipeline():
    config = PipelineConfig()
    
    # 1. Extracción
    extractor = ParquetExtractor("practica/data_lake_lazy.parquet")
    lazy_data = extractor.extraer()
    
    # 2. Transformación
    transformer = VentasTransformer(comision_porcentaje=0.05)
    df_clean = transformer.transformar(lazy_data)
    
    # 3. Carga
    loader = SQLLoader(config.db.db_uri)
    loader.cargar(df_clean, "fact_ventas_modular")

if __name__ == "__main__":
    run_pipeline()

```

---

## 🏋️‍♂️ Práctica de la Lección 39

1. Creá la carpeta `practica/mi_pipeline_modular/`.
2. Dentro de esa carpeta, estructurá los archivos:
  * `config.py`: Definí la dataclass `Config` con una URI de SQLite en memoria (`sqlite:///:memory:`).
  * `components.py`:
    * Clase `ExtractorSimulado`: Genera un DataFrame sintético de Polars con 1,000 filas (`id`, `monto_raw`, `cliente`).
    * Clase `SaneadorTransformer`: Limpia los montos asegurando que sean mayores a 0 y agrega una columna `monto_con_impuesto`.
    * Clase `CargadorDB`: Inserta el DataFrame resultante en la base de datos SQLite usando SQLAlchemy.
  * `app.py`: Punto de entrada que importa los componentes, ejecuta el pipeline completo de principio a fin e imprime los primeros 5 registros de la base de datos para verificar la persisitencia.
3. Ejecutá tu paquete modular desde la terminal: `python3 practica/mi_pipeline_modular/app.py`