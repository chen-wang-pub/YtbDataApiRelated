from app.factory import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin


RecordList = db.Table('RecordList',
                      db.Column('id', db.Integer, primary_key=True),
                      db.Column('playlistId', db.Integer, db.ForeignKey('playlist.id')),
                      db.Column('recordId', db.Integer, db.ForeignKey('record.id'))
                      )

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    playlists = db.relationship('Playlist', backref='user')
    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Playlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    playlist_link = db.Column(db.String(512), index=True, unique=True)
    playlist_name = db.Column(db.String(256), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    records = db.relationship('Record', secondary=RecordList, backref=db.backref('playlists', lazy=True))
    def __repr__(self):
        return '<Playlist {}>'.format(self.playlist_link)


class Record(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(256), index=True)
    record_link = db.Column(db.String(512), index=True, unique=True)
    def __repr__(self):
        return '<Record {}>'.format(self.record_link)


@login.user_loader
def load_user(id):
    return User.query.get(int(id))
