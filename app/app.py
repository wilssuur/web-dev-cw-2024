from flask import Flask, render_template, redirect, url_for
from flask_login import login_required, current_user
from mysqldb import DBConnector

app = Flask(__name__)
application = app
app.config.from_pyfile('config.py')

db_connector = DBConnector(app)

from authorization import bp as authorization_bp, init_login_manager
app.register_blueprint(authorization_bp)
init_login_manager(app)

from admin_action import bp as admin_action_bp
app.register_blueprint(admin_action_bp)

from events import bp as events_bp
app.register_blueprint(events_bp)

from records import bp as records_bp
app.register_blueprint(records_bp)

@app.route('/')
def index():
    if current_user.is_authenticated:
        query_events = ("SELECT events.id, events.name, events.short_desc, events.date_start, events.time_start, events.image_filename, "
                        "events.duration, events.user_id FROM events WHERE status_id=1 and events.date_start > NOW() "
                        "ORDER BY events.date_start asc")
        
        with db_connector.connect().cursor(named_tuple=True) as cursor_events:
            cursor_events.execute(query_events)
            data = cursor_events.fetchall()

        query_records = f"SELECT event_id FROM records WHERE user_id={current_user.id}"
        with db_connector.connect().cursor(named_tuple=True) as cursor_records:
            cursor_records.execute(query_records)
            records = cursor_records.fetchall()
    
        return render_template('index.html', events=data, records=records)
    else:
        return redirect(url_for('auth.auth'))


