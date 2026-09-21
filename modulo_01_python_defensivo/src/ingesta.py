import csv
import logging
import os

from dotenv import load_dotenv


logging.basicConfig(
	level=logging.INFO,
	format="%(asctime)s [%(levelname)s] %(message)s",
)


def cargar_credenciales() -> str:
	"""Carga la API_KEY desde el archivo .env."""
	load_dotenv()
	api_key = os.getenv("API_KEY")
	if not api_key:
		logging.critical("Credencial API_KEY no encontrada en el entorno.")
		raise ValueError("API_KEY no configurada.")
	return api_key


def procesar_ventas_raw(ruta_csv: str) -> dict:
	"""Procesa ventas completadas y descarta registros inválidos."""
	monto_total = 0.0
	validas = 0
	descartadas = 0

	try:
		with open(ruta_csv, mode="r", encoding="utf-8", newline="") as archivo:
			reader = csv.DictReader(archivo)
			for numero_fila, row in enumerate(reader, start=2):
				try:
					estado = row.get("estado")
					monto = float(row.get("monto_usd", ""))
					if estado != "COMPLETADA" or monto <= 0:
						raise ValueError("estado o monto inválido")
				except (TypeError, ValueError):
					logging.warning("Fila %s descartada: registro inválido.", numero_fila)
					descartadas += 1
					continue

				monto_total += monto
				validas += 1
	except FileNotFoundError:
		logging.error(f"El archivo {ruta_csv} no existe.")
		raise

	return {
		"monto_total": round(monto_total, 2),
		"transacciones_validas": validas,
		"registros_descartados": descartadas,
	}
