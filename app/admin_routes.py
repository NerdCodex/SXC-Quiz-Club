from flask import Blueprint, render_template, request, redirect, url_for, session, g, Response, flash, jsonify, send_from_directory
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
import jwt, base64
from functools import wraps
from app.models import *
import datetime
import pandas as pd
from flask import send_file
from openpyxl import Workbook
from io import BytesIO
import os
from .extensions import cache, db


admin_bp = Blueprint('admin', __name__, template_folder='templates/admin')
UPLOAD_FOLDER = os.path.join(admin_bp.root_path, 'static', 'uploads', 'questions')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

JWT_SECRET = "kajsh98238rsiefb9if48heifh498rhweih"
JWT_ALGORITHM = "HS256"

def admin_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = session.get("jwt_token")
        if not token:
            return redirect(url_for("admin.login"))

        try:
            decoded = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            g.admin_user = Admin.query.filter_by(admin_email=decoded["email"]).first()
            if not g.admin_user:
                raise jwt.InvalidTokenError()
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            session.pop("jwt_token", None)
            return redirect(url_for("admin.login"))

        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        admin = Admin.query.filter_by(admin_email=email).first()

        if admin and check_password_hash(admin.admin_password, password):
            payload = {
                "email": email,
                "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
            }
            token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
            session["jwt_token"] = token
            return redirect(url_for("admin.events"))
        else:
            return render_template("login.html", error="Invalid credentials")

    if session.get("jwt_token"):
        return redirect(url_for("admin.events"))

    return render_template("login.html")


@admin_bp.route("/events", methods=["GET", "POST"])
@admin_login_required
def events():
    if request.method == "GET":
        events = Events.query.order_by(Events.event_date).all()
        for event in events:
            event.banner_base64 = base64.b64encode(event.event_banner).decode("utf-8")
        return render_template("events.html", events=events)
    elif request.method == "POST":
        event = Events(
            event_name=request.form["event_name"],
            event_description=request.form["event_description"],
            event_date=datetime.datetime.strptime(request.form["event_date"], "%Y-%m-%d").date(),
            event_starttime=datetime.datetime.strptime(request.form["event_starttime"], "%H:%M").time(),
            event_endtime=datetime.datetime.strptime(request.form["event_endtime"], "%H:%M").time(),
            event_banner=request.files["event_banner"].read()
        )
        db.session.add(event)
        db.session.commit()
        return redirect(url_for("admin.events"))
    else:
        return render_template("events.html")


@admin_bp.route("/events/edit/<int:eid>")
@admin_login_required
def edit_event(eid):
    tab = request.args.get("tab", "questions")  # default to 'questions'
    event = Events.query.get_or_404(eid)
    if tab == "questions":
        questions = Questions.query.filter_by(eid=eid).all()
        return render_template("event_edit.html", eid=eid, event=event, questions=questions, active_tab="questions")
    elif tab == "responses":
        page = request.args.get('page', 1, type=int)
        per_page = 10
        # Paginate responses related to the event
        responses = Responses.query.filter_by(eid=eid).order_by(Responses.rid).paginate(page=page, per_page=per_page, error_out=False)
        return render_template("event_edit.html", eid=eid, event=event, responses=responses, active_tab='responses')
    elif tab == "settings":
        return render_template("event_edit.html", eid=eid, event=event, active_tab=tab)
    elif tab == "certificates":
        certificates = Certificates.query.filter_by(eid=eid).all()
        return render_template("event_edit.html", eid=eid, event=event, active_tab=tab, certificates=certificates)
    else:
        return "<center><h1>404 Page Not Found!</h1></center>"


@admin_bp.route("/certificates/delete/<int:cid>", methods=["POST"])
@admin_login_required
def delete_certificate(cid):
    certificate = Certificates.query.get_or_404(cid)
    db.session.delete(certificate)
    db.session.commit()
    # Return JSON success, no redirect
    return jsonify({"status": "success"})

@admin_bp.route("/certificates/update/<int:cid>", methods=["POST"])
@admin_login_required
def update_certificate(cid):
    try:
        certificate = Certificates.query.get_or_404(cid)
        email = request.form.get('email')
        certificate_url = request.form.get('certificate_url')

        if not email or not certificate_url:
            return jsonify({'status': 'error', 'message': 'Email and Certificate URL are required'}), 400

        certificate.email = email
        certificate.certificate_url = certificate_url
        db.session.commit()

        return jsonify({'status': 'success', 'message': 'Certificate updated successfully'})

    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@admin_bp.route("/certificates/delete_all/<int:eid>", methods=["POST"])
@admin_login_required
def delete_all_certificates(eid):
    try:
        Certificates.query.filter_by(eid=eid).delete()
        db.session.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

@admin_bp.route("/upload-certificates", methods=["POST"])
@admin_login_required
def upload_certificates():
    eid = request.args.get("eid", type=int)
    file = request.files.get("certificate_file")

    if not file:
        flash("No file uploaded", "danger")
        return redirect(url_for("admin.edit_event", eid=eid, tab="certificates"))

    try:
        df = pd.read_excel(file)  # Requires openpyxl installed
        # Expected columns: email, certificate_url
        for _, row in df.iterrows():
            cert = Certificates(eid=eid, email=row["email"], certificate_url=row["certificate_url"])
            db.session.add(cert)
        db.session.commit()
        flash("Certificates uploaded successfully", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error uploading: {str(e)}", "danger")

    return redirect(url_for("admin.edit_event", eid=eid, tab="certificates"))


@admin_bp.route("/events/delete/<int:eid>", methods=["POST"])
@admin_login_required
def delete_event(eid):
    event = Events.query.get_or_404(eid)
    db.session.delete(event)
    db.session.commit()
    return redirect(url_for("admin.events"))

@admin_bp.route("/events/edit/<int:eid>/questions", methods=["POST"])
@admin_login_required
def questions_tab(eid):
    question_text = request.form.get("question_text")
    option_a = request.form.get("option_a")
    option_b = request.form.get("option_b")
    option_c = request.form.get("option_c")
    option_d = request.form.get("option_d")
    correct_answer = request.form.get("correct_answer")
    score = request.form.get("score")
    qid = request.form.get("qid")  # Editing if present

    remove_image = request.form.get("remove_image") == "1"
    image_file = request.files.get("question_image")

    filename = None
    if image_file and image_file.filename != "":
        # Save image to uploads folder
        filename = secure_filename(image_file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        image_file.save(filepath)
        # Store relative path for static serving
        filename = f"uploads/questions/{filename}"

    if qid:
        # Editing existing question
        question = Questions.query.get_or_404(qid)
        question.question = question_text
        question.option_a = option_a
        question.option_b = option_b
        question.option_c = option_c
        question.option_d = option_d
        question.correct_answer = correct_answer
        question.score = score

        if remove_image:
            try:
                image_full_path = os.path.join(UPLOAD_FOLDER, os.path.basename(question.image_path))
                if os.path.exists(image_full_path):
                    os.remove(image_full_path)
                question.image_path = None
            except Exception as e:
                # Optional: log the error instead of stopping execution
                admin_bp.logger.error(f"Failed to delete image file {question.image_path}: {e}")
        elif filename:
            question.image_path = filename  # New image path
        # else: keep existing image_path

    else:
        # Creating new question
        new_question = Questions(
            eid=eid,
            question=question_text,
            option_a=option_a,
            option_b=option_b,
            option_c=option_c,
            option_d=option_d,
            correct_answer=correct_answer,
            score=score,
            image_path=filename  # Path instead of blob
        )
        db.session.add(new_question)

    db.session.commit()
    cache.delete(f"questions_{eid}")
    print(f"questions_{eid}")
    return redirect(url_for("admin.edit_event", eid=eid, tab="questions"))

@admin_bp.route('/event_image/<int:eid>')
@admin_login_required
def event_image(eid):
    event = Events.query.get_or_404(eid)
    if event.event_banner:
        return Response(event.event_banner, mimetype='image/jpeg')  # or 'image/png' depending on your image
    return 'No image found', 404

@admin_bp.route("/events/update/<int:eid>", methods=["POST"])
@admin_login_required
def update_event(eid):
    event = Events.query.get_or_404(eid)

    # Get form data
    event_name = request.form.get("event_name")
    event_description = request.form.get("event_description")
    event_date = request.form.get("event_date")
    event_starttime = request.form.get("event_starttime")
    event_endtime = request.form.get("event_endtime")
    remove_event_image = request.form.get("remove_event_image")

    # Update text fields
    event.event_name = event_name
    event.event_description = event_description
    event.event_date = event_date
    event.event_starttime = event_starttime
    event.event_endtime = event_endtime

    # Handle image upload
    file = request.files.get("event_banner")
    if file and file.filename != "":
        event.event_banner = file.read()
    elif remove_event_image == "1":
        event.event_banner = None  # Remove the image if requested

    # Save the changes
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()

    return redirect(url_for("admin.edit_event", eid=eid))  


@admin_bp.route('/question_image/<int:qid>')
@admin_login_required
def question_image(qid):
    question = Questions.query.get_or_404(qid)
    if question.image_path:
        filename = os.path.basename(question.image_path)
        return send_from_directory(UPLOAD_FOLDER, filename)
    return 'No image found', 404


@admin_bp.route("/events/<int:eid>/questions/delete/<int:qid>", methods=["POST"])
@admin_login_required
def delete_question(eid, qid):
    question = Questions.query.get_or_404(qid)

    # Delete image file if exists
    if question.image_path:  # assuming DB column is `image_path`
        try:
            image_full_path = os.path.join(UPLOAD_FOLDER, os.path.basename(question.image_path))
            if os.path.exists(image_full_path):
                os.remove(image_full_path)
        except Exception as e:
            # Optional: log the error instead of stopping execution
            admin_bp.logger.error(f"Failed to delete image file {question.image_path}: {e}")

    # Delete question from DB
    db.session.delete(question)
    db.session.commit()

    return redirect(url_for("admin.edit_event", eid=eid, tab="questions"))


@admin_bp.route("/events/edit/<int:eid>/responses/download")
@admin_login_required
def download_responses(eid):
    responses = Responses.query.filter_by(eid=eid).all()

    # Create an Excel workbook and sheet
    wb = Workbook()
    ws = wb.active
    ws.title = "Responses"

    # Header row
    ws.append(["Name", "Email", "Reg No", "Percentage Secured"])

    # Data rows
    for r in responses:
        ws.append([r.name_, r.email, r.regno or "-", round(r.percentage_secured, 2)])

    # Save to in-memory file
    output = BytesIO()
    wb.save(output)
    output.seek(0)

    # Send file as download
    return send_file(
        output,
        as_attachment=True,
        download_name=f"event_{eid}_responses.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

@admin_bp.route("/manage", methods=["GET", "POST"])
@admin_login_required
def manage():
    tab = request.args.get("tab", "admins")
    self_delete_attempt = request.args.get("self_delete_attempt")

    if request.method == "POST" and tab == "resetpassword":
        email = request.form.get("email")
        currentpassword = request.form.get("currentpassword")
        newpassword = request.form.get("newpassword")

        admin = Admin.query.filter_by(admin_email=email).first()

        if not admin:
            flash("Admin not found.", "danger")
        elif not check_password_hash(admin.admin_password, currentpassword):
            flash("Current password is incorrect.", "danger")
        else:
            admin.admin_password = generate_password_hash(newpassword)
            db.session.commit()
            flash("Password updated successfully.", "success")
            return redirect(url_for("admin.manage", tab="resetpassword"))

        # If any error, re-render the form with error flashed
        return render_template("manage.html", active_tab="resetpassword")

    if tab == "admins":
        admins = Admin.query.all()
        return render_template(
            "manage.html",
            active_tab="admins",
            admins=admins,
            self_delete_attempt=self_delete_attempt
        )
    elif tab == "resetpassword":
        return render_template("manage.html", active_tab="resetpassword")

    return render_template("manage.html")


@admin_bp.route("/add_admin", methods=["POST"])
def add_admin():
    name = request.form.get("admin_name")
    email = request.form.get("admin_email")
    password = request.form.get("admin_password")

    # Check if email already exists
    existing_admin = Admin.query.filter_by(admin_email=email).first()
    if existing_admin:
        flash("Admin with this email already exists.", "danger")
        return redirect(request.referrer)

    # Create new admin
    hashed_password = generate_password_hash(password)
    new_admin = Admin(admin_name=name, admin_email=email, admin_password=hashed_password)

    db.session.add(new_admin)
    db.session.commit()
    flash("New admin added successfully!", "success")
    return redirect(request.referrer or url_for("admin.manage"))


@admin_bp.route("/delete_admin/<int:aid>", methods=["POST"])
@admin_login_required
def delete_admin(aid):
    admin = Admin.query.get_or_404(aid)

    if admin.admin_email == g.admin_user.admin_email:
        # Redirect with a flag
        return redirect(url_for("admin.manage", tab="admins", self_delete_attempt=1))

    db.session.delete(admin)
    db.session.commit()
    return redirect(url_for("admin.manage", tab="admins"))


@admin_bp.route("/gallery", methods=["GET"])
@admin_login_required
def gallery():
    images = Gallery.query.all()
    return render_template("admin/gallery.html", images=images)


@admin_bp.route("/gallery/save", methods=["POST"])
@admin_login_required
def save_image():
    gid = request.form.get("gid")
    desc = request.form.get("image_desc")
    file = request.files.get("image_file")

    if not desc:
        flash("Please enter a description.", "danger")
        return redirect(url_for("admin.gallery"))

    if gid:  # Edit
        img = Gallery.query.get_or_404(gid)
        img.image_desc = desc
        if file and file.filename != "":
            img.image = file.read()
        db.session.commit()
        flash("Image updated successfully!", "success")
    else:  # Add
        if not file or file.filename == "":
            flash("Please upload an image.", "danger")
            return redirect(url_for("admin.gallery"))
        new_img = Gallery(image=file.read(), image_desc=desc)
        db.session.add(new_img)
        db.session.commit()
        flash("Image added successfully!", "success")

    return redirect(url_for("admin.gallery"))


@admin_bp.route("/gallery/image/<int:gid>")
@admin_login_required
def get_image(gid):
    img = Gallery.query.get_or_404(gid)
    return send_file(BytesIO(img.image), mimetype="image/jpeg")


@admin_bp.route("/gallery/delete/<int:gid>", methods=["POST"])
@admin_login_required
def delete_image(gid):
    img = Gallery.query.get_or_404(gid)
    db.session.delete(img)
    db.session.commit()
    flash("Image deleted successfully!", "success")
    return redirect(url_for("admin.gallery"))


@admin_bp.route("/logout")
@admin_login_required
def logout():
    session.pop("jwt_token", None)
    return redirect(url_for("admin.login"))
