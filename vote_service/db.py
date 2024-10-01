import os
import pymysql
from flask import g

def get_db():
    if 'db' not in g:
        g.db = pymysql.connect(
            host=os.getenv('RDS_HOST'),
            user=os.getenv('RDS_USER'),
            password=os.getenv('RDS_PASSWORD'),
            db=os.getenv('RDS_DB_NAME'),
            cursorclass=pymysql.cursors.DictCursor
        )
    return g.db

def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()
