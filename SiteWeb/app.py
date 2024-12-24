from flask import Flask, render_template, request, redirect, url_for, send_file
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_sqlalchemy import SQLAlchemy
from flask_login import current_user
from flask_socketio import SocketIO
from openpyxl import Workbook
from flask_admin.base import MenuLink
from flask import flash
from flask_admin.contrib.sqla import ModelView
from wtforms.validators import ValidationError
from werkzeug.utils import secure_filename
from flask_admin import Admin, AdminIndexView
import io
from flask_admin.form import Select2Field
from flask_socketio import SocketIO
import threading 
import socket
from _thread import *
from wtforms import form


app = Flask(__name__, template_folder='templates')
app.jinja_env.auto_reload = True

app.secret_key = 'your_secret_key'
socketio = SocketIO(app)


# Configuration de la base de données PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:1234.@localhost/bd'
db = SQLAlchemy(app)

# Configuration de Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


class UserAdminIndexView(AdminIndexView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == 'Admin'

    def inaccessible_callback(self, name, **kwargs):
        flash('You need to log in as an admin to access this page.', 'error')

        return redirect(url_for('login'))  # Redirect to the login page if user is not authenticated or not an admin

# Create Flask-Admin instance with custom index view
admin = Admin(app, name='Admin Panel', index_view=UserAdminIndexView())

# Add a custom navbar link
admin.add_link(MenuLink(name='User Dashboard', url='/dashboard_user'))
admin.add_link(MenuLink(name='Logout', url='/'))


# Define models
class EPF(UserMixin, db.Model):
    __tablename__ = 'epf'
    id = db.Column(db.Integer, primary_key=True)
    direction = db.Column(db.String(20))
    code = db.Column(db.String(20))
    separateur = db.Column(db.String(20))


class Report(db.Model):
    __tablename__ = 'report'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    description = db.Column(db.String(255))
    file = db.Column(db.LargeBinary)


class Séparateur(UserMixin, db.Model):
    __tablename__ = 'separateur'
    id = db.Column(db.Integer, primary_key=True)
    separateur = db.Column(db.String(20), unique=True)
    Type = db.Column(db.String(25))
    pression_separateur = db.Column(db.Float)
    debit_huile = db.Column(db.Float)
    volume_totale_pompe = db.Column(db.Float)
    debit_eau = db.Column(db.Float)
    debit_gaz = db.Column(db.Float)
    volume_totale_gaz = db.Column(db.Float)
    Date = db.Column(db.String(40))


class Région(UserMixin, db.Model):
    __tablename__ = 'region'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(50))
    code = db.Column(db.String(20))


class Ingenieur(UserMixin, db.Model):
    __tablename__ = 'utilisateurs'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(50))
    email = db.Column(db.String(50), unique=True)
    role = db.Column(db.String(50))


# Fonction de chargement de l'utilisateur pour Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return Ingenieur.query.get(int(user_id))

@app.route('/admin')
@login_required
def admin_panel():
    return redirect('/admin')  # Redirect to the Flask-Admin admin panel


class UserAdmin(ModelView):
    column_exclude_list = ('password',)
    form_choices = {
        'role': [
            ('Admin', 'Admin'),
            ('Ingenieur', 'Ingenieur')
        ],
    }
    

    def on_model_change(self, form, model, is_created):
        super().on_model_change(form, model, is_created)
        if is_created:
            separateur = model.separateur
            existing_separator = Séparateur.query.filter_by(separateur=separateur).first()
            if existing_separator and existing_separator.id != model.id:
                flash('A separator with the same name already exists.', 'error')
                raise ValidationError('A separator with the same name already exists.')




# Add your models to Flask-Admin
admin.add_view(UserAdmin(Ingenieur, db.session))
admin.add_view(UserAdmin(EPF, db.session))
admin.add_view(UserAdmin(Séparateur, db.session))
admin.add_view(UserAdmin(Région, db.session))


# Routes
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])

def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = Ingenieur.query.filter_by(username=username).first()

        if user and user.password == password:
            login_user(user)
            if user.role == 'Admin':
                return redirect(url_for('admin.index'))
            elif user.role == 'Ingenieur':
                return redirect(url_for('dashboard_user'))

        return render_template('login.html', message='Identifiants invalides')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/table')
@login_required
def table():
    separators = Séparateur.query.all()
    return render_template('table.html', separators=separators)


@app.route('/reports')
@login_required
def reports():
    # Fetch reports from the database
    reports = Report.query.all()
    return render_template('reports.html', reports=reports)


@app.route('/add_report', methods=['POST'])
@login_required

def add_report():
    name = request.form['report-name']
    description = request.form['report-description']
    file = request.files['report-file'].read()

    # Create a new report instance
    report = Report(name=name, description=description, file=file)

    # Add the report to the database
    db.session.add(report)
    db.session.commit()

    return redirect('/reports')


@app.route('/delete_report/<int:report_id>', methods=['POST'])
@login_required

def delete_report(report_id):
    # Retrieve the report from the database based on the report_id
    report = Report.query.get(report_id)

    if report:
        # Delete the report from the database
        db.session.delete(report)
        db.session.commit()

    return redirect('/reports')



@app.route('/edit_report/<int:report_id>', methods=['GET'])
@login_required

def edit_report(report_id):
    # Retrieve the report from the database based on the report_id
    report = Report.query.get(report_id)

    # Render the edit form template with the report information
    return render_template('edit_report.html', report=report)


@app.route('/update_report/<int:report_id>', methods=['POST'])
@login_required

def update_report(report_id):
    # Retrieve the report from the database based on the report_id
    report = Report.query.get(report_id)

    # Update the report with the new information from the form
    report.name = request.form['name']
    report.description = request.form['description']
    # Update other fields as needed

    # Commit the changes to the database
    db.session.commit()

    return redirect(url_for('reports'))


@app.route('/dashboard_user')
@login_required
def dashboard_user():
    username = current_user.username  # Assuming the username attribute exists in your User model
    return render_template('dashboard_user.html', username=username)


@app.route('/upload', methods=['POST'])
def upload():
    # Get the uploaded file from the request
    file = request.files['file']
    row_id = request.form['id']

    # Load the workbook
    wb = Workbook()

    # Select the active sheet
    sheet = wb.active

    # Read the data from the uploaded file
    for line in file:
        # Assuming the data is in CSV format, split the line by comma
        data = line.strip().split(',')
        # Write the data to the Excel sheet
        sheet.append(data)

    # Save the workbook
    wb.save(f'uploaded_data_{row_id}.xlsx')

    return redirect(url_for('dashboard_user'))




@socketio.on('connect', namespace='/test')
def test_connect():
    data = [x.json() for x in  Séparateur.select()]
    socketio.emit('newnumber', data, namespace='/test')
    print("first socket emitted")


@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected')

def insert_database(message):
    splitted_message = message.split(";")
    print(message)
    sep = Séparateur.query.filter_by ("0").first()
    sep.debit_huile = splitted_message[2]

    db.session.commit()
        # Input = name sep + ";"  + str(debi huile) + ";" + str(last_intensity)
    

thread = threading.Thread()
thread_stop_event = threading.Event()

def launch_socket_server():
    ServerSocket = socket.socket()
    host = '127.0.0.1'
    port = 5555
    ThreadCount = 0
    try:
        ServerSocket.bind((host, port))
    except socket.error as e:
        print(str(e))

    print('Waiting for a Connection..')
    ServerSocket.listen(5)

    while True:
        Client, address = ServerSocket.accept()
        print('Connected to: ' + address[0] + ':' + str(address[1]))
        start_new_thread(threaded_client, (Client,))
        ThreadCount += 1
        print('Thread Number: ' + str(ThreadCount))
    ServerSocket.close()


def threaded_client(connection):
    connection.send(str.encode('Welcome to the Servertest test '))
    while True:
        data = connection.recv(2048)
        reply = 'Server Says: ' + data.decode('utf-8')
        if not data:
            break
        insert_database(data.decode())
        splitted_message = data.decode().split(";")
        socketio.emit('newnumber', [{'Pression_Séparateur': splitted_message[2],
                                     'Debit_Huile': splitted_message[3],
                                     'Debit_Eau ': splitted_message[4],
                                     'Debit_Gaz ': splitted_message[5],
                                     'volume_totale_pompe':splitted_message[6],
                                     'Volume_Totale_Gaz ': splitted_message[7]}],
                      namespace='/test')
        print("socketio emitted", str.encode(reply), "\n")
    connection.close()

print("--------------------------starting sockte server---------------------------")
# creat_AdminRegion()
socketio.start_background_task(launch_socket_server)
print("-----21600---------------------starting flask server---------------------------")

if __name__ == '__main__':
    print('the server has started')
    socketio.run(app)
    print('the server has started')

#if __name__ == '__main__':
 #   app.run(debug=True)
