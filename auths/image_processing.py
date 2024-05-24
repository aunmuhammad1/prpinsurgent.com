from io import BytesIO

from PIL import Image, ImageOps


def generate_thumbnail(image, width, height):
    """
    Create thumbnail.
    """
    im = Image.open(image)
    output = BytesIO()
    im = ImageOps.exif_transpose(im)
    if im.height > height and im.width > width:
        im.thumbnail((width, height), Image.ANTIALIAS)
    try:
        im.save(output, format="JPEG", optimize=True)
    except OSError:
        im = im.convert("RGB")
        im.save(output, format="JPEG", optimize=True)
    return output
