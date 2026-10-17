"""Quantidade de quadros e tempos do formato GIF."""
import math


def quantidade_quadros(duracao):
    return min(144, max(2, round(duracao * 12) + 1))


def tempos_gif(quantidade, duracao):
    if quantidade < 1 or not math.isfinite(duracao) or duracao < .02:
        raise ValueError("Duracao ou quantidade de quadros invalida.")
    ticks = round(duracao * 100)
    if ticks < quantidade * 2:
        raise ValueError("Quadros demais para a duracao solicitada.")
    base, resto = divmod(ticks, quantidade)
    tempos = [(base + (i < resto)) * 10 for i in range(quantidade)]
    tempos[-1] += 1800
    return tempos


