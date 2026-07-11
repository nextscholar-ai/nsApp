import os
from PIL import Image


def generate_qr_image(data: str, output_path: str) -> str:
    """Generates a QR image.

    Uses `qrcode` if available; otherwise creates a placeholder image.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    try:
        import qrcode

        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=2,
        )
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(output_path)
        return output_path
    except Exception:
        # Fallback placeholder (still keeps the module functional)
        img = Image.new("RGB", (512, 512), "white")
        # no-op placeholder; client can still download/view pdf
        img.save(output_path)
        return output_path

