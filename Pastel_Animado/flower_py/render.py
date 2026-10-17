"""Geração de traços e quadros, independente da interface."""
import math
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

    def numero_quadros(self, quantidade=144):
        return min(max(2, quantidade), self.total + 1)

    def quadros(self, quantidade=144):
        quantidade = self.numero_quadros(quantidade)
        yield self.tela.copy(), 0
        metas = iter(math.ceil(i * self.total / (quantidade - 1))
                     for i in range(1, quantidade))
        meta = next(metas)
        feitos = 0
        for largura, cores, angulos, pontos in self.camadas:
            for x, y in pontos:
                self.traco(x, y, largura, cores, angulos)
                feitos += 1
                if feitos == meta:
                    yield self.tela.copy(), feitos / self.total
                    meta = next(metas, None)


