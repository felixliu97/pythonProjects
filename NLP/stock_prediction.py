import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from datetime import datetime, timedelta

def fetch_stock_data(ticker, start_date, end_date):
    """
    Fetch historical stock data for a given ticker
    """
    stock = yf.Ticker(ticker)
    df = stock.history(start=start_date, end=end_date)
    return df

def create_features(df):
    """
    Create technical indicators as features
    """
    # Calculate moving averages
    df['MA5'] = df['Close'].rolling(window=5).mean()
    df['MA20'] = df['Close'].rolling(window=20).mean()
    
    # Calculate price momentum
    df['Momentum'] = df['Close'].pct_change(periods=5)
    
    # Calculate volatility
    df['Volatility'] = df['Close'].rolling(window=20).std()
    
    # Calculate trading volume change
    df['Volume_Change'] = df['Volume'].pct_change()
    
    # Create target variable (next day's closing price)
    df['Target'] = df['Close'].shift(-1)
    
    return df

def prepare_data(df):
    """
    Prepare data for model training
    """
    # Drop rows with NaN values
    df = df.dropna()
    
    # Select features
    features = ['Open', 'High', 'Low', 'Close', 'Volume', 
                'MA5', 'MA20', 'Momentum', 'Volatility', 'Volume_Change']
    
    X = df[features]
    y = df['Target']
    
    # Scale the features
    scaler = MinMaxScaler()
    X_scaled = scaler.fit_transform(X)
    
    return X_scaled, y, scaler

def train_model(X, y):
    """
    Train the prediction model
    """
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    # Calculate model score
    train_score = model.score(X_train, y_train)
    test_score = model.score(X_test, y_test)
    
    print(f"Training R² Score: {train_score:.4f}")
    print(f"Testing R² Score: {test_score:.4f}")
    
    return model, X_test, y_test

def predict_next_day(model, scaler, last_data):
    """
    Predict the next day's stock price
    """
    # Scale the input data
    scaled_data = scaler.transform(last_data)
    
    # Make prediction
    prediction = model.predict(scaled_data)
    
    return prediction[0]

def main():
    # Set parameters
    ticker = "AAPL"  # Example: Apple Inc.
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)  # 1 year of data
    
    # Fetch data
    print(f"Fetching data for {ticker}...")
    df = fetch_stock_data(ticker, start_date, end_date)
    
    # Create features
    print("Creating features...")
    df = create_features(df)
    
    # Prepare data
    print("Preparing data...")
    X, y, scaler = prepare_data(df)
    
    # Train model
    print("Training model...")
    model, X_test, y_test = train_model(X, y)
    
    # Make prediction for next day
    last_data = df[['Open', 'High', 'Low', 'Close', 'Volume', 
                    'MA5', 'MA20', 'Momentum', 'Volatility', 'Volume_Change']].iloc[-1:].values
    
    next_day_prediction = predict_next_day(model, scaler, last_data)
    current_price = df['Close'].iloc[-1]
    
    print("\nPrediction Results:")
    print(f"Current Price: ${current_price:.2f}")
    print(f"Predicted Next Day Price: ${next_day_prediction:.2f}")
    print(f"Predicted Change: ${(next_day_prediction - current_price):.2f} ({(next_day_prediction - current_price)/current_price*100:.2f}%)")

if __name__ == "__main__":
    main()
