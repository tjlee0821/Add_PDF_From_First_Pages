import os
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from PIL import Image, ImageOps
from pypdf import PdfReader
from reportlab.pdfgen import canvas

import gui
import image_utils
import pdf_utils


class RotationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1])
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)

    def image(self, size, orientation=None):
        path = self.directory / 'image.png'
        image = Image.new('RGB', size, 'white')
        # Asymmetric marker proves the direction of rotation, not just dimensions.
        image.putpixel((0, 0), (255, 0, 0))
        exif = image.getexif()
        if orientation is not None:
            exif[274] = orientation
        image.save(path, exif=exif)
        return str(path)

    def pdf(self, name, width=612, height=792, text='base'):
        path = str(self.directory / name)
        document = canvas.Canvas(path, pagesize=(width, height))
        document.drawString(40, 40, text)
        document.save()
        return path

    def converted_image(self, path, legacy, rotate=None):
        kwargs = {} if rotate is None else {'rotate_landscape': rotate}
        if legacy:
            output = image_utils.image_to_pdf(path, **kwargs)
            self.addCleanup(image_utils.cleanup_temp_files, [output])
        else:
            output = str(self.directory / 'converted.pdf')
            pdf_utils.image_to_pdf_page(path, output, **kwargs)
        return PdfReader(output).pages[0].images[0].image

    def test_default_preserves_landscape_in_both_converters(self):
        path = self.image((120, 60))
        for legacy in (False, True):
            with self.subTest(legacy=legacy):
                self.assertEqual(self.converted_image(path, legacy).size, (120, 60))

    def test_orientation_and_exif_in_both_converters(self):
        cases = [((120, 60), None), ((60, 120), None), ((60, 60), None),
                 ((120, 60), 6), ((60, 120), 6)]
        for size, orientation in cases:
            path = self.image(size, orientation)
            with Image.open(path) as source:
                normalized = ImageOps.exif_transpose(source)
                for rotate in (False, True):
                    expected = normalized
                    if rotate and normalized.width > normalized.height:
                        expected = normalized.rotate(90, expand=True)
                    for legacy in (False, True):
                        with self.subTest(size=size, exif=orientation, rotate=rotate, legacy=legacy):
                            actual = self.converted_image(path, legacy, rotate)
                            self.assertEqual(actual.size, expected.size)
                            # Legacy conversion uses JPEG; compare the marker's corner.
                            corners = [(0, 0), (actual.width-1, 0),
                                       (0, actual.height-1), (actual.width-1, actual.height-1)]
                            self.assertEqual(max(corners, key=lambda p: actual.getpixel(p)[0]-actual.getpixel(p)[1]),
                                             max(corners, key=lambda p: expected.getpixel(p)[0]-expected.getpixel(p)[1]))

    def test_pdf_passthrough_for_both_options(self):
        path = self.pdf('input.pdf', 400, 200)
        original = Path(path).read_bytes()
        for rotate in (False, True):
            self.assertEqual(pdf_utils.normalize_to_pdf(path, self.temp.name, rotate_landscape=rotate), (path, False))
            self.assertEqual(image_utils.files_to_pdf_list([path], rotate_landscape=rotate), ([path], []))
            self.assertEqual(Path(path).read_bytes(), original)

    def test_prepend_order_width_backup_and_cleanup(self):
        image = self.image((120, 60))
        for rotate in (False, True):
            base = self.pdf(f'base-{rotate}.pdf')
            insert = self.pdf(f'insert-{rotate}.pdf', 400, 200, 'insert')
            original = Path(base).read_bytes()
            before = set(self.directory.iterdir())
            backup = pdf_utils.prepend_pdfs(base, [image, insert], rotate_landscape=rotate)
            self.assertEqual(Path(backup).read_bytes(), original)
            pages = PdfReader(base).pages
            self.assertEqual(len(pages), 3)
            self.assertEqual(pages[0].images[0].image.size, (60, 120) if rotate else (120, 60))
            self.assertIn('insert', pages[1].extract_text())
            self.assertIn('base', pages[2].extract_text())
            self.assertEqual([float(p.mediabox.width) for p in pages], [400]*3)
            self.assertAlmostEqual(float(pages[1].mediabox.height), 200)
            self.assertAlmostEqual(float(pages[2].mediabox.height), 792*400/612, places=4)
            self.assertEqual(set(self.directory.iterdir())-before, {self.directory / 'tmp'}-before)

    def test_gui_insert_conversion_preserves_order_and_cleans_up(self):
        image = self.image((120, 60))
        insert = self.pdf('insert.pdf', text='insert')
        base = self.pdf('base.pdf')
        original = Path(base).read_bytes()
        pdfs, temporary = image_utils.files_to_pdf_list([image, insert], rotate_landscape=True)
        try:
            self.assertEqual(pdfs, [temporary[0], insert])
            backup = pdf_utils.prepend_pdfs(base, pdfs, rotate_landscape=True)
            self.assertEqual(Path(backup).read_bytes(), original)
            pages = PdfReader(base).pages
            self.assertEqual(pages[0].images[0].image.size, (60, 120))
            self.assertIn('insert', pages[1].extract_text())
            self.assertIn('base', pages[2].extract_text())
            self.assertEqual([float(page.mediabox.width) for page in pages], [612]*3)
        finally:
            image_utils.cleanup_temp_files(temporary)
        self.assertTrue(all(not os.path.exists(path) for path in temporary))

    def test_gui_checkbox_default_and_value_at_each_drop(self):
        root = Mock()
        with patch.object(gui.tk, 'Label'), patch.object(gui.tk, 'BooleanVar') as variable, \
             patch.object(gui.tk, 'Checkbutton') as checkbox:
            app = gui.App(root)
            variable.assert_called_once_with(master=root, value=False)
            self.assertEqual(checkbox.call_args.kwargs['text'], 'Rotate landscape images 90°')
        app.base_pdf = 'base.pdf'
        root.tk.splitlist.return_value = ['insert.png']
        app.rotate_landscape = Mock()
        app.rotate_landscape.get.side_effect = [False, True]
        with patch.object(gui, 'files_to_pdf_list', return_value=(['insert.pdf'], [])) as convert, \
             patch.object(gui, 'prepend_pdfs') as prepend, patch.object(gui, 'messagebox'):
            for rotate in (False, True):
                app.on_drop(SimpleNamespace(data='insert.png'))
                convert.assert_called_with(['insert.png'], rotate_landscape=rotate)
                prepend.assert_called_with('base.pdf', ['insert.pdf'], rotate_landscape=rotate)

    def test_gui_base_image_receives_option(self):
        app = gui.App.__new__(gui.App)
        app.root = Mock()
        app.root.tk.splitlist.return_value = ['base.png']
        app.base_pdf = None
        app.status = Mock()
        app.rotate_landscape = Mock()
        app.rotate_landscape.get.return_value = True
        with patch.object(gui, 'image_to_base_pdf', return_value='base.pdf') as convert, \
             patch.object(gui, 'cleanup_old_backups'), patch.object(gui, 'messagebox'):
            app.on_drop(SimpleNamespace(data='base.png'))
            convert.assert_called_once_with('base.png', rotate_landscape=True)
        with patch.object(gui, 'image_to_pdf_page') as convert:
            gui.image_to_base_pdf('base.png', rotate_landscape=True)
            self.assertTrue(convert.call_args.kwargs['rotate_landscape'])


if __name__ == '__main__':
    unittest.main()
