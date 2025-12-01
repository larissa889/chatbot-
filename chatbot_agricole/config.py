import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuration de l'application"""
    
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'votre-cle-secrete-dev')
    DEBUG = os.getenv('FLASK_DEBUG', 'True') == 'True'
    
    # API Météo
    OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY', '')
    
    # Base de données
    DATABASE_NAME = os.getenv('DATABASE_NAME', 'database.db')
    
    @staticmethod
    def init_app(app):
        pass