from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import func, cast, String, Integer
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bnip.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(50), nullable=False)

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    report_type = db.Column(db.String(50), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    data = db.Column(db.JSON, nullable=False)
    user = db.relationship('User', backref='reports')

# Create tables
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='OSIAS CONTROLER').first():
        admin = User(username='OSIAS CONTROLER', password='0220Osias', role='admin')
        db.session.add(admin)
        db.session.commit()

# Context processors
@app.context_processor
def inject_user():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        return dict(current_user=user)
    return dict(current_user=None)

@app.context_processor
def inject_datetime():
    return dict(datetime=datetime, now=datetime.utcnow())

# Routes
@app.route('/')
def home():
    if 'user_id' in session:
        if session.get('role') == 'admin':
            return redirect(url_for('admin_dashboard'))
        elif session.get('role') == 'CHEF COMERCIAL':
            return redirect(url_for('commercial'))
        elif session.get('role') == 'CHEF DE PRODUCTION':
            return redirect(url_for('production'))
        elif session.get('role') == 'COMPTABLE':
            return redirect(url_for('comptable'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['user_id'] = user.id
            session['role'] = user.role
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
        else:
            new_user = User(username=username, password=password, role=role)
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))



@app.route('/admin')
def admin_dashboard():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Unauthorized access', 'danger')
        return redirect(url_for('login'))

    # Get all non-admin users and their reports
    workers = User.query.filter(User.role != 'admin').all()
    user_reports = {}
    
    for worker in workers:
        user_reports[worker.id] = {
            'user': worker,
            'reports': Report.query.filter_by(user_id=worker.id).order_by(Report.date.desc()).all()
        }

    # Calculate financial totals only from comptable reports
    comptable_reports = Report.query.join(User).filter(
        User.role == 'COMPTABLE'
    ).all()
    
    financial_totals = {
        'total_entrant': sum(float(r.data['frais_entrant']) for r in comptable_reports),
        'total_depenses': sum(float(r.data['frais_depenses']) for r in comptable_reports),
        'total_restant': sum(float(r.data['frais_restant']) for r in comptable_reports)
    }

    return render_template(
        'admin.html',
        user_reports=user_reports,
        financial_totals=financial_totals
    )



@app.route('/commercial', methods=['GET', 'POST'])
def commercial():
    if 'user_id' not in session or session.get('role') != 'CHEF COMERCIAL':
        flash('Unauthorized access', 'danger')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        data = {
            'type_produit': request.form['type_produit'],
            'nombre_produit': request.form['nombre_produit'],  # Added this line
            'prix_unitaire': request.form['prix_unitaire'],
            'valeur_total': request.form['valeur_total']
        }
        report = Report(
            user_id=session['user_id'],
            report_type='commercial',
            data=data
        )
        db.session.add(report)
        db.session.commit()
        flash('Report submitted successfully!', 'success')
        return redirect(url_for('commercial'))
    
    reports = Report.query.options(db.joinedload(Report.user)).filter_by(
        user_id=session['user_id'],
        report_type='commercial'
    ).order_by(Report.date.desc()).all()
    
    return render_template('commercial.html', reports=reports)

@app.route('/production', methods=['GET', 'POST'])
def production():
    if 'user_id' not in session or session.get('role') != 'CHEF DE PRODUCTION':
        flash('Unauthorized access', 'danger')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        data = {
            'type_produit': request.form['type_produit'],
            'nombre_nouveau': request.form['nombre_nouveau'],
            'nombre_stock': request.form['nombre_stock']
        }
        report = Report(
            user_id=session['user_id'],
            report_type='production',
            data=data
        )
        db.session.add(report)
        db.session.commit()
        flash('Report submitted successfully!', 'success')
        return redirect(url_for('production'))
    
    reports = Report.query.options(db.joinedload(Report.user)).filter_by(
        user_id=session['user_id'],
        report_type='production'
    ).order_by(Report.date.desc()).all()
    
    return render_template('production.html', reports=reports)




@app.route('/comptable', methods=['GET', 'POST'])
def comptable():
    if 'user_id' not in session or session.get('role') != 'COMPTABLE':
        flash('Unauthorized access', 'danger')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        frais_entrant = float(request.form['frais_entrant'])
        frais_depenses = float(request.form['frais_depenses'])
        
        data = {
            'frais_entrant': frais_entrant,
            'frais_depenses': frais_depenses,
            'frais_restant': frais_entrant - frais_depenses  # Automatically calculated
        }
        
        report = Report(
            user_id=session['user_id'],
            report_type='comptable',
            data=data
        )
        db.session.add(report)
        db.session.commit()
        flash('Report submitted successfully!', 'success')
        return redirect(url_for('comptable'))
    
    reports = Report.query.options(db.joinedload(Report.user)).filter_by(
        user_id=session['user_id'],
        report_type='comptable'
    ).order_by(Report.date.desc()).all()
    
    return render_template('comptable.html', reports=reports)

@app.route('/delete_report/<int:report_id>', methods=['POST'])
def delete_report(report_id):
    if 'user_id' not in session:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('login'))
    
    report = Report.query.get(report_id)
    
    if session.get('role') == 'admin' or (
        report.user_id == session['user_id'] and 
        report.date.date() == datetime.utcnow().date()
    ):
        db.session.delete(report)
        db.session.commit()
        flash('Report deleted successfully', 'success')
    else:
        flash('You are not authorized to delete this report', 'danger')
    
    return redirect(request.referrer or url_for('home'))






if __name__ == '__main__':
    app.run(debug=True)