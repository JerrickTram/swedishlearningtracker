from flask import Blueprint, render_template, redirect, url_for, flash, request
from .models import Word, QuizAttempt
from .forms import AddWordForm, QuizForm
from . import db
import random
from datetime import datetime
from collections import defaultdict

bp = Blueprint('main', __name__)

@bp.route('/')
def home():
    return render_template('home.html')

@bp.route('/add_word', methods=['GET', 'POST'])
def add_word():
    form = AddWordForm()
    if form.validate_on_submit():
        word = Word(
            swedish_word=form.swedish_word.data,
            english_translation=form.english_translation.data,
            tags=form.tags.data
        )
        db.session.add(word)
        db.session.commit()
        flash('Word added successfully!')
        return redirect(url_for('main.add_word'))
    
    return render_template('add_word.html', form=form)

@bp.route('/edit_word/<int:word_id>', methods=['GET', 'POST'])
def edit_word(word_id):
    word = Word.query.get_or_404(word_id)
    form = AddWordForm(obj=word)
    if form.validate_on_submit():
        word.swedish_word = form.swedish_word.data
        word.english_translation = form.english_translation.data
        word.tags = form.tags.data
        db.session.commit()
        flash('Word updated successfully!')
        return redirect(url_for('main.word_bank'))
    return render_template('edit_word.html', form=form, word=word)

@bp.route('/delete_word/<int:word_id>', methods=['POST'])
def delete_word(word_id):
    word = Word.query.get_or_404(word_id)
    db.session.delete(word)
    db.session.commit()
    flash('Word deleted successfully!')
    return redirect(url_for('main.word_bank'))

@bp.route('/quiz', methods=['GET', 'POST'])
def quiz():
    form = QuizForm()
    word_id = request.args.get('word_id')
    word = Word.query.get(word_id) if word_id else Word.query.order_by(db.func.random()).first()
    feedback = None

    if form.validate_on_submit():
        user_answer = form.answer.data.strip().lower()
        correct_answer = word.swedish_word.strip().lower()

        was_correct = user_answer == correct_answer

        attempt = QuizAttempt(word_id=word.id, was_correct=was_correct)
        db.session.add(attempt)

        if was_correct:
            word.correct_count += 1
            feedback = 'Correct!'
            flash('Correct!', 'success')
        else:
            word.incorrect_count += 1
            feedback = f'Incorrect! The correct answer was {word.swedish_word}'
            flash(f'Incorrect! The correct answer was {word.swedish_word}.', 'danger')

        db.session.commit()

    if request.method == 'GET' and request.args.get('next'):
        word = Word.query.order_by(db.func.random()).first()

    return render_template('quiz.html', form=form, word=word, feedback=feedback)

@bp.route('/stories')
def stories():
    return render_template('stories.html')

@bp.route('/metrics')
def metrics():
    words = Word.query.all()
    attempts = QuizAttempt.query.all()

    # Calculate total correct, total incorrect, and total accuracy
    total_correct = sum(word.correct_count for word in words)
    total_incorrect = sum(word.incorrect_count for word in words)
    total_attempts = total_correct + total_incorrect
    total_accuracy = (total_correct / total_attempts * 100) if total_attempts > 0 else 0

    # Calculate daily metrics
    daily_metrics = defaultdict(int)
    for attempt in attempts:
        date = attempt.timestamp.date()
        daily_metrics[date] += 1

    return render_template('metrics.html', total_correct=total_correct, total_incorrect=total_incorrect,
                           total_accuracy=total_accuracy, daily_metrics=daily_metrics)

@bp.route('/track_word/<int:word_id>/<action>')
def track_word(word_id, action):
    word = Word.query.get(word_id)
    if word:
        if action == 'correct':
            word.correct_count += 1
        elif action == 'incorrect':
            word.incorrect_count += 1
        db.session.commit()
    return redirect(url_for('main.quiz'))

@bp.route('/word_bank')
def word_bank():
    tag = request.args.get('tag')
    if tag:
        words = Word.query.filter(Word.tags.contains(tag)).order_by(Word.swedish_word).all()
    else:
        words = []
        
    all_words = Word.query.all()
    # Count tags
    tag_counts = defaultdict(int)
    for word in all_words:
        if word.tags:
            tags = [t.strip() for t in word.tags.split(',')]
            for tag in tags:
                tag_counts[tag] += 1

    # Sort tags by frequency
    sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)

    return render_template('word_bank.html', words=words, tag=tag, sorted_tags=sorted_tags)