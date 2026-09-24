# 🏛️ Lección 03.B (Módulo 04): Data Vault 2.0: Hubs, Links, Satellites, Hash Keys y Hash Diffs

&gt; **Propósito**: Dominar la metodología de modelado analítico **Data Vault 2.0**, diseñada para resolver los desafíos de escalabilidad masiva, audibilidad total del 100% de los datos e ingesta paralela sin bloqueos desde múltiples sistemas fuente heterogéneos en grandes organizaciones.

---

## 📌 1\. ¿Por qué Data Vault 2.0 frente a Kimball (Estrella) y 3NF?

A medida que las empresas crecen, las arquitecturas tradicionales de Data Warehouse enfrentan problemas severos:

* **Kimball (Esquema Estrella)**: Optimizado para velocidad de consulta en BI, pero frágil ante cambios constantes en los sistemas fuente (modificar esquemas en sistemas OLTP requiere refactorizar dimensiones y tablas de hechos complejas).
* **Inmon (3NF)**: Garantiza consistencia, pero las ingestas son altamente secuenciales y lentas debido a la resolución de claves foráneas y relaciones complejas.

```
                  ┌─────────────────────────────────────────┐
                  │          SISTEMAS FUENTE (OLTP)         │
                  │   CRM, ERP, Web App, APIs, Logs, IoT    │
                  └────────────────────┬────────────────────┘
                                       │
                                       ▼ Ingesta Paralele sin Bloqueos (Hash Keys)
                  ┌─────────────────────────────────────────┐
                  │             RAW DATA VAULT              │
                  │  (Hubs, Links, Satellites - Sin Reglas) │
                  └────────────────────┬────────────────────┘
                                       │
                                       ▼ Aplicación de Reglas de Negocio
                  ┌─────────────────────────────────────────┐
                  │             BUSINESS VAULT              │
                  │   (PIT Tables, Bridge Tables, Reglas)   │
                  └────────────────────┬────────────────────┘
                                       │
                                       ▼ Proyección para Consumo Analítico
                  ┌─────────────────────────────────────────┐
                  │            INFORMATION MARTS            │
                  │   (Esquemas Estrella / Vistas Kimball)  │
                  └─────────────────────────────────────────┘

```

### Principios Fundamentales de Data Vault 2.0:

1. **Auditoría Total (100% Traceability)**: Se almacena todo el dato original sin aplicar reglas de negocio destructivas en la capa Raw.
2. **Resiliencia al Cambio**: Agregar nuevas columnas o fuentes no rompe la estructura existente; solo se añaden satélites o relaciones nuevas.
3. **Carga Paralela Escalable**: Reemplaza las secuencias numéricas tradicionales por **Hash Keys** (MD5/SHA256), permitiendo cargar Hubs, Links y Satellites en paralelo sin esperar la generación de IDs autoincrementales.

---

## 🔬 2\. Los 3 Componentes Clave de Data Vault

El modelo Data Vault desacopla la **identidad** de las entidades, sus **relaciones** y sus **atributos descriptivos**:

```
                       ┌───────────────────────┐
                       │     SAT_CLIENTE       │ (Atributos cambiantes: Nombre, Email)
                       │ ─── hk_cliente (FK)   │
                       └───────────┬───────────┘
                                   │
                                   ▼
┌──────────────────────┐  ┌─────────────────┐  ┌──────────────────────┐
│     HUB_CLIENTE      │&lt;─┤   LINK_VENTA    ├─&gt;│     HUB_PRODUCTO     │
│ (Clave de negocio)   │  │ (Asociación N:M)│  │ (Clave de negocio)   │
│ ─── hk_cliente (PK)  │  │ ─── hk_venta    │  │ ─── hk_producto (PK) │
└──────────────────────┘  └─────────────────┘  └──────────────────────┘

```

### A. Hubs (Entidades de Negocio)

Representan los conceptos centrales del negocio (ej. Cliente, Producto, Cuenta). **No contienen atributos descriptivos**.

* **Estructura**:  
  * `hk_