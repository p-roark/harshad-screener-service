"""Entry point for harshad-screener-service."""
import logging
import os
from app import app

logging.basicConfig(level=logging.INFO)

if __name__ == '__main__':
    import uvicorn
    host = os.environ.get('BIND_HOST', '127.0.0.1')
    port = int(os.environ.get('PORT', '8006'))
    uvicorn.run('app:app', host=host, port=port, reload=False, log_level='info')
