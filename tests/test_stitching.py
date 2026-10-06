from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from PIL import Image, ImageOps

import gui
from image_stitcher import stitch_images


class StitchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1])
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.output = self.folder / 'stitched.png'

    def image(self, name, size, color, orientation=None):
        path = self.folder / name
        with Image.new('RGB', size, color) as image:
            image.putpixel((0, 0), (255, 255, 255))
            exif = image.getexif()
            if orientation:
                exif[274] = orientation
            image.save(path, exif=exif)
        return path

    def test_order_width_aspect_source_integrity_and_single_output(self):
        paths = [self.image('z.png', (10, 20), 'red'),
                 self.image('a.png', (20, 30), 'green'),
                 self.image('m.png', (5, 10), 'blue')]
        originals = [p.read_bytes() for p in paths]
        stitch_images(paths, self.output)
        with Image.open(self.output) as result:
            self.assertEqual(result.size, (20, 110))
            self.assertEqual(result.getpixel((10, 20)), (255, 0, 0, 255))
            self.assertEqual(result.getpixel((10, 50)), (0, 128, 0, 255))
            self.assertEqual(result.getpixel((10, 90)), (0, 0, 255, 255))
        self.assertEqual(originals, [p.read_bytes() for p in paths])
        self.assertEqual(set(self.folder.iterdir()), set(paths) | {self.output})

    def test_two_portraits(self):
        paths = [self.image('1.png', (10, 20), 'red'), self.image('2.png', (10, 30), 'blue')]
        stitch_images(paths, self.output)
        with Image.open(self.output) as result:
            self.assertEqual(result.size, (10, 50))
            self.assertEqual(result.getpixel((5, 19)), (255, 0, 0, 255))
            self.assertEqual(result.getpixel((5, 20)), (0, 0, 255, 255))

    def test_exif_before_optional_rotation_and_pixel_direction(self):
        for size, orientation in [((20, 10), None), ((10, 20), None), ((10, 10), None),
                                  ((20, 10), 6), ((10, 20), 6), ((20, 10), 5)]:
            path = self.image('source.png', size, 'red', orientation)
            for rotate in (False, True):
                with self.subTest(size=size, exif=orientation, rotate=rotate):
                    with Image.open(path) as source:
                        expected = ImageOps.exif_transpose(source)
                        if rotate and expected.width > expected.height:
                            expected = expected.rotate(90, expand=True)
                        expected = expected.convert('RGBA')
                    stitch_images([path], self.output, rotate_landscape=rotate)
                    with Image.open(self.output) as result:
                        self.assertEqual(result.size, expected.size)
                        self.assertEqual(result.tobytes(), expected.tobytes())

    def test_supported_formats(self):
        for suffix in ('jpg', 'jpeg', 'png', 'bmp', 'tif', 'tiff', 'webp'):
            with self.subTest(suffix=suffix):
                path = self.image('source.' + suffix, (12, 20), 'red')
                stitch_images([path], self.output)
                with Image.open(self.output) as result:
                    self.assertEqual(result.format, 'PNG')
                    self.assertEqual(result.size, (12, 20))

    def test_transparency(self):
        path = self.folder / 'alpha.png'
        Image.new('RGBA', (10, 20), (20, 30, 40, 100)).save(path)
        stitch_images([path], self.output)
        with Image.open(self.output) as result:
            self.assertEqual(result.getpixel((5, 5)), (20, 30, 40, 100))

    def test_reject_pdf_empty_and_non_png_output(self):
        pdf = self.folder / 'input.pdf'
        pdf.write_bytes(b'not a PDF to render')
        path = self.image('source.png', (10, 20), 'red')
        for paths, output, message in [([pdf], self.output, 'PDF'),
                                       ([], self.output, 'image'),
                                       ([path], self.folder / 'out.jpg', 'PNG')]:
            with self.subTest(paths=paths), self.assertRaisesRegex(ValueError, message):
                stitch_images(paths, output)
        self.assertFalse(self.output.exists())

    def test_source_overwrite_and_symlink_rejected(self):
        path = self.image('source.png', (10, 20), 'red')
        original = path.read_bytes()
        alias = self.folder / 'alias.png'
        alias.symlink_to(path)
        for output in (path, alias):
            with self.assertRaisesRegex(ValueError, 'source'):
                stitch_images([path], output)
        self.assertEqual(path.read_bytes(), original)

    def test_memory_limit_checked_before_pixel_decode_or_canvas(self):
        path = self.image('source.png', (10, 20), 'red')
        with patch('image_stitcher.MAX_ESTIMATED_BYTES', 1), \
             patch('image_stitcher.normalize_image_orientation') as normalize, \
             patch('image_stitcher.Image.new') as new:
            with self.assertRaisesRegex(ValueError, 'too large'):
                stitch_images([path], self.output)
            normalize.assert_not_called()
            new.assert_not_called()
        self.assertFalse(self.output.exists())

    def test_failed_save_preserves_existing_output_and_removes_temp(self):
        path = self.image('source.png', (10, 20), 'red')
        self.output.write_bytes(b'existing')
        with patch('PIL.Image.Image.save', side_effect=OSError('disk full')):
            with self.assertRaisesRegex(OSError, 'disk full'):
                stitch_images([path], self.output)
        self.assertEqual(self.output.read_bytes(), b'existing')
        self.assertEqual(set(self.folder.iterdir()), {path, self.output})

    def test_pillow_protection_and_memory_errors_are_clear(self):
        path = self.image('source.png', (10, 20), 'red')
        with patch('image_stitcher.Image.open', side_effect=Image.DecompressionBombError('large')):
            with self.assertRaisesRegex(ValueError, 'too large'):
                stitch_images([path], self.output)
        with patch('image_stitcher.Image.new', side_effect=MemoryError):
            with self.assertRaisesRegex(ValueError, 'Not enough memory'):
                stitch_images([path], self.output)
        self.assertFalse(self.output.exists())

    def test_all_exif_dimension_predictions_match_actual_orientation(self):
        from image_processing import normalized_image_size, normalize_image_orientation
        for suffix in ('png', 'jpg', 'tiff', 'webp'):
            for orientation in range(1, 9):
                path = self.image('exif.' + suffix, (20, 10), 'red', orientation)
                for rotate in (False, True):
                    with self.subTest(format=suffix, exif=orientation, rotate=rotate), Image.open(path) as source:
                        size = normalized_image_size(source, rotate)
                        with normalize_image_orientation(source, rotate) as actual:
                            self.assertEqual(size, actual.size)
                    stitch_images([path], self.output, rotate_landscape=rotate)
                    with Image.open(self.output) as result:
                        self.assertEqual(result.size, size)


class StitchGuiTests(unittest.TestCase):
    def app(self):
        app = gui.App.__new__(gui.App)
        app.root = Mock()
        app.root.tk.splitlist.return_value = ['z.png', 'a.png']
        app.mode = Mock()
        app.mode.get.return_value = gui.STITCH_MODE
        app.rotate_landscape = Mock()
        app.rotate_landscape.get.return_value = True
        app.base_pdf = 'existing.pdf'
        app.status = Mock()
        app.label = Mock()
        return app

    def test_drop_dispatch_order_and_no_pdf_calls(self):
        app = self.app()
        with patch.object(gui.filedialog, 'asksaveasfilename', return_value='result.png'), \
             patch.object(gui, 'stitch_images') as stitch, \
             patch.object(gui, 'prepend_pdfs') as prepend, \
             patch.object(gui, 'files_to_pdf_list') as convert, patch.object(gui, 'messagebox'):
            for rotate in (False, True):
                app.rotate_landscape.get.return_value = rotate
                app.on_drop(SimpleNamespace(data='drop'))
                stitch.assert_called_with(['z.png', 'a.png'], 'result.png', rotate_landscape=rotate)
            prepend.assert_not_called()
            convert.assert_not_called()
        self.assertEqual(app.base_pdf, 'existing.pdf')

    def test_pdf_rejected_before_dialog(self):
        app = self.app()
        app.root.tk.splitlist.return_value = ['z.png', 'input.pdf']
        with patch.object(gui.filedialog, 'asksaveasfilename') as dialog, \
             patch.object(gui, 'stitch_images') as stitch, patch.object(gui, 'messagebox') as messages:
            app.on_drop(SimpleNamespace(data='drop'))
            messages.showwarning.assert_called_once()
            self.assertIn('PDF', messages.showwarning.call_args.args[1])
            dialog.assert_not_called()
            stitch.assert_not_called()

    def test_cancel_and_failure_leave_base_untouched(self):
        app = self.app()
        for output in ('', 'result.png'):
            with patch.object(gui.filedialog, 'asksaveasfilename', return_value=output), \
                 patch.object(gui, 'stitch_images', side_effect=ValueError('too large')) as stitch, \
                 patch.object(gui, 'messagebox') as messages:
                app.on_drop(SimpleNamespace(data='drop'))
                self.assertEqual(app.base_pdf, 'existing.pdf')
                if output:
                    messages.showerror.assert_called_once()
                else:
                    stitch.assert_not_called()

    def test_mode_labels_and_restored_pdf_status(self):
        app = self.app()
        app.update_mode()
        self.assertIn('PNG', app.label.config.call_args.kwargs['text'])
        app.mode.get.return_value = gui.PDF_MODE
        app.update_mode()
        self.assertIn('existing.pdf', app.status.config.call_args.kwargs['text'])


if __name__ == '__main__':
    unittest.main()
