import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

# Define user names
users = ["Ashish Kumar", "Ankit Goyal", "Vishwajeet Dabholkar"]

# Define categories and their realistic expense ranges
categories = {
    "Entertainment": (100, 1000),
    "Food": (200, 5000),
    "Utilities": (100, 10000),
    "Education": (500, 20000),
    "Travel expenses": (500, 20000),
    "Gifts": (100, 5000),
    "Rent": (5000, 50000),
    "Subscriptions": (100, 2000)
}

# Define payment methods
payment_methods = ["UPI", "Cash", "Credit_Card"]

# Generate a date range from 1 Jan 2023 to today
start_date = datetime(2023, 1, 1)
end_date = datetime.now()
date_range = pd.date_range(start_date, end_date).to_pydatetime().tolist()

# Function to generate random transactions
def generate_transactions(user, date_range, categories, payment_methods):
    transactions = []
    notes_dict = {
        "Entertainment": ["Movie night", "Concert", "Live event", "Games"],
        "Food": ["Dinner", "Lunch", "Breakfast", "Snacks"],
        "Utilities": ["Electricity bill", "Water bill", "Internet bill", "Gas bill"],
        "Education": ["Course fee", "Books", "Online subscription", "Workshop"],
        "Travel expenses": ["Flight tickets", "Hotel booking", "Taxi fare", "Train tickets"],
        "Gifts": ["Birthday gift", "Anniversary gift", "Festival gift", "Surprise gift"],
        "Rent": ["House rent", "Office rent"],
        "Subscriptions": ["Streaming service", "Magazine subscription", "Gym membership", "Online service"]
    }

    for date in date_range:
        for _ in range(3):  # Approximately one transaction every 10 days per category
            for category, (min_expense, max_expense) in categories.items():
                amount = round(random.uniform(min_expense, max_expense), 2)
                payment_method = random.choice(payment_methods)
                note = random.choice(notes_dict.get(category, ["Sample note"]))
                transactions.append([date.strftime("%Y-%m-%d"), category, amount, payment_method, note])
    return transactions

# Generate transactions for each user
for user in users:
    user_transactions = generate_transactions(user, date_range, categories, payment_methods)
    
    # Create a DataFrame with the generated transactions
    columns = ["DATE", "CATEGORY", "AMOUNT", "PAYMENT_METHOD", "NOTES"]
    user_df = pd.DataFrame(user_transactions, columns=columns)
    
    # Save the generated data to CSV files for each user
    file_name = f"data/{user.replace(' ', '_')}_transactions.csv"
    user_df.to_csv(file_name, index=False)

print("CSV files generated successfully!")
