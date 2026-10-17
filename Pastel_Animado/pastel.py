"""Entrada compatível: python pastel.py [foto] [opções]."""
from flower_py.render import PinturaPastel
from flower_py.export import salvar_gif
from flower_py.timing import quantidade_quadros, tempos_gif
from flower_py.cli import main, entrypoint

if __name__ == "__main__":
    entrypoint()
