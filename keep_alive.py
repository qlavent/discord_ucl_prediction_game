# keep_alive.py

from flask import Flask
from threading import Thread
import os
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask('')


@app.route('/')
def home():
    return "I'm alive!"


@app.route('/health')
def health():
    return {"status": "healthy", "timestamp": time.time()}


def run():
    # Bind to the port that Render assigns or use port 8080 as default
    port = int(os.environ.get("PORT", 8080))
    try:
        app.run(host='0.0.0.0', port=port, debug=False)
    except Exception as e:
        logger.error(f"Flask app error: {e}")


def keep_alive():
    t = Thread(target=run, daemon=True)
    t.start()
    logger.info("Keep-alive server started")
