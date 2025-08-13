from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from collections import defaultdict
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this to a secure secret key

# Configure SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///monitri_expenses.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Expense model
class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200))
    date = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Expense {self.id} - {self.category} - ${self.amount}>'
    
    def to_dict(self):
        """Convert expense to dictionary for JSON responses"""
        return {
            'id': self.id,
            'category': self.category,
            'amount': self.amount,
            'description': self.description or '',
            'date': self.date.strftime('%Y-%m-%d')
        }

@app.route('/')
def index():
    """Main dashboard page"""
    expenses = Expense.query.order_by(Expense.date.desc()).all()
    total = sum(exp.amount for exp in expenses)
    
    # Calculate today's expenses
    today = datetime.utcnow().date()
    today_expenses = [exp for exp in expenses if exp.date.date() == today]
    today_total = sum(exp.amount for exp in today_expenses)
    
    # Get unique categories
    categories = list(set(exp.category for exp in expenses))
    
    return render_template('index.html', 
                         expenses=expenses, 
                         total=total,
                         today_total=today_total,
                         category_count=len(categories))

@app.route('/add', methods=['POST'])
def add_expense():
    """Add new expense"""
    category = request.form.get('category', '').strip()
    amount_str = request.form.get('amount', '').strip()
    description = request.form.get('description', '').strip()
    
    # Validation
    if not category or not amount_str:
        flash('Category and Amount are required!', 'danger')
        return redirect(url_for('index'))
    
    try:
        amount = float(amount_str)
        if amount <= 0:
            flash('Amount must be greater than 0!', 'danger')
            return redirect(url_for('index'))
    except ValueError:
        flash('Amount must be a valid number!', 'danger')
        return redirect(url_for('index'))
    
    # Create new expense
    new_expense = Expense(
        category=category,
        amount=amount,
        description=description if description else None
    )
    
    try:
        db.session.add(new_expense)
        db.session.commit()
        flash('Expense added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error adding expense. Please try again.', 'danger')
        app.logger.error(f"Error adding expense: {e}")
    
    return redirect(url_for('index'))

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_expense(id):
    """Edit existing expense"""
    expense = Expense.query.get_or_404(id)
    
    if request.method == 'POST':
        category = request.form.get('category', '').strip()
        amount_str = request.form.get('amount', '').strip()
        description = request.form.get('description', '').strip()
        
        # Validation
        if not category or not amount_str:
            flash('Category and Amount are required!', 'danger')
            return redirect(url_for('edit_expense', id=id))
        
        try:
            amount = float(amount_str)
            if amount <= 0:
                flash('Amount must be greater than 0!', 'danger')
                return redirect(url_for('edit_expense', id=id))
        except ValueError:
            flash('Amount must be a valid number!', 'danger')
            return redirect(url_for('edit_expense', id=id))
        
        # Update expense
        expense.category = category
        expense.amount = amount
        expense.description = description if description else None
        
        try:
            db.session.commit()
            flash('Expense updated successfully!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash('Error updating expense. Please try again.', 'danger')
            app.logger.error(f"Error updating expense: {e}")
    
    return render_template('edit.html', expense=expense)

@app.route('/delete/<int:id>', methods=['POST'])
def delete_expense(id):
    """Delete expense"""
    expense = Expense.query.get_or_404(id)
    
    try:
        db.session.delete(expense)
        db.session.commit()
        flash('Expense deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting expense. Please try again.', 'danger')
        app.logger.error(f"Error deleting expense: {e}")
    
    return redirect(url_for('index'))

@app.route('/analytics')
def analytics():
    """Analytics page with charts and insights"""
    expenses = Expense.query.all()
    
    if not expenses:
        return render_template('analytics.html', 
                             categories=[], 
                             totals=[], 
                             total_expenses=0,
                             category_count=0,
                             avg_expense=0)
    
    # Group expenses by category
    category_totals = defaultdict(float)
    for expense in expenses:
        category_totals[expense.category] += expense.amount
    
    # Prepare data for charts
    categories = list(category_totals.keys())
    totals = list(category_totals.values())
    
    # Calculate statistics
    total_expenses = sum(totals)
    category_count = len(categories)
    avg_expense = total_expenses / len(expenses) if expenses else 0
    
    return render_template('analytics.html',
                         categories=categories,
                         totals=totals,
                         total_expenses=total_expenses,
                         category_count=category_count,
                         avg_expense=avg_expense)

@app.route('/api/expenses')
def api_expenses():
    """API endpoint to get all expenses as JSON"""
    expenses = Expense.query.order_by(Expense.date.desc()).all()
    return jsonify([expense.to_dict() for expense in expenses])

@app.route('/api/stats')
def api_stats():
    """API endpoint for dashboard statistics"""
    expenses = Expense.query.all()
    total = sum(exp.amount for exp in expenses)
    
    # Today's expenses
    today = datetime.utcnow().date()
    today_expenses = [exp for exp in expenses if exp.date.date() == today]
    today_total = sum(exp.amount for exp in today_expenses)
    
    # Categories
    categories = list(set(exp.category for exp in expenses))
    
    return jsonify({
        'total_expenses': total,
        'expense_count': len(expenses),
        'category_count': len(categories),
        'today_total': today_total
    })

@app.route('/api/analytics')
def api_analytics():
    """API endpoint for analytics data"""
    expenses = Expense.query.all()
    
    # Group by category
    category_totals = defaultdict(float)
    for expense in expenses:
        category_totals[expense.category] += expense.amount
    
    return jsonify({
        'categories': list(category_totals.keys()),
        'totals': list(category_totals.values())
    })

@app.errorhandler(404)
def not_found_error(error):
    flash('Page not found!', 'danger')
    return redirect(url_for('index'))

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    flash('An internal error occurred. Please try again.', 'danger')
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("Database tables created successfully!")
        print("Starting MoniTri Expense Tracker...")
        print("Visit: http://localhost:5000")
    
    app.run(debug=True, host='0.0.0.0', port=5000)