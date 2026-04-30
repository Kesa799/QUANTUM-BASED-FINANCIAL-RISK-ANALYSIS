import yfinance as yf
import pandas as pd
import numpy as np
from quantum_risk import quantumriskanalysis
from flask import Flask, render_template, request

app = Flask(__name__)
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        raw_symbol = request.form.get('stock').upper()
        
        # --- FIX: Support Indian Stocks Automatically ---
        # Checks if it's a 3-5 letter symbol without a suffix (like TCS)
        # and tries adding .NS for National Stock Exchange.
        ticker_options = [raw_symbol]
        if not ("." in raw_symbol):
            ticker_options.append(f"{raw_symbol}.NS")

        data = pd.DataFrame()
        final_symbol = raw_symbol
        
        for t in ticker_options:
            ticker = yf.Ticker(t)
            data = ticker.history(period="1y")
            if not data.empty:
                final_symbol = t
                break

        if data.empty:
            return f"Error: No data found for {raw_symbol}. Try adding .NS for Indian stocks.", 400

        # --- FIX: Log Returns for Stability ---
        # log(P_today / P_yesterday) prevents exponential explosion
        log_returns = np.log(data['Close'] / data['Close'].shift(1)).dropna()
        
        # Annualized Mean and Volatility
        mu = log_returns.mean() * 252
        sigma = log_returns.std() * np.sqrt(252)

        # --- FIX: The "Reality Check" Cap ---
        # Caps the expected growth at 200% to ensure the Quantum model 
        # still sees risk even for high-flyers like NVDA
        mu_capped = max(-2.0, min(2.0, mu))

        investment = float(request.form.get('amount'))
        T = float(request.form.get('years', 1))

        # Perform Quantum Analysis
        result = quantumriskanalysis(mu_capped, sigma, T, investment)

        # Determine Status
        risk_val = result['risk_probability']
        if risk_val < 30:
            status = "Low Risk"
        elif risk_val < 60:
            status = "Moderate Risk"
        elif risk_val < 80:
            status = "High Risk"
        else:
            status = "Extremely high risk"

        return render_template(
            'result.html',
            stock=final_symbol,
            risk=result['risk_probability'],
            expected_return=result['expected_return'],
            volatility=round(sigma * 100, 2),
            VaR=result['VaR'],
            status=status,
            dates=data.index.strftime('%Y-%m-%d').tolist(),
            prices=data['Close'].tolist()
        )

    except Exception as e:
        return f"An unexpected error occurred: {e}", 500


if __name__ == '__main__':
    app.run(debug=True)
