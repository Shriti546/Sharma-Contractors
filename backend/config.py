import os

class Config:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
    
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'sharma-contractors-secret-key-2024-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f"sqlite:///{os.path.join(BACKEND_DIR, 'sharma_contractors.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload configuration - uses root images folder
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or os.path.join(BASE_DIR, 'images')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}
    
    # Admin credentials (change before going live)
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME') or 'admin'
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD') or 'sharma2024'
    
    # Business Info
    BUSINESS_NAME = 'SHARMA CONTRACTORS'
    BUSINESS_PHONE = '+91 8860442225'
    BUSINESS_PHONE2 = '+91 8076422029'
    BUSINESS_EMAIL = 'hello@sharmacontractors.com'
    BUSINESS_WHATSAPP = '918860442225'
    BUSINESS_WHATSAPP2 = '918076422029'
    BUSINESS_ADDRESS = 'New Delhi, India'
    BUSINESS_INSTAGRAM = 'https://instagram.com/sharmacontractors'
    BUSINESS_FACEBOOK = 'https://facebook.com/sharmacontractors'

