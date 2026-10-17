# Pintura pastel animada

Versão em Python inspirada no efeito do vídeo enviado. Você escolhe uma foto e ela é reconstruída com traços de giz pastel sobre um fundo quase preto. Os traços começam largos e ficam menores para revelar os detalhes.

Abra `demonstracao.mp4` para ver o programa em ação. Esse exemplo foi convertido de GIF para MP4 para facilitar a reprodução e usa como entrada um recorte do resultado já pintado no vídeo; uma foto original dará uma base de melhor qualidade. Ele não usa a fotografia original do autor, que não foi fornecida.

## O que foi observado no vídeo

- Uma janela chamada “Oil Pastel” aparece sobre o VS Code.
- O arquivo visível é `flower.py`, com uma classe chamada `Pastel`.
- O código usa operações de NumPy e Pillow: imagem de referência, textura do papel, desfoque, gradientes e camadas de traços.
- A imagem de um buquê surge progressivamente em cores. O vídeo completo tem aproximadamente 12,7 segundos, incluindo a abertura e a tela final do Instagram.

A organização dos traços segundo os contornos pode ser inferida do cálculo dos gradientes e do tensor de estrutura visível. O vídeo não mostra o programa inteiro: esta é uma implementação independente, sem promessa de correspondência exata. A foto original do buquê não foi fornecida.

## Abrir no Windows

1. Instale Python 3.10 ou mais recente, com Tcl/Tk (a instalação padrão do Python para Windows costuma incluir esse componente).
2. Clone ou baixe o repositório e abra a pasta `Pastel_Animado`.
3. Abra `iniciar_windows.bat`. Na primeira execução, ele cria um ambiente local e instala Pillow e NumPy; essa etapa precisa de internet.
4. Escolha uma foto no seletor. Para um resultado próximo ao exemplo, use uma foto vertical de flores, colorida e com boa definição.
5. Aguarde a pintura e clique em **Salvar pintura em PNG**.

O programa roda no computador. Não há versão executável nem aplicativo Android neste pacote. O arquivo BAT foi preparado para Windows; a renderização e a exportação foram verificadas em modo sem janela no ambiente Linux de desenvolvimento.

## Pelo terminal / VS Code

Abra um terminal na pasta `Pastel_Animado`:

```sh
python -m venv .venv
```

Ative o ambiente no Windows:

```bat
.venv\Scripts\activate
```

Ou no Linux/macOS:

```sh
source .venv/bin/activate
```

Depois:

```sh
python -m pip install -r requirements.txt
python pastel.py
```

No Linux, a interface também precisa do pacote Tk do sistema, normalmente chamado `python3-tk`.

## Salvar a animação

Escolher a foto e ver a animação na janela, salvando o GIF ao terminar:

```sh
python pastel.py "minha_foto.jpg" --gif "animacao.gif"
```

Exportar a pintura e o GIF sem abrir janela:

```sh
python pastel.py "minha_foto.jpg" --sem-janela --png "pintura.png" --gif "animacao.gif"
```

O GIF tem lado maior de até 560 px e largura de até 420 px para limitar tamanho e memória. O PNG mantém a resolução configurada para a pintura. O GIF repete e segura a imagem pronta por mais 1,8 segundo. Não inclui áudio, filmagem do monitor ou marca d’água.

## Ajustes

- `--tamanho 1000`: aumenta o lado maior do PNG e o custo de processamento; padrão: 760. A foto não é ampliada se for menor.
- `--duracao 16`: duração aproximada da pintura; padrão: 12 segundos. A interface pode levar mais tempo em computadores lentos.
- `--semente 7`: muda a distribuição dos traços. A mesma foto e semente repetem o resultado.
- Em `flower_py/render.py`, no início da classe `PinturaPastel`, `fundo=(7, 7, 9)` define o fundo.
- `escalas` define as cinco espessuras de traço, da maior à menor; `limites` define quantos traços cada camada pode receber.

## Como funciona

1. Corrige a orientação da foto e reduz a resolução mantendo a proporção.
2. Prepara cinco versões desfocadas para amostrar as cores de cada camada.
3. Calcula os contornos e orienta os traços ao longo deles.
4. Distribui marcas curvas com cores retiradas da foto, bordas irregulares e pequenos vazios de pigmento.
5. Mostra a pintura progressivamente, das massas de cor aos detalhes.

Os traços permanecem visíveis no resultado: não é uma simples revelação da foto original por transparência. Para recriar também o enquadramento do vídeo, grave a janela sobre o VS Code com o celular na vertical após preparar a animação.
