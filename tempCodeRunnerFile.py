# Day chart
    # day_q = db.session.query(
    #     Expense.date,
    #     func.sum(Expense.amount)
    # )
    # if start_date:
    #     day_q = day_q.filter(Expense.date >= start_date)
    # if end_date:
    #     day_q = day_q.filter(Expense.date <= end_date)
    # if selected_category:
    #     day_q = day_q.filter(Expense.category == selected_category)

    # day_rows = day_q.group_by(Expense.category).all()
    # print(day_rows)
    # day_labels = [c for c, _ in cat_rows]
    # day_values = [float(v) for _, v in cat_rows]
    # print(day_values)
    