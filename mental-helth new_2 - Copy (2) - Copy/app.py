from flask import Flask, render_template, request, redirect, url_for, session, make_response, jsonify
from models import db, UserSession, Admin
import os
from werkzeug.utils import secure_filename
from ai_engine import ai_engine

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key' # Change this in production
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mental_health.db'
app.config['UPLOAD_FOLDER'] = 'uploads'

db.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

# Register template filter for localization
from utils import localize_text
def localize_filter(text, lang='en'):
    return localize_text(text, lang)
app.jinja_env.filters['localize'] = localize_filter

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    # Capture lang from query param and store in session
    lang = request.args.get('lang')
    if lang:
        session['lang'] = lang

    if request.method == 'POST':
        user_age = int(request.form.get('age', 0))
        if user_age > 75:
            return "Age must be 75 or below.", 400
            
        action = request.form.get('action')
        session['user_info'] = request.form
        
        if action == 'complete':
            return redirect(url_for('complete_profile', lang=session.get('lang', 'en')))
            
        # Redirect to checkbox-based symptoms page
        return redirect(url_for('symptoms', lang=session.get('lang', 'en')))
    return render_template('profile.html')

@app.route('/complete-profile', methods=['GET', 'POST'])
def complete_profile():
    import uuid
    
    # Ensure user has basic profile info
    if 'user_info' not in session:
        return redirect(url_for('profile', lang=session.get('lang', 'en')))
    
    if request.method == 'POST':
        # Merge complete profile data with existing session info
        complete_info = request.form.to_dict()
        # Ensure ID is preserved if already generated
        if 'user_id' not in complete_info:
             complete_info['user_id'] = str(uuid.uuid4())[:8].upper()
             
        session['user_info'].update(complete_info)
        return redirect(url_for('symptoms', lang=session.get('lang', 'en')))
        
    # Generate a temporary user ID for display
    user_id = str(uuid.uuid4())[:8].upper()
    return render_template('complete_profile.html', user_id=user_id, basic_info=session.get('user_info', {}))

@app.route('/symptoms', methods=['GET', 'POST'])
def symptoms():
    """Checkbox-based symptom selection with AI-powered prediction"""
    # Ensure user has completed the profile first
    user_info = session.get('user_info')
    if not user_info:
        return redirect(url_for('profile', lang=session.get('lang', 'en')))
    
    if request.method == 'POST':
        # Handle symptom submission
        selected_symptoms = request.form.getlist('symptoms')
        
        if not selected_symptoms:
            return "Please select at least one symptom.", 400
        
        # Convert selected symptoms to a descriptive text for AI prediction
        symptom_text = convert_symptoms_to_text(selected_symptoms)
        
        # Use AI to predict top 3 conditions with confidence scores
        top_predictions = ai_engine.predict_top_diseases(symptom_text, top_n=3)
        
        # Get the primary prediction
        primary_prediction = top_predictions[0]['disease'] if top_predictions else "Unknown"
        
        # Save to DB with AI predictions
        new_session = UserSession(
            name=user_info['name'],
            age=user_info['age'],
            profession=user_info['profession'],
            language=session.get('lang', request.args.get('lang', 'en')), 
            selected_symptoms=f"{','.join(selected_symptoms)}"
        )
        db.session.add(new_session)
        db.session.commit()
        
        # Store predictions in session for report generation
        session['top_predictions'] = top_predictions
        session['selected_symptoms_list'] = selected_symptoms
        
        return redirect(url_for('generate_ai_report', session_id=new_session.id))
    
    return render_template('symptoms_carousel.html')

# --- Helper Functions ---

def convert_symptoms_to_text(symptom_list):
    """Convert checkbox symptom codes to descriptive text for AI"""
    symptom_descriptions = {
        'gad': 'excessive worry, anxiety, restlessness, difficulty relaxing',
        'gad_worry': 'constant worrying about everyday things',
        'gad_restless': 'feeling restless and on edge',
        'gad_fatigue': 'fatigue and tiredness',
        'gad_focus': 'difficulty concentrating',
        
        'depression': 'sadness, hopelessness, loss of interest in activities',
        'dep_sad': 'persistent sadness and emptiness',
        'dep_interest': 'loss of interest in hobbies and activities',
        'dep_energy': 'low energy and fatigue',
        'dep_appetite': 'changes in appetite and sleep',
        
        'stress': 'exhaustion, irritability, burnout from work or daily life',
        'stress_exhaust': 'extreme exhaustion and burnout',
        'stress_irrit': 'irritability and mood swings',
        'stress_conc': 'difficulty concentrating due to stress',
        
        'ocd': 'obsessive thoughts, compulsive behaviors, repetitive actions',
        'ocd_obses': 'intrusive obsessive thoughts',
        'ocd_comp': 'compulsive repetitive behaviors',
        
        'ptsd': 'flashbacks, nightmares, anxiety about past traumatic events',
        'ptsd_rexp': 're-experiencing traumatic events',
        'ptsd_avoid': 'avoiding reminders of trauma',
        
        'personality': 'unstable relationships, impulsive behavior, emotional instability',
        'pers_unstable': 'unstable and intense relationships',
        'pers_impulse': 'impulsive and risky behavior',
        
        'adhd': 'difficulty focusing, hyperactivity, impulsive actions',
        'adhd_att': 'inattention and difficulty focusing',
        'adhd_hyp': 'hyperactivity and restlessness',
        
        'autism': 'difficulty understanding social cues, communication challenges',
        'aut_social': 'difficulty with social interactions',
        'aut_comm': 'communication challenges',
        
        'eating': 'concerns about body image, weight, eating behaviors',
        'eat_body': 'negative body image concerns',
        'eat_habits': 'unhealthy eating patterns'
    }
    
    descriptions = [symptom_descriptions.get(s, s) for s in symptom_list]
    return "User reports experiencing: " + ", ".join(descriptions)

# --- AI Integration Routes ---

@app.route('/generate-ai-report/<int:session_id>')
def generate_ai_report(session_id):
    """Generate report using AI based on selected symptoms"""
    from utils import create_pdf_report, extract_advice_from_docx
    
    user_session = UserSession.query.get_or_404(session_id)
    
    # Get predictions from session
    top_predictions = session.get('top_predictions', [])
    
    # Extract the symptom text
    symptoms_raw = user_session.selected_symptoms
    symptom_list = [s.strip() for s in symptoms_raw.split(',')]
    full_symptom_description = convert_symptoms_to_text(symptom_list)
    
    # Get user's selected language
    user_lang = user_session.language or 'en'
    
    # Generate advice structure using extract_advice_from_docx with language support
    advice_data = extract_advice_from_docx(
        app.config['UPLOAD_FOLDER'], 
        symptoms_raw,  # Pass the raw symptom string
        lang=user_lang
    )
    
    # If no advice found from docx, fallback to AI-generated content
    if not advice_data:
        advice_data = ai_engine.generate_report_content(full_symptom_description)
    
    if not advice_data:
        return "AI Model not trained. Please ask admin to train the model first."

    # Generate PDF with the same advice data and language
    try:
        pdf_path = create_pdf_report(user_session, advice_data)
        filename = os.path.basename(pdf_path)
        
        # Verify PDF was created successfully
        full_path = os.path.join('static', filename)
        if not os.path.exists(full_path):
            print(f"ERROR: PDF file not found at {full_path}")
            return "Error: PDF generation failed. Please try again."
        
        print(f"PDF generated successfully: {full_path}")
        
    except Exception as e:
        print(f"ERROR generating PDF: {str(e)}")
        return f"Error generating PDF: {str(e)}"
    
    return render_template('report.html', 
                         user=user_session, 
                         advice=advice_data, 
                         pdf_file=filename,
                         top_predictions=top_predictions,
                         lang=user_lang)

@app.route('/ai-assessment')
def ai_assessment():
    """Legacy chat route - now redirects to symptoms"""
    return redirect(url_for('symptoms'))

@app.route('/api/chat', methods=['POST'])
def api_chat():
    """Legacy API - kept for compatibility but not used"""
    data = request.json
    user_msg = data.get('message')
    response = ai_engine.get_diagnosis(user_msg)
    return jsonify({"response": response})

@app.route('/generate-ai-report', methods=['POST'])
def generate_ai_report_route():
    """Legacy route - redirects to new flow"""
    return redirect(url_for('symptoms'))

@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'admin' and password == 'admin123':
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return "Invalid Credentials"
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    users = UserSession.query.order_by(UserSession.timestamp.desc()).all()
    total_users = UserSession.query.count()
    return render_template('admin_dashboard.html', users=users, total_users=total_users)

@app.route('/admin/upload', methods=['POST'])
def upload_file():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
        
    if 'file' not in request.files:
        return redirect(request.url)
    
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
        
    if file and file.filename.endswith('.docx'):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return redirect(url_for('admin_dashboard'))
    return "Invalid File Type"

@app.route('/admin/train-ai')
def train_ai():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    result = ai_engine.train_model()
    return f"Training Result: {result} <br> <a href='/admin/dashboard'>Back to Dashboard</a>"

@app.route('/admin/delete-user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    """Delete a specific user session from the database"""
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        user_session = UserSession.query.get(user_id)
        if user_session:
            db.session.delete(user_session)
            db.session.commit()
            return jsonify({'success': True, 'message': 'User deleted successfully'})
        else:
            return jsonify({'success': False, 'message': 'User not found'}), 404
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/report/<int:session_id>')
def generate_report(session_id):
    # This is the old route, kept for viewing historical reports if needed
    # But new reports go through generate_ai_report_route
    user_session = UserSession.query.get_or_404(session_id)
    # If it was an AI report, we might need to regenerate content or load saved JSON (which we don't save currently)
    # For now, this old route might fail for new AI sessions if we don't save the advice.
    # But the user asked to replace the system.
    return "Historical report viewing not fully implemented for AI sessions yet."

if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5001)
