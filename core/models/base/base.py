import sqlalchemy as _sql
from sqlalchemy.ext.declarative import declared_attr, declarative_base


class BaseModel(object):
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    id = _sql.Column(_sql.Integer, primary_key=True)


Base = declarative_base(cls=BaseModel)
