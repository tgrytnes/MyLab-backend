from __future__ import annotations

import os


class Settings:
    host = os.getenv("MYLAB_HOST", "0.0.0.0")
    port = int(os.getenv("MYLAB_PORT", "8000"))
    demo_email = os.getenv("MYLAB_DEMO_EMAIL", "demo@mylab.app")
    demo_password = os.getenv("MYLAB_DEMO_PASSWORD", "demo123")
    demo_token = os.getenv("MYLAB_DEMO_TOKEN", "demo-token")


settings = Settings()
