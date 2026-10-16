"""Reconstrucao animada de fotografias com tracos de giz pastel.

Uso: python pastel.py [foto.jpg] [--gif animacao.gif] [--sem-janela]
"""
import argparse
import math
from pathlib import Path
import queue
import threading

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps


class PinturaPastel:
    def __init__(self, caminho, tamanho=760, semente=42, fundo=(7, 7, 9)):
        self.rng = np.random.default_rng(semente)
        with Image.open(caminho) as foto:
            self.foto = ImageOps.exif_transpose(foto).convert("RGB")
        self.foto.thumbnail((tamanho, tamanho), Image.Resampling.LANCZOS)
        self.w, self.h = self.foto.size
        if min(self.w, self.h) < 16:
            raise ValueError("Escolha uma imagem com pelo menos 16 pixels em cada lado.")
        self.tela = Image.new("RGB", self.foto.size, fundo)
        self.granulado = self.rng.random((self.h, self.w), dtype=np.float32)
        # Ruido suave cria irregularidades maiores, alem dos poros do papel.
        ruido = Image.fromarray(self.rng.integers(0, 256, (max(2, self.h // 4),
                                                 max(2, self.w // 4)), dtype=np.uint8))
        self.fibra = np.asarray(ruido.resize(self.foto.size,
                               Image.Resampling.BILINEAR), dtype=np.float32) / 255
        self.camadas = []
        escalas = (0.058, 0.035, 0.021, 0.012, 0.006)
        limites = (1000, 1600, 2400, 3200, 4200)
        referencia = np.asarray(self.foto, dtype=np.float32)
        for escala, limite in zip(escalas, limites):
            largura = max(2.2, min(self.w, self.h) * escala)
            cores = np.asarray(self.foto.filter(ImageFilter.GaussianBlur(largura * .28)),
                               dtype=np.float32)
            luz = cores @ np.array([.299, .587, .114], dtype=np.float32)
            gy, gx = np.gradient(luz)
            # Tensor de estrutura: direcao suave e tangente aos contornos.
            # Pillow nao filtra imagens F em todas as versoes; converter as
            # componentes para L com escala preserva o sinal e a amplitude.
            def filtrar(matriz):
                alcance = float(np.max(np.abs(matriz))) + 1e-6
                codificada = np.uint8(np.clip(matriz / alcance * 127 + 128, 0, 255))
                filtrada = Image.fromarray(codificada).filter(
                    ImageFilter.GaussianBlur(largura * .7))
                return (np.asarray(filtrada, dtype=np.float32) - 128) * alcance / 127
            jxx, jyy, jxy = (filtrar(gx * gx), filtrar(gy * gy), filtrar(gx * gy))
            angulos = .5 * np.arctan2(2 * jxy, jxx - jyy) + math.pi / 2
            passo = max(3, largura * 1.05)
            yy, xx = np.mgrid[0:self.h:passo, 0:self.w:passo]
            xy = np.column_stack((xx.ravel(), yy.ravel())).astype(float)
            xy += self.rng.uniform(-passo * .43, passo * .43, xy.shape)
            xy[:, 0] = np.clip(xy[:, 0], 0, self.w - 1)
            xy[:, 1] = np.clip(xy[:, 1], 0, self.h - 1)
            if len(xy) > limite:
                # Preservar detalhes sem concentrar tudo numa unica regiao.
                xi, yi = xy[:, 0].astype(int), xy[:, 1].astype(int)
                detalhe = np.linalg.norm(referencia[yi, xi] - cores[yi, xi], axis=1)
                pesos = 1 + detalhe / 16 + np.hypot(gx[yi, xi], gy[yi, xi]) / 12
                xy = xy[self.rng.choice(len(xy), limite, replace=False, p=pesos / pesos.sum())]
            self.rng.shuffle(xy)
            self.camadas.append((largura, cores, angulos, xy))
        self.total = sum(len(c[3]) for c in self.camadas)

    def traco(self, x, y, largura, cores, angulos):
        xi, yi = int(x), int(y)
        angulo = float(angulos[yi, xi]) + self.rng.normal(0, .13)
        comprimento = largura * self.rng.uniform(2.0, 3.8)
        dx, dy = math.cos(angulo), math.sin(angulo)
        curva = self.rng.normal(0, largura * .18)
        pontos = []
        for t in np.linspace(-.5, .5, 7):
            desvio = curva * (1 - 4 * t * t)
            pontos.append((x + dx * t * comprimento - dy * desvio,
                           y + dy * t * comprimento + dx * desvio))
        raio = largura * .65 + 3
        x0 = max(0, int(min(p[0] for p in pontos) - raio))
        y0 = max(0, int(min(p[1] for p in pontos) - raio))
        x1 = min(self.w, int(max(p[0] for p in pontos) + raio) + 1)
        y1 = min(self.h, int(max(p[1] for p in pontos) + raio) + 1)
        mascara = Image.new("L", (x1 - x0, y1 - y0))
        desenho = ImageDraw.Draw(mascara)
        locais = [(px - x0, py - y0) for px, py in pontos]
        espessura = max(2, round(largura))
        desenho.line(locais, fill=255, width=espessura, joint="curve")
        # Extremidades e bordas irregulares, semelhantes ao giz deitado.
        for px, py in locais:
            r = largura * self.rng.uniform(.34, .52)
            desenho.ellipse((px - r, py - r, px + r, py + r), fill=255)
        ruido = self.granulado[y0:y1, x0:x1]
        fibra = self.fibra[y0:y1, x0:x1]
        tinta = np.asarray(mascara, dtype=np.float32) / 255
        tinta *= (.70 + .30 * ruido)
        tinta *= np.where(ruido < (.025 + .07 * (1 - fibra)), .20, 1.0)
        cor = np.clip(cores[yi, xi] + self.rng.normal(0, 2.3, 3), 0, 255)
        papel = np.asarray(self.tela.crop((x0, y0, x1, y1)), dtype=np.float32)
        pigmento = np.clip(cor[None, None, :] * (.95 + .10 * ruido[..., None]), 0, 255)
        resultado = papel * (1 - tinta[..., None]) + pigmento * tinta[..., None]
        self.tela.paste(Image.fromarray(resultado.astype(np.uint8)), (x0, y0))

    def quadros(self, quantidade=144):
        yield self.tela.copy(), 0
        por_camada = max(1, (quantidade - 2) // len(self.camadas))
        feitos = 0
        for largura, cores, angulos, pontos in self.camadas:
            passo = max(1, math.ceil(len(pontos) / por_camada))
            for numero, (x, y) in enumerate(pontos, start=1):
                self.traco(x, y, largura, cores, angulos)
                feitos += 1
                if numero % passo == 0 or numero == len(pontos):
                    yield self.tela.copy(), feitos / self.total
        yield self.tela.copy(), 1


def executar(args):
    import tkinter as tk
    from tkinter import filedialog, messagebox
    from PIL import ImageTk

    root = tk.Tk()
    root.withdraw()
    foto = args.foto or filedialog.askopenfilename(title="Escolha a foto para pintar",
        filetypes=[("Imagens", "*.jpg *.jpeg *.png *.webp *.bmp *.tif *.tiff"),
                   ("Todos os arquivos", "*.*")])
    if not foto:
        root.destroy()
        return
    root.title("Pastel animado")
    root.configure(bg="#080809")
    legenda = tk.Label(root, text="Preparando os tracos...", bg="#080809",
                       fg="white", padx=12, pady=8)
    legenda.pack()
    canvas = tk.Label(root, bg="#080809")
    canvas.pack(padx=12)
    estado = {"imagem": None, "fechado": False}
    fila = queue.Queue(maxsize=3)
    gifs = []

    def guardar_gif(imagem):
        if args.gif:
            pequena = imagem.copy()
            pequena.thumbnail((420, 560), Image.Resampling.LANCZOS)
            gifs.append(pequena)

    def trabalho():
        try:
            pintura = PinturaPastel(foto, args.tamanho, args.semente)
            for imagem, progresso in pintura.quadros():
                while not estado["fechado"]:
                    try:
                        fila.put((imagem, progresso, None), timeout=.2)
                        break
                    except queue.Full:
                        continue
                if estado["fechado"]:
                    return
        except Exception as erro:
            fila.put((None, 0, str(erro)))

    def salvar():
        if estado["imagem"] is None:
            return
        destino = filedialog.asksaveasfilename(title="Salvar pintura", defaultextension=".png",
                                               initialfile="pintura_pastel.png",
                                               filetypes=[("Imagem PNG", "*.png")])
        if destino:
            try:
                estado["imagem"].save(destino)
            except OSError as erro:
                messagebox.showerror("Nao foi possivel salvar", str(erro))

    tk.Button(root, text="Salvar pintura em PNG", command=salvar).pack(pady=10)
    def atualizar():
        try:
            imagem, progresso, erro = fila.get_nowait()
        except queue.Empty:
            root.after(20, atualizar)
            return
        if erro:
            messagebox.showerror("Erro ao preparar a imagem", erro)
            root.destroy()
            return
        estado["imagem"] = imagem
        mostrada = imagem.copy()
        mostrada.thumbnail((root.winfo_screenwidth() - 80,
                            root.winfo_screenheight() - 190), Image.Resampling.LANCZOS)
        exibicao = ImageTk.PhotoImage(mostrada)
        canvas.configure(image=exibicao)
        canvas.image = exibicao
        guardar_gif(imagem)
        legenda.configure(text=f"Pintando... {progresso:.0%}" if progresso < 1 else "Pintura pronta")
        if progresso < 1:
            root.after(max(10, round(args.duracao * 1000 / 144)), atualizar)
        elif args.gif:
            try:
                salvar_gif(gifs, args.gif, args.duracao)
                legenda.configure(text=f"Pronto! GIF salvo em {args.gif}")
            except OSError as erro:
                messagebox.showerror("Nao foi possivel salvar o GIF", str(erro))

    def fechar():
        estado["fechado"] = True
        root.destroy()
    root.protocol("WM_DELETE_WINDOW", fechar)
    root.deiconify()
    threading.Thread(target=trabalho, daemon=True).start()
    root.after(20, atualizar)
    root.mainloop()


def salvar_gif(quadros, destino, duracao):
    Path(destino).parent.mkdir(parents=True, exist_ok=True)
    # Paleta global para reduzir tremulacao de cores entre quadros.
    paleta = quadros[-1].quantize(colors=256)
    convertidos = [q.quantize(palette=paleta, dither=Image.Dither.NONE) for q in quadros]
    tempos = [max(20, round(duracao * 1000 / len(quadros) / 10) * 10)] * len(quadros)
    tempos[-1] += 1800
    convertidos[0].save(destino, save_all=True, append_images=convertidos[1:],
                         duration=tempos, loop=0, optimize=False, disposal=1)


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
        for imagem, _ in pintura.quadros():
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
        executar(args)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError) as erro:
        raise SystemExit(f"Nao foi possivel criar a pintura: {erro}")
