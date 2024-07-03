import os

from PIL import Image


def convert_image_type_pillow(image_path: str, output_format: str) -> str:
    if not os.path.exists(image_path):
        raise FileNotFoundError("Image does not exist")

    if len(output_format) > 10 or output_format == "":
        raise ValueError("Extension string must be between 1 and 10")

    image = Image.open(image_path)
    image_base, _ = os.path.splitext(image_path)
    output_format = output_format.lower() if output_format.startswith(".") else f".{output_format.lower()}"
    output_path = f"{image_base}{output_format}"
    image.save(output_path, format=output_format)

    return output_path
