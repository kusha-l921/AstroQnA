from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'astro_qna.db')

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Models
class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    answers = db.relationship('Answer', backref='question', cascade='all, delete-orphan', lazy=True)

class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    text = db.Column(db.String(1000), nullable=False)
    votes = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/questions', methods=['GET'])
def get_questions():
    questions = Question.query.order_by(Question.created_at.desc()).all()
    data = []
    for q in questions:
        data.append({
            'id': q.id,
            'title': q.title,
            'created_at': q.created_at.isoformat(),
            'answers': [
                {'id': a.id, 'text': a.text, 'votes': a.votes, 'created_at': a.created_at.isoformat()}
                for a in sorted(q.answers, key=lambda x: x.created_at)
            ]
        })
    return jsonify(data)

@app.route('/api/questions', methods=['POST'])
def add_question():
    payload = request.get_json() or {}
    title = (payload.get('title') or '').strip()
    if not title:
        return jsonify({'error': 'Title required'}), 400
    q = Question(title=title)
    db.session.add(q)
    db.session.commit()
    return jsonify({'id': q.id, 'title': q.title, 'created_at': q.created_at.isoformat()}), 201

@app.route('/api/questions/<int:question_id>/answers', methods=['POST'])
def add_answer(question_id):
    payload = request.get_json() or {}
    text = (payload.get('text') or '').strip()
    if not text:
        return jsonify({'error': 'Answer text required'}), 400
    q = Question.query.get_or_404(question_id)
    a = Answer(question=q, text=text)
    db.session.add(a)
    db.session.commit()
    return jsonify({'id': a.id, 'text': a.text, 'votes': a.votes, 'created_at': a.created_at.isoformat()}), 201

@app.route('/api/answers/<int:answer_id>/vote', methods=['PUT'])
def vote_answer(answer_id):
    payload = request.get_json() or {}
    vote_type = payload.get('vote')
    a = Answer.query.get_or_404(answer_id)
    if vote_type == 'up':
        a.votes += 1
    elif vote_type == 'down':
        a.votes -= 1
    else:
        return jsonify({'error': 'Invalid vote type'}), 400
    db.session.commit()
    return jsonify({'id': a.id, 'votes': a.votes})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=8000)