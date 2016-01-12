import os

SQLALCHEMY_DATABASE_URI = 'sqlite:///app.db'
basedir = '/root/Imview_server/'
UPLOAD_FOLDER = os.path.join(basedir, 'static')
SESSION_TYPE = 'memcached'
SECRET_KEY = '1299565b47f5cc4ba5db1010ebb4d543'
