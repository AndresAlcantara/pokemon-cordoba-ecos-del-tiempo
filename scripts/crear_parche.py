"""
crear_parche.py
===============
Crea un parche BPS con tus cambios: la diferencia entre el Unbound original
y MiHack.gba. Lo que se comparte es el parche, nunca la ROM.

Por qué BPS y no IPS: IPS no admite archivos de más de 16 MB y Unbound ocupa
32 MB. BPS además guarda una suma de control del archivo base, así que avisa
si alguien lo aplica sobre una ROM equivocada.

Uso (desde la carpeta GBA):
    herramientas\\python-venv\\Scripts\\python.exe scripts\\crear_parche.py
Resultado: parches/MiHack_AAAA-MM-DD.bps
Para aplicarlo, el jugador necesita su propio Unbound v2.0.3.2 y Flips.
"""
import subprocess
import sys
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
FLIPS = RAIZ / "herramientas" / "Flips" / "flips.exe"
ORIGINAL = RAIZ / "original" / "Pokemon Unbound v2.0.3.2 (ORIGINAL - no tocar).gba"
COPIA = RAIZ / "MiHack.gba"
PARCHES = RAIZ / "parches"


def main() -> int:
    for ruta in (FLIPS, ORIGINAL, COPIA):
        if not ruta.exists():
            print(f"ERROR: falta {ruta}")
            return 1
    PARCHES.mkdir(exist_ok=True)
    salida = PARCHES / f"MiHack_{date.today().isoformat()}.bps"
    # --create --bps-delta: modo de creación más lento pero con parches más pequeños.
    r = subprocess.run(
        [str(FLIPS), "--create", "--bps-delta", str(ORIGINAL), str(COPIA), str(salida)],
        capture_output=True, text=True,
    )
    print(r.stdout.strip() or r.stderr.strip())
    if r.returncode != 0 or not salida.exists():
        print("ERROR: Flips no pudo crear el parche.")
        return 1
    print(f"Parche creado: {salida.relative_to(RAIZ)} ({salida.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
