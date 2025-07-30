from flask import Flask, render_template, session, make_response
from admin_routes import *
from flask_wtf import CSRFProtect
import base64


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:subburakesh2255@localhost/sxc"
app.secret_key = "kajsgf74rhisjbdfs"
csrf = CSRFProtect(app)
db.init_app(app)


@app.template_filter('b64encode')
def b64encode_filter(data):
    if data is None:
        return ''
    return base64.b64encode(data).decode('utf-8')

@app.route("/")
def home():
    return render_template("pages/home.html")

@app.route("/faculty")
def faculty():
    return render_template("pages/faculty.html")

@app.route("/download/certificate")
def download():
    return render_template("pages/download.html")

@app.route("/quiz/<string:slug>", methods=["GET", "POST"])
def quiz(slug):
    event = Events.query.filter_by(slugurl=slug).first()
    if not event:
        return "<center><h1>404 Not Found</h1></center>"

    now = datetime.datetime.now()
    today = now.date()
    current_time = now.time()

    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        regno = request.form.get("regno")

        # Check if already submitted
        existing = Responses.query.filter_by(eid=event.eid, email=email).first()
        if existing:
            flash("You've already submitted this quiz with this email. Please use a different email.", "danger")
            questions = Questions.query.filter_by(eid=event.eid).all()
            resp = make_response(render_template("public/quiz.html", event=event, questions=questions))
            resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            resp.headers["Pragma"] = "no-cache"
            return resp

        answers = {}
        for key in request.form:
            if key.startswith("qid_"):
                qid = key.split("_")[1]
                answers[int(qid)] = request.form[key]

        questions = Questions.query.filter_by(eid=event.eid).all()
        correct_answers = {q.qid: q.correct_answer for q in questions}
        scores = {q.qid: q.score for q in questions}

        marks_scored = sum(
            scores[qid] for qid in answers if qid in correct_answers and answers[qid] == correct_answers[qid]
        )
        total_score = sum(scores.values())
        percentage_secured = (marks_scored / total_score) * 100 if total_score > 0 else 0

        response = Responses(
            eid=event.eid,
            name_=name,
            email=email,
            regno=regno,
            percentage_secured=round(percentage_secured, 2)
        )
        db.session.add(response)
        db.session.commit()

        resp = make_response(render_template("public/thankyou.html",
                                             marks_scored=marks_scored,
                                             total_score=total_score,
                                             percentage_secured=percentage_secured,
                                             event=event))
        resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        resp.headers["Pragma"] = "no-cache"
        return resp

    if event.event_date == today and event.event_starttime <= current_time <= event.event_endtime:
        questions = Questions.query.filter_by(eid=event.eid).all()
        resp = make_response(render_template("public/quiz.html", event=event, questions=questions))
        resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        resp.headers["Pragma"] = "no-cache"
        return resp
    else:
        return render_template("public/waiting.html", event=event)

app.register_blueprint(admin_bp, url_prefix="/admin")

app.route("/")
if __name__ == "__main__":
    app.run(debug=True)