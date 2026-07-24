import os
from pathlib import Path


def load_institute_asset():
    """Return institute logo path, name, and contact number.

    This repo currently has no dedicated institute settings table.
    We use defaults and look for optional logo under uploads.
    """
    institute_name = os.environ.get("INSTITUTE_NAME", "SCHOOL-ERP Institute")
    institute_contact = os.environ.get("INSTITUTE_CONTACT", "0000000000")

    # Optional: uploads/institute/logo.png
    logo_candidates = [
        Path("uploads") / "institute" / "logo.png",
        Path("uploads") / "institute_logo.png",
    ]
    logo_path = None
    for p in logo_candidates:
        if p.exists():
            logo_path = str(p)
            break

    return logo_path, institute_name, institute_contact
