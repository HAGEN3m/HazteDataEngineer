# 🏛️ Lección 01.B (Módulo 04): Modelado Dimensional Kimball Avanzado: Tablas de Hechos y Dimensiones Especiales

> **Propósito**: Dominar las técnicas avanzadas de arquitectura de datos analítica orientada al negocio mediante la metodología de Ralph Kimball, definiendo con precisión la granularidad (*grain*), los cuatro tipos de tablas de hechos y los patrones especiales de dimensiones (Conformed, Degenerate, Junk, Role-Playing).

---

## 📌 1. OLTP vs. OLAP: Normalización vs. Desnormalización

En ingeniería de datos, el diseño de la base de datos depende estrictamente del patrón de acceso:

```
[ OLTP / Sistema Transaccional ]                  [ OLAP / Data Warehouse ]
   (3NF - Tercera Forma Normal)                      (Modelo Dimensional Estrella)
┌────────────┐   ┌────────────┐                 ┌─────────────────┐   ┌─────────────────┐
│ Clientes   │───│ Pedidos    │                 │ Dim_Cliente     │───│ Fact_Ventas     │
└────────────┘   └────────────┘                 └─────────────────┘   └─────────────────┘
      │                                                                        │
      ▼                                                                        ▼
Escritura rápida (INSERT/UPDATE).               Lectura analítica rápida (SUM/AVG).
Evita redundancia de datos.                    Minimiza JOINs; desnormalización consciente.
```

---

## 🔬 2. Tipos de Tablas de Hechos (Fact Tables)

La **tabla de hechos** representa un evento de negocio numerable y medible. Dependiendo de la naturaleza del proceso, se dividen en cuatro tipos:

1. **Transaction Fact Tables (Hechos Transaccionales)**:
   * Registra un evento discreto en un punto específico del tiempo (ej. una venta en caja, un clic, una transferencia bancaria).
   * **Granularidad**: Una fila por transacción.
2. **Periodic Snapshot Fact Tables (Instantáneas Periódicas)**:
   * Almacena el estado o saldo acumulado en intervalos regulares (diario, mensual) (ej. saldo de cuenta bancaria al final del día, nivel de stock mensual).
   * **Granularidad**: Una fila por entidad por periodo.
3. **Accumulating Snapshot Fact Tables (Instantáneas Acumulativas)**:
   * Modela procesos con un flujo o pipeline de etapas con inicio y fin bien definidos (ej. procesamiento de un pedido desde 'recibido', 'empaquetado', 'enviado' hasta 'entregado').
   * Contiene múltiples columnas de fecha que se van actualizando a medida que avanza el hito.
4. **Factless Fact Tables (Hechos sin Métricas)**:
   * Registra la ocurrencia o relación entre eventos donde no hay métricas numéricas directas (ej. asistencia de alumnos a clases, cobertura de promociones).

---

## 🛠️ 3. Patrones Especiales de Dimensiones

Las **dimensiones** proveen el contexto (*quién, qué, dónde, cuándo, por qué*) a las métricas de la tabla de hechos.

```
                  ┌──────────────────────┐
                  │ Dim_Tiempo           │ (Role-Playing: Fecha_Pedido, Fecha_Envio)
                  └──────────┬───────────┘
                             │
┌──────────────────────┐     ▼     ┌──────────────────────┐
│ Dim_Cliente          │───[FACT]──│ Dim_Estado_Junk      │ (Junk: Pago_Aprobado, Envio_Express)
└──────────────────────┘     ▲     └──────────────────────┘
                             │
                  ┌──────────┴───────────┐
                  │ Codigo_Ticket        │ (Degenerate: Sin tabla propia)
                  └──────────────────────┘
```

### A. Role-Playing Dimensions (Dimensiones de Rol)
Ocurre cuando una sola dimensión física se reutiliza con múltiples significados lógicos dentro de la misma tabla de hechos.
* *Ejemplo*: `Dim_Tiempo` unida a la tabla de hechos como `fecha_pedido_key`, `fecha_pago_key` y `fecha_envio_key`.

### B. Degenerate Dimensions (Dimensiones Degeneradas)
Atributos dimensionales que residen directamente dentro de la tabla de hechos sin tener una tabla de dimensión dedicada. Típicamente son identificadores únicos del sistema fuente.
* *Ejemplo*: `numero_factura`, `ticket_id`, `numero_guia_rastreo`.

### C. Junk Dimensions (Dimensiones Basura / Combinadas)
Agrupación de múltiples indicadores booleanos, flags o códigos de estado de baja cardinalidad en una sola tabla dimensional para evitar inflar la tabla de hechos con decenas de claves foráneas.
* *Ejemplo*: Agrupar `tipo_pago` (Tarjeta/Efectivo), `envio_express` (Sí/No) y `cupon_aplicado` (Sí/No) en una sola `Dim_Perfil_Transaccion`.

### D. Conformed Dimensions (Dimensiones Conformadas)
Dimensiones idénticas compartidas entre múltiples *Data Marts* o tablas de hechos. Permiten realizar consultas cruzadas (*Drill-Across*) entre diferentes procesos de negocio.
* *Ejemplo*: `Dim_Cliente` y `Dim_Producto` compartidas entre el Data Mart de Ventas y el Data Mart de Garantías.

---

## ⚡ 4. Definiendo la Granularidad (*The Grain*)

La regla #1 de Ralph Kimball es **declarar explícitamente el grano** antes de diseñar cualquier tabla de hechos.

> *"El grano define exactamente qué representa una sola fila en la tabla de hechos."*

* ❌ **Grano ambiguo**: "Muestra las ventas de productos por cliente".
* ✅ **Grano atómico preciso**: "Una fila representa un ítem individual comprado dentro de una transacción en un punto de venta".

---

## 🏋️‍♂️ Ejercicio Práctico Hands-On: Esquema Estrella DDL en PostgreSQL

Crea el archivo `modelo_estrella_ecommerce.sql` para implementar una arquitectura Kimball con dimensión Junk y Degenerada:

```sql
-- 1. Dimensión Conformada de Tiempo
CREATE TABLE dim_tiempo (
    tiempo_key INT PRIMARY KEY, -- Formato YYYYMMDD
    fecha DATE NOT NULL,
    anio INT NOT NULL,
    trimestre INT NOT NULL,
    mes INT NOT NULL,
    dia_semana VARCHAR(15) NOT NULL
);

-- 2. Dimensión Junk (Agrupa flags de estado)
CREATE TABLE dim_estado_transaccion (
    estado_key SERIAL PRIMARY KEY,
    metodo_pago VARCHAR(30) NOT NULL,
    es_envio_express BOOLEAN NOT NULL,
    es_cliente_vip BOOLEAN NOT NULL
);

-- 3. Tabla de Hechos Transaccional
CREATE TABLE fact_ventas_item (
    venta_item_id BIGSERIAL PRIMARY KEY,
    
    -- Claves Foráneas (FK) a Dimensiones
    tiempo_pedido_key INT NOT NULL REFERENCES dim_tiempo(tiempo_key),
    tiempo_envio_key INT NOT NULL REFERENCES dim_tiempo(tiempo_key), -- Role-Playing
    estado_key INT NOT NULL REFERENCES dim_estado_transaccion(estado_key),
    cliente_id INT NOT NULL,
    producto_id INT NOT NULL,
    
    -- Dimensión Degenerada
    numero_factura VARCHAR(50) NOT NULL,
    
    -- Métricas Numéricas
    cantidad INT NOT NULL,
    precio_unitario NUMERIC(10,2) NOT NULL,
    monto_descuento NUMERIC(10,2) DEFAULT 0.00,
    monto_total_linea NUMERIC(12,2) NOT NULL
);
```

---

## 🧠 Checkpoint de Autoevaluación

1. ¿Cuál es la diferencia entre una *Transaction Fact Table* y una *Accumulating Snapshot Fact Table*?
2. ¿Qué es una *Degenerate Dimension* y por qué no requiere una tabla de dimensión independiente?
3. ¿Por qué se utiliza una *Junk Dimension* y qué problema resuelve en la tabla de hechos?
4. Explica el concepto de *Conformed Dimension* y por qué es fundamental para realizar consultas *Drill-Across* en un Data Warehouse empresarial.
