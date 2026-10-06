"""Shared image formats and orientation policy; no PDF dependencies."""
import os
from PIL import ImageOps


SUPPORTED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff', '.webp'}


def is_image_file(file_path):
    return os.path.splitext(file_path)[1].lower() in SUPPORTED_IMAGE_EXTENSIONS


def normalized_image_size(image, rotate_landscape=False):
    """Predict dimensions from EXIF metadata without allocating decoded pixels."""
    width, height = image.size
    exif = image.getexif()
    # Pillow may already expose oriented TIFF dimensions before decoding.
    # Use the stored raster dimensions so EXIF is accounted for exactly once.
    if image.format == 'TIFF':
        width, height = exif.get(256, width), exif.get(257, height)
    if exif.get(274) in (5, 6, 7, 8):
        width, height = height, width
    if rotate_landscape and width > height:
        width, height = height, width
    return width, height


def normalize_image_orientation(image, rotate_landscape=False):
    """Return an owned image: EXIF first, optional 90° counterclockwise second."""
    normalized = ImageOps.exif_transpose(image)
    if rotate_landscape and normalized.width > normalized.height:
        rotated = normalized.rotate(90, expand=True)
        normalized.close()
        return rotated
    return normalized
