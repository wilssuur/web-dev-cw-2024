from flask import render_template, request, redirect, url_for, flash, Blueprint, current_app
from flask_login import login_required, current_user
from mysql.connector.errors import DatabaseError
from app import db_connector
from authorization import can_user
from datetime import datetime
from werkzeug.utils import secure_filename
import uuid
import math
import os

bp = Blueprint('events', __name__, url_prefix='/events')
PAGE_COUNT = 5

EVENT_FIELDS = ['name', 'topic', 'start_date', 'start_time', 'duration', 'short_desc']
OPTIONAL_FIELDS = ['full_desc']
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def generate_unique_filename(filename):
    base, ext = os.path.splitext(filename)
    unique_name = uuid.uuid4().hex
    return f"{unique_name}{ext}"

def get_form_data(required_fields, optional_fields=None):
    event = {}
    all_filled = True
    for field in required_fields:
        value = request.form.get(field)
        if not value:
            all_filled = False
        event[field] = value
    if optional_fields:
        for field in optional_fields:
            event[field] = request.form.get(field)
    return event, all_filled


def get_topics():
    query = "SELECT * FROM topics"

    with db_connector.connect().cursor(named_tuple=True) as cursor:
        cursor.execute(query)
        topics = cursor.fetchall()
    return topics

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/create', methods=['POST', 'GET'])
@login_required
def create():
    topics = get_topics()
    if request.method == "GET":
        return render_template('user/new_event.html', topics=topics, event=None)
    
    event = {}
    event, all_filled = get_form_data(EVENT_FIELDS, OPTIONAL_FIELDS)
    if not all_filled:
        flash("Заполните все обязательные поля", category="danger")
        return render_template('user/new_event.html', topics=topics, event=event)

    if not request.files['file']:
        flash("Загрузите изображение", category="danger")
        return render_template('user/new_event.html', topics=topics, event=event)
    if not 'file' in request.files:
        flash("Ошибка загрузки изображения", category="danger")
        return render_template('user/new_event.html', topics=topics, event=event)
    
    file = request.files['file']
    filename = secure_filename(file.filename)
    filename = generate_unique_filename(filename)

    if not file and allowed_file(file.filename):
        flash("Неверный формат изображения", category="danger")
        return render_template('user/new_event.html', topics=topics, event=event)
    try:
        file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
    except Exception:
        flash("Ошибка сохранения изображения", category="danger")
        return render_template('user/new_event.html', topics=topics, event=event)
    
    event['user_id'], event['filename'] = current_user.id, filename
    query = ("INSERT INTO events "
             "(name, topic_id, date_start, time_start, duration, short_desc, full_desc, status_id, "
             "user_id, image_filename) VALUES (%(name)s, %(topic)s, %(start_date)s, "
             "%(start_time)s, %(duration)s, %(short_desc)s, %(full_desc)s, 3, %(user_id)s, %(filename)s)")
    try:
        with db_connector.connect().cursor(named_tuple=True) as cursor:
            cursor.execute(query, event)
            db_connector.connect().commit()
            flash("Мероприятие отправлено на проверку", category="success")
            return redirect(url_for('index'))
    except DatabaseError:
        flash("Ошибка базы данных", category="danger")
        db_connector.connect().rollback()
        return render_template('user/new_event.html', topics=topics, event=event)
    
@bp.route('/<int:event_id>/delete', methods=['POST'])
@login_required
@can_user('delete')
def delete(event_id):
    query_select = "SELECT image_filename FROM events WHERE id=%s"
    query_delete = "DELETE FROM events WHERE id=%s"
    
    try:
        with db_connector.connect().cursor(named_tuple=True) as cursor:
            cursor.execute(query_select, (event_id, ))
            event = cursor.fetchone()
            
            if event and event.image_filename:
                image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], event.image_filename)
                if os.path.exists(image_path):
                    os.remove(image_path)

            cursor.execute(query_delete, (event_id, ))
            db_connector.connect().commit()
            flash("Мероприятие успешно удалено", category="success")

    except DatabaseError as e:
        flash(f"Ошибка удаления данных: {str(e)}", category="danger")
        db_connector.connect().rollback()
    
    except OSError as e:
        flash(f"Ошибка удаления файла: {str(e)}", category="danger")

    return redirect(url_for('events.created'))


@bp.route('/<int:event_id>/show')
@login_required
def show(event_id):
    query = ("SELECT name, date_start, time_start, duration, short_desc, full_desc, image_filename "
        "FROM events WHERE id = %s")

    with db_connector.connect().cursor(named_tuple=True) as cursor:
        cursor.execute(query, (event_id, ))
        event = cursor.fetchone()

    return render_template('show_event.html', event=event)

@bp.route('/<int:event_id>/edit', methods=['GET', 'POST'])
@login_required
@can_user('edit')
def edit(event_id):
    topics = get_topics()
    if request.method == "GET":
        query = ("SELECT name, topic_id, date_start, time_start, duration, short_desc, full_desc "
                "FROM events WHERE id = %s")

        event = {}

        with db_connector.connect().cursor(named_tuple=True) as cursor:
            cursor.execute(query, (event_id, ))
            event = cursor.fetchone()

    if request.method == "POST":
        event = {}
        event, all_filled = get_form_data(EVENT_FIELDS, OPTIONAL_FIELDS)
        if not all_filled:
            flash("Заполните все обязательные поля", category="danger")
            return render_template('user/new_event.html', topics=topics, event=event)
        event['event_id'] = event_id

        query = ("UPDATE events SET name=%(name)s, topic_id=%(topic)s, "
                 "date_start=%(start_date)s, time_start=%(start_time)s, duration=%(duration)s, "
                 "short_desc=%(short_desc)s, full_desc=%(full_desc)s WHERE id=%(event_id)s")

        try:
            with db_connector.connect().cursor(named_tuple=True) as cursor:
                cursor.execute(query, event)
                db_connector.connect().commit()

            flash("Изменения успешно сохранены", category="success")
            return redirect(url_for('events.created'))
        except DatabaseError:
            flash("Ошибка редактирования мероприятия", category="danger")
            db_connector.connect().rollback()

    return render_template('user/edit_event.html', event=event, topics=topics)

@bp.route('/created')
@login_required
def created():
    page_number = request.args.get('page_number', 1, type = int)
    current_time = datetime.now()
    query = ("SELECT events.id, events.name, events.date_start, events.time_start, status.name as status "
             "FROM events JOIN status ON events.status_id = status.id WHERE events.user_id = %s "
             "ORDER BY events.status_id desc "
             f"LIMIT {PAGE_COUNT} OFFSET {PAGE_COUNT * (page_number - 1)}")
    
    query_count = ("SELECT COUNT(*) as count FROM events WHERE events.user_id = %s")

    with db_connector.connect().cursor(named_tuple=True) as cursor:
        cursor.execute(query, (current_user.id, ))
        data = cursor.fetchall()
        
        cursor.execute(query_count, (current_user.id, ))
        total_count = cursor.fetchone().count

        all_page = math.ceil(total_count / PAGE_COUNT)
        start_page = max(page_number - 3, 1)
        end_page = min(page_number + 3, all_page)

    return render_template('user/my_created_events.html',
                           events=data,
                           start_page=start_page, 
                           end_page=end_page, 
                           page_number=page_number, 
                           total_pages=total_count/PAGE_COUNT,
                           current_time=current_time,
                           datetime=datetime)


