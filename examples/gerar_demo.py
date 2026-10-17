"""Recria os exemplos a partir do material já presente no projeto."""
from pathlib import Path
import subprocess
import sys
from PIL import Image, ImageDraw, ImageOps

ROOT = Path(__file__).resolve().parents[1]
source = ROOT / 'Pastel_Animado/Buque_do_video.png'
docs = ROOT / 'docs'
docs.mkdir(exist_ok=True)
subprocess.run([sys.executable, str(ROOT / 'Pastel_Animado/pastel.py'),
                str(source), '--sem-janela', '--tamanho', '480', '--semente', '42',
                '--duracao', '6', '--png', str(docs / 'pintura.png'),
                '--gif', str(docs / 'demo.gif')], check=True)
sheet = Image.new('RGB', (680, 450), '#15151a')
draw = ImageDraw.Draw(sheet)
for x, path, title in [(10, source, 'Entrada: recorte do video'),
                        (350, docs / 'pintura.png', 'Resultado: semente 42')]:
    with Image.open(path) as im:
        preview = ImageOps.contain(im.convert('RGB'), (320, 400))
        sheet.paste(preview, (x + (320-preview.width)//2, 35))
    draw.text((x, 12), title, fill='white')
sheet.save(docs / 'comparacao.png')
