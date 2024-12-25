import sqlite3
import numpy as np
import pandas as pd
from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import yfinance as yf
from sklearn.preprocessing import MinMaxScaler
from keras.models import load_model
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Use a strong secret key

# SQLite Database connection
def get_db_connection():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row  # This allows us to access columns by name
    return conn

# Route to create the database and user table (if not already created)
def create_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create the users table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        mobile TEXT NOT NULL
    )
    ''')
    conn.commit()
    conn.close()

# Call create_db to make sure the table is created when the app starts
create_db()

# Route to handle user signup
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        mobile = request.form.get('mobile')

        # Hash the password before storing it
        hashed_password = generate_password_hash(password)

        # Check if username already exists in the database
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        
        if user:
            conn.close()
            return render_template('signup.html', error='Username already exists.')

        # Insert new user with hashed password into the database
        conn.execute('INSERT INTO users (username, password, mobile) VALUES (?, ?, ?)', 
                     (username, hashed_password, mobile))
        conn.commit()
        conn.close()

        return redirect(url_for('login'))

    return render_template('signup.html')


# Route to handle the user dashboard (Display username and user details)
@app.route('/dashboard')
def dashboard():
    if 'logged_in' not in session:
        return redirect(url_for('login'))  # Redirect to login page if not logged in
    
    # Get the current user's username from the session
    username = session.get('username')
    
    # Query the database to get user details
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()

    if user:
        # Pass the user details to the template
        return render_template('index.html', user=user)
    else:
        return redirect(url_for('login'))  # Redirect if user not found


# Route to handle user login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Query database to check if user exists and password matches
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):  # Compare hashed passwords
            session['logged_in'] = True
            session['username'] = username  # Store the username in session
            return redirect(url_for('home'))  # Redirect to home page after successful login
        else:
            return render_template('login.html', error='Invalid credentials.')

    return render_template('login.html')

# Route to handle logout
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)  # Clear the username from session
    return redirect(url_for('home'))

# Home route
@app.route('/')
def home():
    if 'logged_in' in session:
        username = session.get('username')
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        # conn.close()
        return render_template('index.html', user=user)
    return render_template('index.html')  # If not logged in, render without user info

# Route to handle stock prediction
@app.route('/prediction')
def prediction():
    if 'logged_in' in session:
        return render_template('prediction.html')
    return redirect(url_for('login'))

# Route to handle learning page
@app.route('/learning')
def learning():
    if 'logged_in' in session:
        username = session.get('username')
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        return render_template('learning.html', user=user)
    return redirect(url_for('login'))

# Route to fetch stock data and make predictions
@app.route('/fetch-data', methods=['POST'])
def fetch_data():
    data = request.json
    ticker = data.get('ticker')
    start_date = data.get('start_date')
    end_date = data.get('end_date')

    try:
        df = yf.download(ticker, start=start_date, end=end_date)
        if df.empty:
            return jsonify({'error': 'No data found for the given ticker and date range.'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    stats = df.describe().round(2).to_dict()

    data_training = pd.DataFrame(df['Close'][0:int(len(df) * 0.70)])
    data_testing = pd.DataFrame(df['Close'][int(len(df) * 0.70):])

    scaler = MinMaxScaler(feature_range=(0, 1))
    data_training_array = scaler.fit_transform(data_training)

    x_train = []
    y_train = []
    for i in range(100, data_training_array.shape[0]): 
        x_train.append(data_training_array[i-100:i])
        y_train.append(data_training_array[i, 0])

    x_train, y_train = np.array(x_train), np.array(y_train)

    past_100_days = data_training.tail(100)
    final_df = pd.concat([past_100_days, data_testing], ignore_index=True)
    input_data = scaler.transform(final_df)

    x_test = []
    y_test = []
    for i in range(100, input_data.shape[0]):
        x_test.append(input_data[i-100:i])
        y_test.append(input_data[i, 0])

    x_test, y_test = np.array(x_test), np.array(y_test)
    
    try:
        model = load_model('/Users/seflame/Desktop/Project/keras_model.h5')
        y_predicted = model.predict(x_test)
    except Exception as e:
        return jsonify({'error': f"Prediction error: {str(e)}"}), 500

    scale_factor = 1 / scaler.scale_[0]
    y_predicted = y_predicted.flatten() * scale_factor
    y_test = y_test * scale_factor

    data_json = df.reset_index().to_dict(orient='records')

    return jsonify({
        'data': data_json,
        'predictions': y_predicted.tolist(),
        'actual': y_test.tolist(),
        'statistics': stats
    })

# Run the app
if __name__ == '__main__':
    app.run(port=5000, debug=True)
