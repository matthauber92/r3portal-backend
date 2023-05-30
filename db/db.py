import os
from dotenv import load_dotenv, find_dotenv
import sqlalchemy as _sql
import sqlalchemy.orm as _orm

load_dotenv(find_dotenv())

db_name = os.getenv('DB_NAME')
db_user = os.getenv('DB_USER')
db_pass = os.getenv('DB_PASSWORD')
db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')


DATABASE_URL = 'postgresql://{}:{}@{}:{}/{}'.format(db_user, db_pass, db_host, db_port, db_name)

engine = _sql.create_engine(DATABASE_URL)

SessionLocal = _orm.sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    global db
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()
