#!/usr/bin/env python3
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from app import config

app = create_app()

if __name__ == "__main__":
    os.makedirs(config.CACHE_DIR, exist_ok=True)
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
