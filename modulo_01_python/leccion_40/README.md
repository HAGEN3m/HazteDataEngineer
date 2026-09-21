# 🐍 Lección 40: Cierre del Bloque 4 — Proyecto Capstone de Data Engineering Ssr

¡Llegamos al gran hito final del **Bloque 4: Python para Data Engineering Ssr (Lecciones 31 a 40)**![1]

A lo largo de este bloque hemos recorrido el camino completo del procesamiento y la arquitectura de datos moderna:

* **Lección 31**: Almacenamiento columnar y compresión con **Apache Parquet** y particionamiento en Data Lakes[2][3].
* **Lección 32**: Extracción defensiva desde **APIs REST** con reintentos automáticos y backoff exponencial[2].
* **Lección 33**: Abstracción y gestión segura de bases de datos relacionales con **SQLAlchemy**[4].
* **Lección 34**: Ingesta masiva (*Bulk Loading*) e inserciones eficientes por lotes.
* **Lección 35**: Saneamiento e inmutabilidad vectorizada en Pandas con `df.assign()` y `np.select()`.
* **Lección 36**: Agregaciones compuestas y funciones de ventana con `.transform()`, `.pivot_table()` y `.melt()`.
* **Lección 37**: Procesamiento multihilo de alta velocidad con **Polars** y expresiones `pl.col()`[5].
* **Lección 38**: Evaluación perezosa (**LazyFrame**), optimización de consultas (*Pushdown*) y streaming con `scan_parquet()`[5].
* **Lección 39**: Arquitectura modular desacoplada (Configuración, Extractores, Transformadores y Cargadores).

En esta lección integraremos todos estos bloques en un **Proyecto Capstone End-to-End**[6][7].

---

## 1\. Especificaciones del Proyecto Capstone

El objetivo es construir una plataforma de ingesta y transformación de transacciones comerciales aplicando una arquitectura modular enterprise[6][7].

```
┌────────────────────────┐      ┌────────────────────────┐
│  API REST (Pública)    │      │  Data Lake (Parquet)   │
└───────────┬────────────┘      └───────────┬────────────┘
            │                               │
            ▼                               ▼
 ┌─────────────────────────────────────────────────────┐
 │  Extractor Modulado (Sesión Defensiva &amp; Lazy Scan)  │
 └──────────────────────────┬──────────────────────────┘
                            │
                            ▼
 ┌─────────────────────────────────────────────────────┐
 │  Transformer en Polars (LazyFrame + Pushdown)       │
 └──────────────────────────┬──────────────────────────┘
                            │
                            ▼
 ┌─────────────────────────────────────────────────────┐
 │  Loader Relacional (SQLAlchemy / Bulk Loading)      │
 └──────────────────────────┬──────────────────────────┘
                            │
                            ▼
               ┌────────────────────────┐
               │  Database (SQLite/DB)  │
               └────────────────────────┘

```

---

## 2\. Implementación Completa de la Arquitectura

### A. Configuración Centralizada (`config/settings.py`)

```
# config/settings.py
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class PipelineConfig:
    api_url: str = os.getenv("API_URL", "https://httpbin.org/json")
    parquet_path: str = os.getenv("PARQUET_PATH", "practica/data_lake_lazy.parquet")
    db_uri: str = os.getenv("DATABASE_URL", "sqlite:///:memory:")
    chunk_size: int = 5000

```

### B. Capa de Extracción Defensiva (`src/extractors.py`)

```
# src/extractors.py
import polars as pl
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

class DataExtractor:
    def __init__(self, api_url: str, parquet_path: str):
        self.api_url = api_url
        self.parquet_path = parquet_path
        self.sesion = self._crear_sesion_defensiva()

    def _crear_sesion_defensiva() -&gt; requests.Session:
        sesion = requests.Session()
        retries = Retry(total=3, backoff_factor=1.0, status_forcelist=)
        sesion.mount("https://", HTTPAdapter(max_retries=retries))
        return sesion

    def extraer_api() -&gt; dict:
        print(f"🌐 [Extractor] Consultando API defensivamente: {self.api_url}")
        res = self.sesion.get(self.api_url, timeout=(3.0, 10.0))
        res.raise_for_status()
        return res.json()

    def scan_parquet_lake(self) -&gt; pl.LazyFrame:
        print(f"📂 [Extractor] Escaneando Data Lake en modo Lazy: {self.parquet_path}")
        return pl.scan_parquet(self.parquet_path)

```

### C. Capa de Transformación con Polars (`src/transformers.py`)

```
# src/transformers.py
import polars as pl

class SalesTransformer:
    def __init__(self, umbral_monto: float = 50.0):
        self.umbral = umbral_monto

    def transformar(self, lazy_df: pl.LazyFrame) -&gt; pl.DataFrame:
        print("⚡ [Transformer] Ejecutando plan optimizado con Polars Lazy Engine...")
        
        plan_optimizado = (
            lazy_df
            .filter(pl.col("monto") &gt; self.umbral)
            .with_columns(
                monto_impuesto=pl.col("monto") * 1.21,
                categoria_monto=pl.when(pl.col("monto") &gt; 200.0)
                                  .then(pl.lit("ALTO_VALOR"))
                                  .otherwise(pl.lit("ESTANDAR"))
            )
            .select(["id", "cliente", "region", "categoria", "monto", "monto_impuesto", "categoria_monto"])
        )
        
        # Dispara la ejecución evaluada y optimizada en Rust
        return plan_optimizado.collect()

```

### D. Capa de Persistencia Relacional (`src/loaders.py`)

```
# src/loaders.py
import polars as pl
from sqlalchemy import create_engine

class RelationalLoader:
    def __init__(self, db_uri: str, chunk_size: int = 5000):
        self.engine = create_engine(db_uri)
        self.chunk_size = chunk_size

    def cargar_bulk(self, df: pl.DataFrame, nombre_tabla: str) -&gt; None:
        print(f"📥 [Loader] Insertando {len(df)} registros en la tabla '{nombre_tabla}'...")
        
        # Inserción masiva por lotes
        df.to_pandas().to_sql(
            name=nombre_tabla,
            con=self.engine,
            if_exists="replace",
            index=False,
            chunksize=self.chunk_size,
            method="multi"
        )
        print("✅ [Loader] Carga masiva completada con éxito.")

```

### E. Orquestador Principal (`main.py`)

```
# main.py
import polars as pl
from config.settings import PipelineConfig
from src.extractors import DataExtractor
from src.transformers import SalesTransformer
from src.loaders import RelationalLoader

def ejecutar_capstone():
    print("🚀 Iniciando Pipeline Capstone de Data Engineering...")
    config = PipelineConfig()
    
    # 1. Extracción
    extractor = DataExtractor(config.api_url, config.parquet_path)
    lazy_parquet = extractor.scan_parquet_lake()
    
    # 2. Transformación con Polars
    transformer = SalesTransformer(umbral_monto=100.0)
    df_procesado = transformer.transformar(lazy_parquet)
    
    # 3. Carga Relacional
    loader = RelationalLoader(config.db_uri, config.chunk_size)
    loader.cargar_bulk(df_procesado, "fact_ventas_capstone")
    
    print("🎉 Pipeline Capstone finalizado correctamente.")

if __name__ == "__main__":
    ejecutar_capstone()

```

---

## 🏋️‍♂️ Práctica del Proyecto Capstone (Lección 40)

1. Creá la estructura de directorios dentro de `practica/capstone_de/`:

```
practica/capstone_de/
├── config/
│   └── settings.py
├── src/
│   ├── extractors.py
│   ├── transformers.py
│   └── loaders.py
└── main.py

```

1. Asegurate de tener generado un archivo Parquet de prueba en `practica/data_lake_lazy.parquet` (creado en la Lección 38).
2. Ejecutá el pipeline completo desde la terminal: `python3 practica/capstone_de/main.py`
3. Comprobá que:
  * La extracción escanee el archivo Parquet en modo perezoso (*Lazy*)[5].
  * Polars ejecute las transformaciones en Rust con *Pushdown* optimizado[5].
  * La carga se realice mediante lotes en la base de datos de destino.