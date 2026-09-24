
from transformaciones import limpiar_monto_str
from datetime import datetime

if __name__ == "__main__":
    for i in ["$1,500.50", "$200.00", "INVALIDO", "$3,450.75"]:
        print(f"{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n{limpiar_monto_str(i)}\n{"*"*25}\n")