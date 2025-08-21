import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY') or 'dev-secret-key'
    AI_API_URL = os.environ.get('AI_API_URL') or 'https://juenaferbabdar.beget.app/webhook/tekbot2'
    
    DB_HOST = os.environ.get('DB_HOST') or '147.45.138.77'
    DB_PORT = int(os.environ.get('DB_PORT') or 3306)
    DB_USER = os.environ.get('DB_USER') or 'tekbot'
    DB_PASSWORD = os.environ.get('DB_PASSWORD') or '77tanufe'
    DB_NAME = os.environ.get('DB_NAME') or 'tekbot'
    
    KANBAN_DB_HOST = os.environ.get('KANBAN_DB_HOST') or '147.45.138.77'
    KANBAN_DB_PORT = int(os.environ.get('KANBAN_DB_PORT') or 3306)
    KANBAN_DB_USER = os.environ.get('KANBAN_DB_USER') or 'tekman'
    KANBAN_DB_PASSWORD = os.environ.get('KANBAN_DB_PASSWORD') or 'Moloko123!'
    KANBAN_DB_NAME = os.environ.get('KANBAN_DB_NAME') or 'TEKMAN'
    
    if os.environ.get('TIMEWEB_APPS') == 'true':
        SQLALCHEMY_DATABASE_URI = 'sqlite:///app.db'
    else:
        SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
