config_db = {
    "host": "localhost",
    "puerto": 5432,
    "usuario": "admin_data",
    "base_datos": "dw_ventas"
}

config_db["ssl"] = True
password_default = config_db.get("password", "SIN_PASSWORD")

for i, j in config_db.items():
    print(f"Parámetro: {i} | Valor: {j}")
    if i == "puerto" and j == 5432:
        print("⚡ Conexión configurada para PostgreSQL en puerto estándar.")