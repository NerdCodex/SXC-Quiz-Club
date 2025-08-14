from .extensions import db
from sqlalchemy import func
from sqlalchemy.orm import relationship, backref
from sqlalchemy.event import listens_for
from slugify import slugify
from sqlalchemy import UniqueConstraint



class Admin(db.Model):
    __tablename__ = "admins"

    aid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    admin_name = db.Column(db.String(200), nullable=False)
    admin_email = db.Column(db.String(200), nullable=False, unique=True)
    admin_password = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f"<Admin {self.admin_email}>"


class Events(db.Model):
    __tablename__ = 'events'

    eid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    event_name = db.Column(db.Text, nullable=False)
    event_description = db.Column(db.Text, nullable=False)
    event_date = db.Column(db.Date, nullable=False)
    event_starttime = db.Column(db.Time, nullable=False)
    event_endtime = db.Column(db.Time, nullable=False)
    event_banner = db.Column(db.LargeBinary, nullable=False)
    slugurl = db.Column(db.String(255), unique=True)

    # Define relationships with cascade delete
    questions = relationship('Questions', backref='event', cascade='all, delete-orphan')
    responses = relationship('Responses', backref='event', cascade='all, delete-orphan')
    certificates = relationship('Certificates', backref='event', cascade='all, delete-orphan')

    def generate_slug(self):
        base_slug = slugify(self.event_name)
        slug = base_slug
        counter = 1

        while Events.query.filter(func.lower(Events.slugurl) == slug.lower(), Events.eid != self.eid).first():
            slug = f"{base_slug}-{counter}"
            counter += 1

        self.slugurl = slug

    # def __repr__(self):
    #     return f"<Event(eid={self.eid}, name='{self.event_name}', date={self.event_date})>"

@listens_for(Events, 'before_insert')
def receive_before_insert(mapper, connection, target):
    target.generate_slug()

@listens_for(Events, 'before_update')
def receive_before_update(mapper, connection, target):
    target.generate_slug()


class Questions(db.Model):
    __tablename__ = 'questions'

    qid = db.Column(db.Integer, primary_key=True)
    eid = db.Column(db.Integer, db.ForeignKey('events.eid', ondelete='CASCADE'))
    question = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.String(255))
    option_b = db.Column(db.String(255))
    option_c = db.Column(db.String(255))
    option_d = db.Column(db.String(255))
    correct_answer = db.Column(db.String(1), nullable=False)
    image_path = db.Column(db.Text)
    score = db.Column(db.Integer, nullable=False, default=1)


class Responses(db.Model):
    __tablename__ = 'responses'

    rid = db.Column(db.Integer, primary_key=True)
    eid = db.Column(db.Integer, db.ForeignKey('events.eid', ondelete='CASCADE'))
    name_ = db.Column(db.Text, nullable=False)
    email = db.Column(db.String(255), nullable=False)
    regno = db.Column(db.Text)
    percentage_secured = db.Column(db.Float, nullable=False)

    __table_args__ = (
        UniqueConstraint('eid', 'email', name='unique_response_per_event'),
    )


class Certificates(db.Model):
    __tablename__ = 'certificates'

    cid = db.Column(db.Integer, primary_key=True)
    eid = db.Column(db.Integer, db.ForeignKey('events.eid', ondelete='CASCADE'))
    email = db.Column(db.Text, nullable=False)
    certificate_url = db.Column(db.Text, nullable=False)


class Gallery(db.Model):
    __tablename__ = "gallery"
    gid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    image = db.Column(db.LargeBinary, nullable=False)  # stores binary data
    image_desc = db.Column(db.Text, nullable=False)