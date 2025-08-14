from flask import Blueprint, render_template, request, send_file, send_from_directory, make_response, jsonify, flash
from datetime import date
import datetime, base64, os
from io import BytesIO
from .extensions import cache, db
from .models import Events, Gallery, Certificates, Questions, Responses
from .admin_routes import UPLOAD_FOLDER


main_bp = Blueprint("main", __name__)

@main_bp.app_template_filter('b64encode')
def b64encode_filter(data):
    if data is None:
        return ''
    return base64.b64encode(data).decode('utf-8')

@main_bp.route("/")
def home():
    upcoming_events = Events.query.filter(Events.event_date >= date.today()) \
                                  .order_by(Events.event_date.asc()) \
                                  .limit(3) \
                                  .all()

    events_with_images = []
    for event in upcoming_events:
        banner_base64 = base64.b64encode(event.event_banner).decode('utf-8')
        events_with_images.append({
            "event_date": event.event_date,
            "event_name": event.event_name,
            "event_description": event.event_description,
            "banner_base64": banner_base64,
            "slugurl": event.slugurl
        })

    return render_template("pages/home.html", upcoming_events=events_with_images)


@main_bp.route("/faculty")
def faculty():
    return render_template("pages/faculty.html")

@main_bp.route('/gallery')
def gallery():
    images = Gallery.query.all()  # Fetch all rows from the Gallery table
    return render_template("pages/gallery.html", images=images)

@main_bp.route('/gallery/images/<int:gid>')
def get_image(gid):
    img = Gallery.query.get_or_404(gid)
    return send_file(BytesIO(img.image), mimetype='image/jpeg')

@main_bp.route("/download/certificate", methods=["GET", "POST"])
def download():
    if request.method == "GET":
        events = (
            Events.query
            .join(Certificates, Certificates.eid == Events.eid)
            .with_entities(Events.eid, Events.event_name)
            .distinct()
            .all()
        )
        return render_template("pages/download.html", events=events)
    elif request.method == "POST":
        data = request.get_json()
        email = data.get('email')
        eid = data.get('eid')
        
        if not email or not eid:
            return jsonify({'error': 'Missing email or event id'}), 400

        certificate = Certificates.query.filter_by(email=email, eid=eid).first()

        if certificate and certificate.certificate_url:
            return jsonify({'certificate_url': certificate.certificate_url})

        return jsonify({'certificate_url': None})
    else:
        return "<center><h1>404 Page Not Found!</h1></center>"


@main_bp.route("/quiz/<string:slug>", methods=["GET", "POST"])
def quiz(slug):
    event = Events.query.filter_by(slugurl=slug).first()
    if not event:
        return "<center><h1>404 Not Found</h1></center>", 404

    now = datetime.datetime.now()
    today, current_time = now.date(), now.time()

    if request.method == "GET":
        if event.event_date != today or not (event.event_starttime <= current_time <= event.event_endtime):
            return render_template("public/waiting.html", event=event)

    # Cache the questions by event ID
    cache_key = f"questions_{event.eid}"
    questions = cache.get(cache_key)
    if questions is None:
        questions = Questions.query.filter_by(eid=event.eid).all()
        cache.set(cache_key, questions)

    if request.method == "POST":
        if event.event_date != today or not (event.event_starttime <= current_time <= event.event_endtime):
            flash("Late Submission your response will not be taken into account.", "danger")
            return render_template("public/waiting.html", event=event)
        
        name = request.form.get("name")
        email = request.form.get("email")
        regno = request.form.get("regno")

        if Responses.query.filter_by(eid=event.eid, email=email).first():
            flash("You've already submitted this quiz with this email. Please use a different email.", "danger")
            return _nocache(render_template("public/quiz.html", event=event, questions=questions))

        answers = {
            int(key.split("_")[1]): value
            for key, value in request.form.items() if key.startswith("qid_")
        }

        correct_answers = {q.qid: q.correct_answer for q in questions}
        scores = {q.qid: q.score for q in questions}

        marks_scored = sum(
            scores[qid] for qid, ans in answers.items() if correct_answers.get(qid) == ans
        )
        total_score = sum(scores.values())
        percentage = (marks_scored / total_score * 100) if total_score else 0

        db.session.add(Responses(
            eid=event.eid, name_=name, email=email, regno=regno,
            percentage_secured=round(percentage, 2)
        ))
        db.session.commit()

        return _nocache(render_template(
            "public/thankyou.html",
            marks_scored=marks_scored,
            total_score=total_score,
            percentage_secured=percentage,
            event=event
        ))

    return _nocache(render_template("public/quiz.html", event=event, questions=questions))

def _nocache(response):
    if not hasattr(response, 'headers'):
        response = make_response(response)
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    return response

@main_bp.route('/question_image/<int:qid>')
def public_question_image(qid):
    question = Questions.query.get_or_404(qid)
    if question.image_path:
        filename = os.path.basename(question.image_path)
        return send_from_directory(UPLOAD_FOLDER, filename)
    return 'No image found', 404

