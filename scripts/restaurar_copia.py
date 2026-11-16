"""
restaurar_copia.py
==================
Vuelve a dejar MiHack.gba igual que el Unbound original.

Qué hace, paso a paso:
  1. Comprueba que el original existe y que no ha cambiado (huella SHA-1).
  2. Si ya hay un MiHack.gba, lo guarda primero en respaldos/ (nunca se pierde nada).
  3. Copia el original encima de MiHack.gba.

Uso (desde la carpeta GBA):
    herramientas\\python-venv\\Scripts\\python.exe scripts\\restaurar_copia.py
o con doble clic en "Restaurar MiHack.bat".
"""
import hashlib
import shutil
import sys
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ORIGINAL = RAIZ / "original" / "Pokemon Unbound v2.0.3.2 (ORIGINAL - no tocar).gba"
COPIA = RAIZ / "MiHack.gba"
RESPALDOS = RAIZ / "respaldos"
# Huella del Unbound v2.0.3.2 que había en la carpeta el 14/11/2026.
SHA1_ORIGINAL = "0f54a37fdae801a186068bdc0bbad8b77ec0d306"


def sha1(ruta: Path) -> str:
    h = hashlib.sha1()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def main() -> int:
    if not ORIGINAL.exists():
        print(f"ERROR: no encuentro el original en {ORIGINAL}")
        return 1

    huella = sha1(ORIGINAL)
    if huella != SHA1_ORIGINAL:
        print("ERROR: el original ha cambiado (la huella SHA-1 no coincide).")
        print(f"  esperada: {SHA1_ORIGINAL}\n  actual:   {huella}")
        print("No restauro nada para no propagar un original dañado.")
        return 1
    print("Original verificado (SHA-1 correcto).")

    if COPIA.exists():
        RESPALDOS.mkdir(exist_ok=True)
        sello = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        destino = RESPALDOS / f"MiHack_antes-de-restaurar_{sello}.gba"
        shutil.copy2(COPIA, destino)
        print(f"Copia actual guardada en: {destino.relative_to(RAIZ)}")

    shutil.copyfile(ORIGINAL, COPIA)
    print("MiHack.gba restaurado. Vuelve a estar igual que Unbound original.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
