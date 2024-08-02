from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from datetime import datetime
from pymongo import MongoClient
from bson.objectid import ObjectId
from utils import add_expense_from_chat
import csv
from io import StringIO

import logging

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.secret_key = 'your_secret_key'

@app.route('/setup', methods=['GET', 'POST'])
def setup():
    if request.method == 'POST':
        session['db_uri'] = request.form['db_uri']
        session['db_name'] = request.form['db_name']
        return redirect(url_for('login'))
    return render_template('setup.html')

def get_db():
    client = MongoClient(session['db_uri'])
    db = client[session['db_name']]
    return db

@app.context_processor
def inject_footer_text():
    db_uri = session.get('db_uri', '')
    if "mongodb.net" in db_uri:
        footer_text = "Powered by Mongo"
    elif "singlestore.com" in db_uri:
        footer_text = "Powered by SingleStore"
    else:
        footer_text = "Developed by Vishwa"
    return {'footer_text': footer_text}

@app.route('/')
def index():
    # Check if database connection details are in session
    if 'db_uri' not in session or 'db_name' not in session:
        return redirect(url_for('setup'))

    # Check if user is logged in
    if 'username' in session:
        db = get_db()
        transactions = db.transactions
        user_id = session['user_id']
        username = session['username']

        user_transactions = list(transactions.find({"user_id": ObjectId(user_id)}))

        # Ensure amounts are treated as floats for summation
        total_amount = sum(float(transaction['amount']) for transaction in user_transactions)
        total_upi = sum(float(transaction['amount']) for transaction in user_transactions if transaction['payment_method'] == 'UPI')
        total_cash = sum(float(transaction['amount']) for transaction in user_transactions if transaction['payment_method'] == 'Cash')

        return render_template('index.html', username=username, total_amount=total_amount, total_upi=total_upi, total_cash=total_cash)
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        db = get_db()
        users = db.users
        username = request.form['username']
        password = request.form['password']
        user = users.find_one({"username": username, "password": password})
        if user:
            session['user_id'] = str(user['_id'])
            session['username'] = user['username']
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password. Please try again.', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('setup'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        db = get_db()
        users = db.users
        username = request.form['username']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']
        existing_user = users.find_one({"username": username})
        if existing_user:
            flash('Username already exists. Please choose a different one.', 'error')
        else:
            users.insert_one({"username": username, "email": email, "phone": phone, "password": password})
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/transactions')
def transactions_view():
    if 'username' in session:
        db = get_db()
        transactions = db.transactions
        user_id = session['user_id']
        username = session['username']
        # user_transactions = list(transactions.find({"user_id": ObjectId(user_id)}))
        user_transactions = list(transactions.find({"user_id": ObjectId(user_id)}).sort("date", -1))
        return render_template('transaction.html', transactions=user_transactions, username=username)
    else:
        return redirect(url_for('login'))

@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    if 'username' in session:
        db = get_db()
        transactions = db.transactions
        user_id = session['user_id']
        date = request.form['date']
        category = request.form['category']
        amount = float(request.form['amount'])
        payment_method = request.form['payment_method']
        description = request.form['notes']

        transactions.insert_one({
            "user_id": ObjectId(user_id),
            "date": date,
            "category": category,
            "amount": amount,
            "payment_method": payment_method,
            "description": description
        })

        return redirect(url_for('transactions_view'))
    else:
        return redirect(url_for('login'))

@app.route('/delete_transaction/<transaction_id>', methods=['POST'])
def delete_transaction(transaction_id):
    if 'username' in session:
        db = get_db()
        transactions = db.transactions
        transactions.delete_one({"_id": ObjectId(transaction_id)})
        flash('Transaction deleted successfully.', 'success')
    else:
        flash('You must be logged in to delete a transaction.', 'error')
    return redirect(url_for('transactions_view'))

@app.route('/daily_spending_data', methods=['GET'])
def daily_spending_data():
    if 'username' in session:
        db = get_db()
        transactions = db.transactions
        user_id = session['user_id']

        month = request.args.get('month')
        year = request.args.get('year')

        pipeline = [
            {"$match": {"user_id": ObjectId(user_id)}},
            {"$match": {"date": {"$regex": f"^{year}-{month}"}}},
            {"$group": {"_id": "$date", "total_amount": {"$sum": "$amount"}}},
            {"$sort": {"_id": 1}}
        ]
        data = list(transactions.aggregate(pipeline))

        labels = [item['_id'] for item in data]
        amounts = [item['total_amount'] for item in data]

        return jsonify({'labels': labels, 'amounts': amounts})
    else:
        return redirect(url_for('login'))

@app.route('/current_month_spending_data', methods=['GET'])
def current_month_spending_data():
    if 'username' in session:
        db = get_db()
        transactions = db.transactions
        user_id = session['user_id']

        now = datetime.now()
        month = now.strftime('%m')
        year = now.strftime('%Y')

        pipeline = [
            {"$match": {"user_id": ObjectId(user_id)}},
            {"$match": {"date": {"$regex": f"^{year}-{month}"}}},
            {"$group": {"_id": "$date", "total_amount": {"$sum": "$amount"}}},
            {"$sort": {"_id": 1}}
        ]
        data = list(transactions.aggregate(pipeline))

        labels = [item['_id'] for item in data]
        amounts = [item['total_amount'] for item in data]

        return jsonify({'labels': labels, 'amounts': amounts})
    else:
        return redirect(url_for('login'))


@app.route('/monthly_spending_data')
def monthly_spending_data():
    if 'username' in session:
        db = get_db()
        transactions = db.transactions
        user_id = session['user_id']
        
        pipeline = [
            {"$match": {"user_id": ObjectId(user_id)}},
            {"$group": {"_id": {"$substr": ["$date", 0, 7]}, "total_amount": {"$sum": "$amount"}}}
        ]
        data = list(transactions.aggregate(pipeline))

        labels = [datetime.strptime(item['_id'], '%Y-%m').strftime('%b %Y') for item in data]
        amounts = [item['total_amount'] for item in data]

        return jsonify({'labels': labels, 'amounts': amounts})
    else:
        return redirect(url_for('login'))

@app.route('/statistics', methods=['GET', 'POST'])
def statistics():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    db = get_db()
    transactions = db.transactions
    user_id = session.get('user_id')
    
    if not user_id:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        month = request.form.get('month')
        year = request.form.get('year')
    else:
        now = datetime.now()
        month = now.strftime('%m')
        year = now.strftime('%Y')

    pipeline = [
        {"$match": {"user_id": ObjectId(user_id)}},
        {"$match": {"date": {"$regex": f"^{year}-{month}"}}}
    ]

    total_expenses_result = list(transactions.aggregate(pipeline + [
        {"$group": {"_id": None, "total_amount": {"$sum": "$amount"}}}
    ]))
    total_expenses = total_expenses_result[0]['total_amount'] if total_expenses_result else 0

    expense_by_category_result = list(transactions.aggregate(pipeline + [
        {"$group": {"_id": "$category", "total_amount": {"$sum": "$amount"}}}
    ]))
    expense_by_category = {item['_id']: item['total_amount'] for item in expense_by_category_result}

    top_spending_categories_result = list(transactions.aggregate(pipeline + [
        {"$group": {"_id": "$category", "total_amount": {"$sum": "$amount"}}},
        {"$sort": {"total_amount": -1}},
        {"$limit": 5}
    ]))
    top_spending_categories = {item['_id']: item['total_amount'] for item in top_spending_categories_result}

    return render_template('statistics.html', 
                           total_expenses=total_expenses, 
                           expense_by_category=expense_by_category,
                           top_spending_categories=top_spending_categories, 
                           selected_month=month, 
                           selected_year=year, 
                           datetime=datetime)

@app.route('/upload_csv', methods=['POST'])
def upload_csv():
    if 'username' in session:
        db = get_db()
        transactions = db.transactions
        user_id = session['user_id']

        # Check if the CSV file is present in the request
        if 'csv_file' not in request.files:
            return jsonify({"status": "error", "message": "No file part"})
        
        file = request.files['csv_file']
        if file.filename == '':
            return jsonify({"status": "error", "message": "No selected file"})

        if file and file.filename.endswith('.csv'):
            stream = StringIO(file.stream.read().decode("UTF8"), newline=None)
            csv_input = csv.reader(stream)

            headers = next(csv_input)
            required_headers = ["DATE", "CATEGORY", "AMOUNT", "PAYMENT_METHOD", "NOTES"]
            
            if not all(header in headers for header in required_headers):
                return jsonify({"status": "error", "message": "CSV file must contain DATE, CATEGORY, AMOUNT, PAYMENT_METHOD, NOTES headers"})

            for row in csv_input:
                date, category, amount, payment_method, notes = row
                transactions.insert_one({
                    "user_id": ObjectId(user_id),
                    "date": date,
                    "category": category,
                    "amount": float(amount),
                    "payment_method": payment_method,
                    "description": notes
                })
            
            return jsonify({"status": "success", "message": "Transactions imported successfully"})
        else:
            return jsonify({"status": "error", "message": "Invalid file format. Please upload a CSV file."})
    else:
        return redirect(url_for('login'))

@app.route('/ai_chat', methods=['GET', 'POST'])
def ai_chat():
    if 'username' in session:
        if request.method == 'POST':
            user_id = session['user_id']
            user_input = request.json.get('user_input')
            expenses = add_expense_from_chat(user_id, user_input)
            
            # Debugging: Print the expenses to verify their structure
            print("Expenses:", expenses)
            
            # Ensure expenses is always a list
            if isinstance(expenses, dict):
                expenses = [expenses]
            
            if expenses:
                db = get_db()
                transactions = db.transactions
                for expense in expenses:
                    # Ensure expense is a dictionary and has 'user_id' key
                    if isinstance(expense, dict) and 'user_id' in expense:
                        try:
                            expense['user_id'] = ObjectId(expense['user_id'])
                        except Exception as e:
                            print(f"Error converting user_id to ObjectId: {e}")
                            return jsonify({'status': 'error', 'message': 'Invalid user_id format.'})
                    else:
                        print("Expense format is invalid:", expense)
                        return jsonify({'status': 'error', 'message': 'Invalid expense format.'})
                    transactions.insert_one(expense)
                expenses = [convert_object_ids(expense) for expense in expenses]
                
                if 'history' not in session:
                    session['history'] = []
                
                session['history'].append({'type': 'user', 'content': user_input})
                session['history'].append({'type': 'bot', 'content': expenses})
                session.modified = True  # Mark the session as modified
                
                return jsonify({'status': 'success', 'message': 'Transaction(s) added successfully!', 'expenses': expenses})
            else:
                return jsonify({'status': 'error', 'message': 'No valid transaction found.'})
        return render_template('ai_chat.html', history=session.get('history', []))
    else:
        logging.info("User not logged in. Redirecting to login page.")
        return redirect(url_for('login'))


def convert_object_ids(expense):
    if '_id' in expense:
        expense['_id'] = str(expense['_id'])
    if 'user_id' in expense:
        expense['user_id'] = str(expense['user_id'])
    return expense


if __name__ == '__main__':
    app.run(debug=True)
