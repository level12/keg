from blazeutils.strings import randchars

from keg.db import db


class Blog(db.Model):
    __tablename__ = 'blogs'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Unicode(50), unique=True, nullable=False)

    @classmethod
    def testing_create(cls):
        blog = Blog(title=randchars())
        db.session.add(blog)
        db.session.commit()
        return blog


####
# The next several entities exist to facilitate testing of the way Keg handles multiple database
# binds and dialects.
####

class PGDud(db.Model):
    __tablename__ = 'pgdud'
    __bind_key__ = 'postgres'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(50), unique=True, nullable=False)


class PGDud2(db.Model):
    __tablename__ = 'pgdud'
    __bind_key__ = 'postgres'
    __table_args__ = {'schema': 'fooschema'}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(50), unique=True, nullable=False)

    @classmethod
    def testing_create(cls):
        dud = cls(name=randchars())
        db.session.add(dud)
        db.session.commit()
        return dud


class SADud(db.Model):
    __tablename__ = 'sadud'
    __bind_key__ = 'sqlite2'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(50), unique=True, nullable=False)


class MSSQLDud(db.Model):
    __tablename__ = 'mssqldud'
    __bind_key__ = 'mssql'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(50), unique=True, nullable=False)


class MSSQLDud2(db.Model):
    __tablename__ = 'mssqldud'
    __bind_key__ = 'mssql'
    __table_args__ = {'schema': 'fooschema'}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(50), unique=True, nullable=False)

    @classmethod
    def testing_create(cls):
        dud = cls(name=randchars())
        db.session.add(dud)
        db.session.commit()
        return dud
