"""Argumentos e execução pelo terminal."""
import argparse
import math
from pathlib import Path
from PIL import Image
from .render import PinturaPastel
from .export import salvar_gif
from .timing import quantidade_quadros


def main():
    parser = argparse.ArgumentParser(description="Transforma uma foto em pintura pastel animada.")
    parser.add_argument("foto", nargs="?", help="Caminho de uma foto; omitido, abre o seletor.")
    parser.add_argument("--tamanho", type=int, default=760, help="Lado maior, de 64 a 1600 pixels.")
    parser.add_argument("--duracao", type=float, default=12, help="Duracao aproximada, em segundos.")
    parser.add_argument("--semente", type=int, default=42, help="Varia o desenho dos tracos.")
    parser.add_argument("--gif", help="Caminho para salvar a animacao GIF.")
    parser.add_argument("--png", default="pintura_pastel.png", help="PNG gerado em modo sem janela.")
    parser.add_argument("--sem-janela", action="store_true", help="Exporta sem abrir a interface.")
    args = parser.parse_args()
    if not 64 <= args.tamanho <= 1600:
        parser.error("--tamanho deve ficar entre 64 e 1600.")
    if not math.isfinite(args.duracao) or not 1 <= args.duracao <= 120:
        parser.error("--duracao deve ficar entre 1 e 120 segundos.")
    if args.sem_janela:
        if not args.foto:
            parser.error("Informe a foto ao usar --sem-janela.")
        pintura = PinturaPastel(args.foto, args.tamanho, args.semente)
        quadros = []
        for imagem, _ in pintura.quadros(quantidade_quadros(args.duracao)):
            if args.gif:
                imagem.thumbnail((420, 560), Image.Resampling.LANCZOS)
                quadros.append(imagem)
        Path(args.png).parent.mkdir(parents=True, exist_ok=True)
        pintura.tela.save(args.png)
        print(f"Pintura salva: {args.png}")
        if args.gif:
            salvar_gif(quadros, args.gif, args.duracao)
            print(f"Animacao salva: {args.gif}")
    else:
        from .gui import executar
        executar(args)


def entrypoint():
    try:
        main()
    except (OSError, ValueError) as erro:
        raise SystemExit(f"Nao foi possivel criar a pintura: {erro}")
