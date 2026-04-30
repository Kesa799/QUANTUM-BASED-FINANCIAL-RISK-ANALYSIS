from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
import numpy as np
from scipy.stats import norm

def quantumriskanalysis(mu, sigma, T, investment):
    try:
        # --- Step 1: Probability of Loss ---
        # Use a safe minimum sigma to avoid division by zero
        safe_sigma = max(sigma, 0.01)
        
        # Z-score: probability that the return is < 0
        z = (0 - mu * T) / (safe_sigma * np.sqrt(T))
        p_loss = norm.cdf(z)

        # 🛡️ SAFETY CLAMP: Keeps arcsin math valid (0.01 to 0.99)
        p_loss = max(0.01, min(0.99, p_loss))

        # --- Step 2: Quantum Encoding ---
        qc = QuantumCircuit(1, 1)
        # RY Rotation maps probability to the amplitude of |1>
        qc.ry(2 * np.arcsin(np.sqrt(p_loss)), 0)
        qc.measure(0, 0)

        simulator = AerSimulator()
        job = simulator.run(qc, shots=2000)
        counts = job.result().get_counts()

        # Measured Probability from the Quantum state
        risk_prob = counts.get('1', 0) / 2000

        # --- Step 3: Expected Return (Grounded) ---
        # We display the simple annualized return to avoid scientific notation
        display_return = mu * 100

        # --- Step 4: Value at Risk (VaR) ---
        # Calculates the 95th percentile loss. 
        # Clamped at -100% (total loss) and 0% (no loss) for UI sanity
        raw_var = (np.exp(mu * T - 1.65 * safe_sigma * np.sqrt(T)) - 1) * 100
        VaR_clamped = max(-100.0, min(0.0, raw_var))

        return {
            "risk_probability": round(float(risk_prob * 100), 2),
            "expected_return": round(float(display_return), 2),
            "VaR": round(float(VaR_clamped), 2)
        }

    except Exception as e:
        print(f"Quantum Module Error: {e}")
        return {
            "risk_probability": 50.0,
            "expected_return": 0.0,
            "VaR": -100.0
        }
