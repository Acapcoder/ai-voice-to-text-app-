from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from docx import Document
import os
import json
import threading
from ctransformers import AutoModelForCausalLM

app = Flask(__name__)
app.secret_key = 'hi5nine'

# Global variable to store the model
llama_model = None

# File paths
USER_FILE = 'data/users.json'
NOTE_FILE = 'data/notes.json'

os.makedirs('data', exist_ok=True)

def load_model():
    global llama_model
    model_path = "D:\project\model"
    print(f"Loading model from {model_path}...")
    llama_model = AutoModelForCausalLM.from_pretrained(model_path, model_type="llama")
    print("Model loaded successfully.")

threading.Thread(target=load_model).start()

def generate_summary(text):
    if llama_model is None:
        return "Model is still loading. Please try again in a moment."
    
    prompt = f"Please summarize the following text concisely:\n\n{text}\n\nSummary:"
    summary = llama_model(prompt, max_new_tokens=100, temperature=0.7, top_p=0.9)
    return summary.strip()

def load_json(file_path):
    if not os.path.exists(file_path):
        return []
    with open(file_path, 'r') as f:
        return json.load(f)

def save_json(file_path, data):
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

@app.route('/')
def home():
    return render_template('form.html')

@app.route('/signup', methods=['POST'])
def signup():
    full_name = request.form['full_name']
    email = request.form['email']
    password = request.form['password']
    confirm_password = request.form['confirm_password']

    if password != confirm_password:
        return 'Passwords do not match!', 400

    users = load_json(USER_FILE)
    if any(u['email'] == email for u in users):
        return 'Email already exists!', 400

    hashed_password = generate_password_hash(password)
    user_id = max([u['id'] for u in users], default=0) + 1

    users.append({
        'id': user_id,
        'full_name': full_name,
        'email': email,
        'password': hashed_password
    })

    save_json(USER_FILE, users)
    return redirect(url_for('home'))

@app.route('/signin', methods=['POST'])
def signin():
    email = request.form['email']
    password = request.form['password']

    users = load_json(USER_FILE)
    user = next((u for u in users if u['email'] == email), None)

    if not user or not check_password_hash(user['password'], password):
        return 'Incorrect email or password!', 400

    session['user_id'] = user['id']
    session['user_name'] = user['full_name']
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('home'))

    notes = load_json(NOTE_FILE)
    user_notes = [n for n in notes if n['user_id'] == session['user_id']]
    user_notes.sort(key=lambda x: x['created_at'], reverse=True)
    return render_template('dashboard.html', user_name=session['user_name'], notes=user_notes)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/save_note', methods=['POST'])
def save_note():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not authenticated'}), 403

    data = request.json
    note_text = data.get('note_text')
    note_id = data.get('note_id')
    current_time = datetime.now().isoformat()

    notes = load_json(NOTE_FILE)

    if note_id:
        for note in notes:
            if note['id'] == note_id and note['user_id'] == session['user_id']:
                note['note_text'] = note_text
                note['updated_at'] = current_time
                break
    else:
        new_id = max([n['id'] for n in notes], default=0) + 1
        note_id = new_id
        notes.append({
            'id': note_id,
            'user_id': session['user_id'],
            'note_text': note_text,
            'created_at': current_time,
            'updated_at': current_time
        })

    save_json(NOTE_FILE, notes)

    return jsonify({
        'status': 'success',
        'id': note_id,
        'note_text': note_text,
        'created_at': current_time,
        'updated_at': current_time
    })

@app.route('/get_note/<int:note_id>')
def get_note(note_id):
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not authenticated'}), 403

    notes = load_json(NOTE_FILE)
    note = next((n for n in notes if n['id'] == note_id and n['user_id'] == session['user_id']), None)

    if note:
        return jsonify({'status': 'success', 'note': note})
    return jsonify({'status': 'error', 'message': 'Note not found'}), 404

@app.route('/edit_note', methods=['POST'])
def edit_note():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not authenticated'}), 403

    data = request.json
    note_id = data.get('note_id')
    new_text = data.get('note_text')
    current_time = datetime.now().isoformat()

    notes = load_json(NOTE_FILE)
    for note in notes:
        if note['id'] == note_id and note['user_id'] == session['user_id']:
            note['note_text'] = new_text
            note['updated_at'] = current_time
            break

    save_json(NOTE_FILE, notes)

    return jsonify({'status': 'success', 'note_text': new_text, 'updated_at': current_time})

@app.route('/delete_note', methods=['POST'])
def delete_note():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not authenticated'}), 403

    note_id = request.json.get('note_id')
    notes = load_json(NOTE_FILE)
    notes = [n for n in notes if not (n['id'] == note_id and n['user_id'] == session['user_id'])]

    save_json(NOTE_FILE, notes)

    return jsonify({'status': 'success', 'message': 'Note deleted successfully'})

@app.route('/export_note', methods=['POST'])
def export_note():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 403

    note_id = int(request.form.get('note_id'))
    notes = load_json(NOTE_FILE)
    note = next((n for n in notes if n['id'] == note_id and n['user_id'] == session['user_id']), None)

    if not note:
        return jsonify({'error': 'Note not found'}), 404

    document = Document()
    document.add_paragraph(note['note_text'])

    os.makedirs('temp', exist_ok=True)
    filename = f"note_{note_id}.docx"
    filepath = os.path.join('temp', filename)
    document.save(filepath)

    return send_file(filepath, as_attachment=True, download_name=filename)

@app.route('/summarize', methods=['POST'])
def summarize():
    data = request.json
    text = data.get('text', '')

    if not text:
        return jsonify({'error': 'No text provided'}), 400

    try:
        summary = generate_summary(text)
        return jsonify({'summary': summary})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
