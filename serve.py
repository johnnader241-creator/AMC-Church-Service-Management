import os
from waitress import serve
from app import create_app

app = create_app()
serve(app, host='0.0.0.0', port=int(os.getenv('PORT', '5000')), threads=int(os.getenv('WEB_THREADS', '6')), connection_limit=int(os.getenv('WEB_CONNECTION_LIMIT', '200')))