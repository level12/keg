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
