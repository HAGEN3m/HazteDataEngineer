CONFIG_ESQUEMA = ("id_transaccion", "cliente_id", "monto", "fecha")
ids_reporte = ["C-01", "C-02", "C-01", "C-03", "C-02", "C-04", "C-01"]

ids_unicos = set(ids_reporte)

ids_base_datos = {"C-01", "C-02", "C-05"}

print(f"Cantidad original de registros: {len(ids_reporte)} | Cantidad de registros únicos: {len(ids_unicos)}")

clientes_nuevos = ids_unicos - ids_base_datos
print(f"Clientes nuevos: {clientes_nuevos}")

all_clients = ids_unicos | ids_base_datos
print(f"Todos los clientes: {all_clients}")

