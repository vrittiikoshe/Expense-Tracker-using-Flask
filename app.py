from flask import Flask, render_template, request, url_for, flash, redirect, Response
from flask_sqlalchemy import SQLAlchemy
from datetime import date, datetime, date as dt_date
from sqlalchemy import func
from flask import get_flashed_messages




app = Flask(__name__)

# Secret key
app.config['SECRET_KEY'] = 'secret123'

# Database config
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///expenses.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# Model
class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(120), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)


# Create DB
with app.app_context():
    db.create_all()


# Categories
CATEGORIES = ['Food', 'Transport', 'Rent', 'Utilities', 'Health']


# Helper function
def parse_date_or_none(s):
    if not s:
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        return None


# Home route
@app.route('/')
def index():
    start_str = (request.args.get("start") or "").strip()
    end_str = (request.args.get("end") or "").strip()
    selected_category = (request.args.get("category") or "").strip()

    start_date = parse_date_or_none(start_str)
    end_date = parse_date_or_none(end_str)

    if start_date and end_date and end_date < start_date:
        flash("End date cannot be before start date", "error")
        start_date = end_date = None
        start_str = end_str = ""

    q = Expense.query

    if start_date:
        q = q.filter(Expense.date >= start_date)
    if end_date:
        q = q.filter(Expense.date <= end_date)
    if selected_category:
        q = q.filter(Expense.category == selected_category)

    expenses = q.order_by(Expense.date.desc(), Expense.id.desc()).all()
    total = round(sum(e.amount for e in expenses), 2)

    # Pie chart (category-wise)
    cat_q = db.session.query(
        Expense.category,
        func.sum(Expense.amount)
    )

    if start_date:
        cat_q = cat_q.filter(Expense.date >= start_date)
    if end_date:
        cat_q = cat_q.filter(Expense.date <= end_date)
    if selected_category:
        cat_q = cat_q.filter(Expense.category == selected_category)

    cat_rows = cat_q.group_by(Expense.category).all()
    cat_labels = [c for c, _ in cat_rows]
    cat_values = [float(v or 0) for _, v in cat_rows]

    # Day chart (date-wise)
    day_q = db.session.query(
        Expense.date,
        func.sum(Expense.amount)
    )

    if start_date:
        day_q = day_q.filter(Expense.date >= start_date)
    if end_date:
        day_q = day_q.filter(Expense.date <= end_date)
    if selected_category:
        day_q = day_q.filter(Expense.category == selected_category)

    day_rows = day_q.group_by(Expense.date).order_by(Expense.date).all()
    day_labels = [d.isoformat() for d, _ in day_rows]
    day_values = [round(float(v or 0), 2) for _, v in day_rows]

    return render_template(
        'index.html',
        categories=CATEGORIES,
        expenses=expenses,
        today=date.today().isoformat(),
        total=total,
        start_str=start_str,
        end_str=end_str,
        selected_category=selected_category,
        cat_labels=cat_labels,
        cat_values=cat_values,
        day_labels=day_labels,
        day_values=day_values
    )


# Add expense
@app.route('/add', methods=['POST'])
def add():
    description = (request.form.get("description") or "").strip()
    amount_str = (request.form.get("amount") or "").strip()
    category = (request.form.get("category") or "").strip()
    date_str = (request.form.get("date") or "").strip()

    if not description or not amount_str or not category:
        flash("Please fill description, amount, category", "error")
        return redirect(url_for("index"))

    try:
        amount = float(amount_str)
        if amount <= 0:
            raise ValueError
    except ValueError:
        flash("Amount must be positive number", "error")
        return redirect(url_for("index"))

    try:
        d = datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else date.today()
    except ValueError:
        d = date.today()

    new_expense = Expense(
        description=description,
        amount=amount,
        category=category,
        date=d
    )

    db.session.add(new_expense)
    db.session.commit()

    flash("Expense added successfully", "success")
    return redirect(url_for("index"))


# Delete expense
@app.route('/delete/<int:expense_id>', methods=['POST'])
def delete(expense_id):
    e = Expense.query.get_or_404(expense_id)
    db.session.delete(e)
    db.session.commit()

    flash("Expense deleted", "success")
    return redirect(url_for("index"))

# Edit expense
@app.route('/edit/<int:expense_id>', methods=['GET'])
def edit(expense_id):
    e = Expense.query.get_or_404(expense_id)
    return render_template('edit.html', expense=e, categories=CATEGORIES, today=dt_date.today().isoformat())

@app.route('/edit/<int:expense_id>', methods=['POST'])
def edit_post(expense_id):
    e = Expense.query.get_or_404(expense_id)
    description = (request.form.get("description") or "").strip()
    amount_str = (request.form.get("amount") or "").strip()
    category = (request.form.get("category") or "").strip()
    date_str = (request.form.get("date") or "").strip()
    
    if not description or not amount_str or not category:
        flash("Please fill description, amount, category", "error")
        return redirect(url_for("edit", expense_id=expense_id))
    
    
    try:
        amount = float(amount_str)
        if amount <= 0:
            raise ValueError
    except ValueError:
        flash("Amount must be positive number", "error")
        return redirect(url_for("edit", expense_id=expense_id))
    
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else date.today()
    except ValueError:
        d = dt_date.today()
        
    if (
        e.description != description or
        e.amount != amount or
        e.category != category or
        e.date != d
    ):
        e.description = description
        e.amount = amount
        e.category = category
        e.date = d

        db.session.commit()
        flash("Expense updated successfully", "success")
    else:
        flash("No changes made", "error")
    

    return redirect(url_for("index"),code = 303)
    
    #return render_template('edit.html', expense=e, categories=CATEGORIES, today=dt_date.today().isoformat())

# Export CSV
@app.route('/export.csv')
def export_csv():
    start_str = (request.args.get("start") or "").strip()
    end_str = (request.args.get("end") or "").strip()
    selected_category = (request.args.get("category") or "").strip()

    start_date = parse_date_or_none(start_str)
    end_date = parse_date_or_none(end_str)

    q = Expense.query

    if start_date:
        q = q.filter(Expense.date >= start_date)
    if end_date:
        q = q.filter(Expense.date <= end_date)
    if selected_category:
        q = q.filter(Expense.category == selected_category)

    expenses = q.order_by(Expense.date, Expense.id).all()

    lines = ["Description,Amount,Category,Date"]
    for e in expenses:
        lines.append(f"{e.description},{e.amount:.2f},{e.category},{e.date.isoformat()}")

    csv_data = "\n".join(lines)

    fname_start = start_str or "all"
    fname_end = end_str or "all"
    filename = f"expenses_{fname_start}_to_{fname_end}.csv"

    return Response(
        csv_data,
        headers={
            "Content-Type": "text/csv",
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )
    get_flashed_messages()

# Run app
if __name__ == '__main__':
    app.run(debug=True)