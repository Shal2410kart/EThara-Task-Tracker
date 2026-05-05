from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.secret_key = "my_custom_secret_key_for_ethara"

# Database connection routing (Railway Postgres or Local)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///local_db.sqlite3')
if app.config['SQLALCHEMY_DATABASE_URI'].startswith("postgres://"):
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace("postgres://", "postgresql://", 1)

db = SQLAlchemy(app)

# --- DB Structure ---
class TeamMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    u_name = db.Column(db.String(50), unique=True)
    pass_word = db.Column(db.String(50))
    access_level = db.Column(db.String(20)) # 'Admin' or 'Member'

class ProjectTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_details = db.Column(db.String(200))
    current_status = db.Column(db.String(20), default="Pending")
    worker_id = db.Column(db.Integer, db.ForeignKey('team_member.id'))

# --- Setup Dummy Data ---
with app.app_context():
    db.create_all()
    if not TeamMember.query.first():
        boss = TeamMember(u_name="admin", pass_word="admin123", access_level="Admin")
        worker = TeamMember(u_name="user1", pass_word="user123", access_level="Member")
        db.session.add_all([boss, worker])
        db.session.commit()

# --- App Logic ---
@app.route('/', methods=['GET', 'POST'])
def auth_page():
    if request.method == 'POST':
        typed_user = request.form['username']
        typed_pass = request.form['password']
        
        found_user = TeamMember.query.filter_by(u_name=typed_user, pass_word=typed_pass).first()
        if found_user:
            session['user_id'] = found_user.id
            session['access'] = found_user.access_level
            return redirect('/panel')
        return "Wrong username or password!"
            
    return render_template('login.html')

@app.route('/panel')
def main_panel():
    if 'user_id' not in session:
        return redirect('/')
        
    if session['access'] == 'Admin':
        all_tasks = ProjectTask.query.all()
        all_staff = TeamMember.query.all()
        return render_template('dashboard.html', tasks=all_tasks, users=all_staff, role=session['access'])
    else:
        my_tasks = ProjectTask.query.filter_by(worker_id=session['user_id']).all()
        return render_template('dashboard.html', tasks=my_tasks, role=session['access'])

@app.route('/create_new', methods=['POST'])
def create_new():
    if session.get('access') == 'Admin':
        info = request.form['task_details']
        assignee = request.form['assign_to']
        t = ProjectTask(task_details=info, worker_id=assignee)
        db.session.add(t)
        db.session.commit()
    return redirect('/panel')

@app.route('/logoff')
def logoff():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)