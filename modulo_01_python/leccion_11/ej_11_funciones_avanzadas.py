

def auditar_pipeline(nombre_pipeline, *args, **kwargs):
    total_acumulado = sum(args)
    cant_reg = len(args)
    metadata = kwargs
    metadata["nombre_pipeline"] = nombre_pipeline
    es_exitoso = cant_reg > 0
    metadata["cantidad_reg"] = cant_reg
    metadata["total_acumulado"] = total_acumulado
    return metadata, es_exitoso

metadata, es_exitoso = auditar_pipeline("ingesta_diaria", 150.50, 300.00, 450.25, 100.00, entorno="PROD", ejecutado_por="airflow")

print(f"METADATA {metadata}\nES_EXITOSO {es_exitoso}" )