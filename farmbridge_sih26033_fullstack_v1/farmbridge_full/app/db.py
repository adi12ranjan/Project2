import sqlite3
from pathlib import Path
from flask import g
DB_PATH=Path(__file__).resolve().parent.parent/'instance'/'farmbridge.db'
def get_db():
    if 'db' not in g:
        DB_PATH.parent.mkdir(exist_ok=True); g.db=sqlite3.connect(DB_PATH); g.db.row_factory=sqlite3.Row; g.db.execute('PRAGMA foreign_keys=ON')
    return g.db
def close_db(e=None):
    db=g.pop('db',None)
    if db: db.close()
def init_db(app):
    app.teardown_appcontext(close_db)
    with app.app_context():
        db=get_db(); db.executescript('''
CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,phone TEXT UNIQUE NOT NULL,password_hash TEXT NOT NULL,role TEXT NOT NULL CHECK(role IN ('farmer','consumer')),location TEXT DEFAULT '',created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS produce(id INTEGER PRIMARY KEY AUTOINCREMENT,farmer_id INTEGER NOT NULL,crop_name TEXT NOT NULL,quantity_kg REAL NOT NULL CHECK(quantity_kg>0),asking_price REAL NOT NULL CHECK(asking_price>=0),description TEXT DEFAULT '',location TEXT DEFAULT '',status TEXT NOT NULL DEFAULT 'available',created_at TEXT DEFAULT CURRENT_TIMESTAMP,FOREIGN KEY(farmer_id) REFERENCES users(id) ON DELETE CASCADE);
CREATE TABLE IF NOT EXISTS orders(id INTEGER PRIMARY KEY AUTOINCREMENT,produce_id INTEGER NOT NULL,consumer_id INTEGER NOT NULL,quantity_kg REAL NOT NULL CHECK(quantity_kg>0),total_amount REAL NOT NULL CHECK(total_amount>=0),status TEXT NOT NULL DEFAULT 'placed',created_at TEXT DEFAULT CURRENT_TIMESTAMP,FOREIGN KEY(produce_id) REFERENCES produce(id),FOREIGN KEY(consumer_id) REFERENCES users(id));'''); db.commit()
