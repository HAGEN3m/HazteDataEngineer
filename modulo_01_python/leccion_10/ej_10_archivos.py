import csv


eventos_raw = [
    {"timestamp": "2026-01-01 10:00:00", "modulo": "Ingesta", "nivel": "INFO", "mensaje": "Conexión exitosa"},
    {"timestamp": "2026-01-01 10:01:15", "modulo": "Transformación", "nivel": "ERROR", "mensaje": "Monto negativo detectado"},
    {"timestamp": "2026-01-01 10:02:30", "modulo": "Carga", "nivel": "WARNING", "mensaje": "Tiempo de respuesta elevado"}
]

registro_1 = eventos_raw[1]
columnas = []
for i in registro_1:
    columnas.append(i)



with open("log_ejecucion.csv", mode="w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=columnas)
    writer.writeheader()
    writer.writerows(eventos_raw)


with open("log_ejecucion.csv", mode="r", encoding="utf-8") as f_in, \
    open("alertas.txt", mode="a", encoding="utf-8") as f_out:

        reader = csv.DictReader(f_in)
        for i in reader:
            if i["nivel"] == "WARNING" or i["nivel"] == "ERROR":
                f_out.write(f"{i['mensaje']}\n")

with open("alertas.txt", mode="r", encoding="utf-8") as f:
    contador = 0
    for i in f:
        contador += 1
        print(f"{contador} {i.strip()}")

