from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'Pastel_Animado'))
from pastel import PinturaPastel, salvar_gif, tempos_gif, quantidade_quadros


class PastelTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.source = self.base / 'input.png'
        y, x = np.mgrid[:32, :48]
        Image.fromarray(np.stack((x*5, y*7, (x+y)*3), axis=-1).astype('uint8')).save(self.source)

    def render(self, seed=42, count=13):
        p = PinturaPastel(self.source, 64, seed)
        frames = list(p.quadros(count))
        return p, frames

    def test_progress_and_unique_completion(self):
        p, frames = self.render()
        progress = [v for _, v in frames]
        self.assertEqual(len(frames), 13)
        self.assertEqual(progress[0], 0)
        self.assertEqual(progress[-1], 1)
        self.assertEqual(progress.count(1), 1)
        self.assertTrue(all(a < b for a, b in zip(progress, progress[1:])))
        self.assertEqual(frames[-1][0].tobytes(), p.tela.tobytes())

    def test_seed_and_frame_count_do_not_change_final_render(self):
        a, _ = self.render()
        b, _ = self.render(count=144)
        c, _ = self.render(seed=7)
        self.assertEqual(a.tela.tobytes(), b.tela.tobytes())
        self.assertNotEqual(a.tela.tobytes(), c.tela.tobytes())

    def test_resize_and_no_upscale(self):
        p, _ = self.render()
        self.assertEqual(p.foto.size, (48, 32))
        Image.new('RGB', (200, 100)).save(self.source)
        self.assertEqual(PinturaPastel(self.source, 100).foto.size, (100, 50))

    def test_tiny_and_missing_images(self):
        Image.new('RGB', (8, 8)).save(self.source)
        with self.assertRaises(ValueError):
            PinturaPastel(self.source)
        with self.assertRaises(OSError):
            PinturaPastel(self.base / 'missing.png')

    def test_timing_budget(self):
        for duration in (1, 1.234, 6, 12, 120):
            times = tempos_gif(quantidade_quadros(duration), duration)
            self.assertEqual(sum(times), round(duration*100)*10+1800)
            self.assertTrue(all(t >= 20 and t % 10 == 0 for t in times))

    def test_actual_gif_duration_and_final_frame(self):
        # Many distinct frames force the short-duration resampling path.
        frames = [Image.new('RGB', (16, 16), (i, 255-i, 100)) for i in range(144)]
        for duration in (1, 1.234, 12, 120):
            with self.subTest(duration=duration):
                dest = self.base / 'nested' / 'test.gif'
                salvar_gif(frames, dest, duration)
                with Image.open(dest) as gif:
                    times = []
                    for i in range(gif.n_frames):
                        gif.seek(i)
                        times.append(gif.info['duration'])
                    self.assertEqual(sum(times), round(duration*100)*10+1800)
                    self.assertEqual(gif.convert('RGB').getpixel((0, 0)), (143, 112, 100))
                    self.assertEqual(gif.info['loop'], 0)

    def test_empty_gif_rejected(self):
        with self.assertRaises(ValueError):
            salvar_gif([], self.base / 'empty.gif', 1)

    def cli(self, *args):
        return subprocess.run([sys.executable, str(ROOT / 'Pastel_Animado/pastel.py'), *map(str,args)],
                              capture_output=True, text=True, timeout=30, cwd=self.base)

    def test_cli_export(self):
        png, gif = self.base/'out.png', self.base/'out.gif'
        r = self.cli(self.source, '--sem-janela', '--duracao', 1, '--png', png, '--gif', gif)
        self.assertEqual(r.returncode, 0, r.stderr)
        with Image.open(png) as im:
            self.assertEqual(im.size, (48, 32))
        with Image.open(gif) as im:
            durations = []
            for i in range(im.n_frames):
                im.seek(i)
                durations.append(im.info['duration'])
            self.assertEqual(sum(durations), 2800)

    def test_invalid_cli(self):
        for args in [('--sem-janela',), ('--tamanho', '63'), ('--duracao', 'nan'),
                     ('--duracao', '0'), ('--duracao', '121')]:
            with self.subTest(args=args):
                r = self.cli(*args)
                self.assertEqual(r.returncode, 2)
                self.assertNotIn('Traceback', r.stderr)

    def test_import_does_not_require_tk(self):
        script = "import sys; sys.modules['tkinter']=None; import pastel"
        r = subprocess.run([sys.executable, '-c', script], cwd=ROOT/'Pastel_Animado',
                           capture_output=True, text=True, timeout=10)
        self.assertEqual(r.returncode, 0, r.stderr)


if __name__ == '__main__':
    unittest.main()
