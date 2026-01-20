import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    MODEL_NAME = "DeepPavlov/rubert-base-cased"
    MODEL_PATH = "data/trained_model"
    
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    
    API_VERSION = "v1"
    APP_NAME = "NLU Service"
    APP_DESCRIPTION = "Natural Language Understanding Service for Oil & Gas Commands"
    
config = Config()