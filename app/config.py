from __future__ import annotations

import os
from pathlib import Path


class Settings:
    host = os.getenv("MYLAB_HOST", "0.0.0.0")
    port = int(os.getenv("MYLAB_PORT", "8000"))
    data_dir = os.getenv(
        "MYLAB_DATA_DIR",
        str(Path(__file__).resolve().parent.parent / "data"),
    )


settings = Settings()
