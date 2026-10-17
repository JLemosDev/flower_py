"""Interface Tkinter e comunicação com as tarefas de fundo."""
import math
import queue
import threading
import time
from PIL import Image
from .render import PinturaPastel
from .export import salvar_gif
from .timing import quantidade_quadros


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
    exportacao = queue.Queue()
    inicio = None
    proximo = None
    gifs = []

    def guardar_gif(imagem):
        if args.gif:
            pequena = imagem.copy()
            pequena.thumbnail((420, 560), Image.Resampling.LANCZOS)
            gifs.append(pequena)

    def enviar(item):
        while not estado["fechado"]:
            try:
                fila.put(item, timeout=.2)
                return True
            except queue.Full:
                continue
        return False

    def trabalho():
        try:
            pintura = PinturaPastel(foto, args.tamanho, args.semente)
            quantidade = pintura.numero_quadros(quantidade_quadros(args.duracao))
            for indice, (imagem, progresso) in enumerate(pintura.quadros(quantidade)):
                alvo = args.duracao * indice / (quantidade - 1)
                if not enviar((imagem, progresso, None, alvo)):
                    return
        except Exception as erro:
            enviar((None, 0, str(erro), 0))

    def exportar():
        try:
            salvar_gif(gifs, args.gif, args.duracao)
            exportacao.put(None)
        except Exception as erro:
            exportacao.put(str(erro))

    def verificar_exportacao():
        try:
            erro = exportacao.get_nowait()
        except queue.Empty:
            root.after(50, verificar_exportacao)
            return
        if erro:
            messagebox.showerror("Nao foi possivel salvar o GIF", erro)
        else:
            legenda.configure(text=f"Pronto! GIF salvo em {args.gif}")

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
        nonlocal inicio, proximo
        if proximo is None:
            try:
                proximo = fila.get_nowait()
            except queue.Empty:
                root.after(20, atualizar)
                return
        imagem, progresso, erro, alvo = proximo
        if inicio is None:
            inicio = time.monotonic()
        restante = inicio + alvo - time.monotonic()
        if restante > 0:
            root.after(max(1, math.ceil(restante * 1000)), atualizar)
            return
        proximo = None
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
            root.after(1, atualizar)
        elif args.gif:
            legenda.configure(text="Salvando GIF...")
            # Concluir a gravação mesmo se a janela for fechada neste momento.
            threading.Thread(target=exportar, daemon=False).start()
            root.after(50, verificar_exportacao)

    def fechar():
        estado["fechado"] = True
        root.destroy()
    root.protocol("WM_DELETE_WINDOW", fechar)
    root.deiconify()
    threading.Thread(target=trabalho, daemon=True).start()
    root.after(20, atualizar)
    root.mainloop()


