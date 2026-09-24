from datetime import datetime, timedelta

logs_servidor = [
    {"id": 1, "timestamp_str": "2026-01-10 08:30:00", "estado": "OK"},
    {"id": 2, "timestamp_str": "2026-01-14 12:00:00", "estado": "ERROR"},
    {"id": 3, "timestamp_str": "2026-01-15 09:15:00", "estado": "OK"},
]

fecha_referencia = datetime(2026, 1, 15, 10, 0, 0)

def str_to_datetime(date_str: str) -> datetime:
    formato = "%Y-%m-%d %H:%M:%S"
    try:
        date_time = datetime.strptime(date_str, formato)
        return date_time
    except:
        print("Fecha invalida")
        return None

for i in logs_servidor:
    i["timestamp_str"] = str_to_datetime(i["timestamp_str"])

def diferencia(fecha_referencia: datetime, log: datetime) -> timedelta:
    return fecha_referencia - log


for i in logs_servidor:
    if diferencia(fecha_referencia, i["timestamp_str"]) <= timedelta(days=2) and i["estado"] == "ERROR":
        print(f"🚨 ALERTA: Log #{i['id']} con estado ERROR detectado dentro de la ventana de 48hs (Fecha: {i['timestamp_str'].strftime('%Y-%m-%d')})")