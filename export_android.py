import json
from pathlib import Path

def exportar_json_android(preguntas, nombre_archivo="preguntas_android.json"):
    output_dir = Path("data/android_export")
    output_dir.mkdir(parents=True, exist_ok=True)

    ruta = output_dir / nombre_archivo

    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(preguntas, f, ensure_ascii=False, indent=4)

    return str(ruta)
