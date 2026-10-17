"""Exportação de GIF com paleta global."""
import math
from pathlib import Path
import numpy as np
from PIL import Image
from .timing import tempos_gif


def salvar_gif(quadros, destino, duracao):
    if not quadros:
        raise ValueError("Nenhum quadro para exportar.")
    if not math.isfinite(duracao) or duracao < .02:
        raise ValueError("Duracao invalida.")
    limite = max(1, round(duracao * 100) // 2)
    if len(quadros) > limite:
        indices = np.linspace(0, len(quadros) - 1, limite, dtype=int)
        quadros = [quadros[i] for i in indices] if limite > 1 else [quadros[-1]]
    Path(destino).parent.mkdir(parents=True, exist_ok=True)
    # Paleta global para reduzir tremulacao de cores entre quadros.
    paleta = quadros[-1].quantize(colors=256)
    convertidos = [q.quantize(palette=paleta, dither=Image.Dither.NONE) for q in quadros]
    tempos = tempos_gif(len(quadros), duracao)
    convertidos[0].save(destino, save_all=True, append_images=convertidos[1:],
                         duration=tempos, loop=0, optimize=False, disposal=1)


