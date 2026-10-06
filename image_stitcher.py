"""Vertical image stitching using Pillow only, with preflight memory validation."""
import os
from pathlib import Path
import tempfile
import warnings

from PIL import Image
from image_processing import is_image_file, normalized_image_size, normalize_image_orientation


MAX_ESTIMATED_BYTES = 512 * 1024 * 1024


def stitch_images(image_paths, output_path, rotate_landscape=False):
    """Stitch the first frame of each input into a single lossless RGBA PNG.

    Keep supplied order, normalize to the widest oriented input, and never
    overwrite an input. Save atomically so errors leave an existing output intact.
    """
    paths = [Path(path) for path in image_paths]
    output = Path(output_path)
    if not paths:
        raise ValueError('Select at least one image to stitch.')
    if output.suffix.lower() != '.png':
        raise ValueError('Stitch Images output must be a PNG file.')

    for path in paths:
        if path.suffix.lower() == '.pdf':
            raise ValueError('PDF inputs are not supported in Stitch Images mode. Drop images only.')
        if not is_image_file(path):
            raise ValueError(f'Unsupported image format: {path.name}')
        if output.resolve() == path.resolve() or (output.exists() and os.path.samefile(path, output)):
            raise ValueError('The output must not overwrite a source image.')

    temporary = None
    try:
        with warnings.catch_warnings():
            # Keep Pillow's protections, and reject warnings before decoding.
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            sizes = []
            for path in paths:
                with Image.open(path) as source:
                    sizes.append(normalized_image_size(source, rotate_landscape))

            width = max(w for w, h in sizes)
            heights = [max(1, round(h * width / w)) for w, h in sizes]
            height = sum(heights)
            pixels = width * height
            # Canvas + decoding/orientation + RGBA conversion/resizing + encoder slack.
            estimated = (4 * pixels + 16 * max(w * h for w, h in sizes)
                         + 12 * width * max(heights) + 16 * 1024 * 1024)
            if (estimated > MAX_ESTIMATED_BYTES or max(width, height) >= 2**31
                    or (Image.MAX_IMAGE_PIXELS is not None and pixels > Image.MAX_IMAGE_PIXELS)):
                raise ValueError(
                    f'Stitched image is too large: {width} × {height} pixels '
                    f'(estimated {estimated / 1024**2:.0f} MiB). '
                    'Use fewer images or resize the inputs before stitching.'
                )

            with Image.new('RGBA', (width, height)) as stitched:
                y = 0
                for path, size, target_height in zip(paths, sizes, heights):
                    with Image.open(path) as source:
                        with normalize_image_orientation(source, rotate_landscape) as oriented:
                            if oriented.size != size:
                                raise ValueError(f'Image dimensions changed during stitching: {path.name}')
                            with oriented.convert('RGBA') as rgba:
                                if rgba.size == (width, target_height):
                                    stitched.paste(rgba, (0, y))
                                else:
                                    with rgba.resize((width, target_height), Image.Resampling.LANCZOS) as resized:
                                        stitched.paste(resized, (0, y))
                    y += target_height

                with tempfile.NamedTemporaryFile(dir=output.parent, suffix='.png', delete=False) as temp:
                    temporary = temp.name
                stitched.save(temporary, format='PNG')
            os.replace(temporary, output)
            temporary = None
    except (Image.DecompressionBombError, Image.DecompressionBombWarning) as error:
        raise ValueError('An input image is too large to process safely. Resize it before stitching.') from error
    except MemoryError as error:
        raise ValueError('Not enough memory to stitch these images. Use fewer or smaller inputs.') from error
    finally:
        if temporary is not None:
            os.remove(temporary)
    return str(output)
