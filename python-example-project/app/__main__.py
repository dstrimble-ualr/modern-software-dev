"""Run the server: `python -m app` (PORT defaults to 8000)."""
import os

from . import create_app

create_app().run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
