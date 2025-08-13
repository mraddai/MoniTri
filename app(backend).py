from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'addai'  # Replace with your own secret key

# Configure SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

# Expense model
class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200))
    date = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Expense {self.id} - {self.category} - {self.amount}>'

@app.route('/')
def index():
    expenses = Expense.query.order_by(Expense.date.desc()).all()
    total = sum(exp.amount for exp in expenses)
    return render_template('index.html', expenses=expenses, total=total)

@app.route('/add', methods=['POST'])
def add_expense():
    category = request.form.get('category')
    amount = request.form.get('amount')
    description = request.form.get('description')

    if not category or not amount:
        flash('Category and Amount are required!', 'danger')
        return redirect(url_for('index'))

    try:
        amount = float(amount)
    except ValueError:
        flash('Amount must be a number.', 'danger')
        return redirect(url_for('index'))

    new_expense = Expense(category=category, amount=amount, description=description)
    db.session.add(new_expense)
    db.session.commit()

    flash('Expense added successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_expense(id):
    expense = Expense.query.get_or_404(id)

    if request.method == 'POST':
        category = request.form.get('category')
        amount = request.form.get('amount')
        description = request.form.get('description')

        if not category or not amount:
            flash('Category and Amount are required!', 'danger')
            return redirect(url_for('edit_expense', id=id))

        try:
            amount = float(amount)
        except ValueError:
            flash('Amount must be a number.', 'danger')
            return redirect(url_for('edit_expense', id=id))

        expense.category = category
        expense.amount = amount
        expense.description = description
        db.session.commit()

        flash('Expense updated successfully!', 'success')
        return redirect(url_for('index'))

    return render_template('edit.html', expense=expense)

@app.route('/delete/<int:id>', methods=['POST'])
def delete_expense(id):
    expense = Expense.query.get_or_404(id)
    db.session.delete(expense)
    db.session.commit()
    flash('Expense deleted successfully!', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
