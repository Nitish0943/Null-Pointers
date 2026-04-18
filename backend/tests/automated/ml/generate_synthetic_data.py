import numpy as np
import pandas as pd

def generate_test_batch(scenario="normal", n_samples=50):
    """
    Scenarios: normal, overheating, overcurrent, friction
    """
    # Base: Position around 50, Temp around 40
    data = {
        "actual_position": np.random.normal(50, 0.5, n_samples),
        "actual_temperature": np.random.normal(40, 1.0, n_samples),
        "position_error": np.random.normal(0, 0.1, n_samples),
        "temperature_error": np.random.normal(0, 0.5, n_samples),
        "risk_score": np.zeros(n_samples)
    }

    if scenario == "overheating":
        data["actual_temperature"] += np.linspace(0, 30, n_samples)
        data["temperature_error"] += np.linspace(0, 15, n_samples)
    
    if scenario == "friction":
        data["position_error"] += np.linspace(0, 5, n_samples)
        data["actual_position"] -= np.linspace(0, 2, n_samples)

    df = pd.DataFrame(data)
    return df

if __name__ == "__main__":
    df = generate_test_batch("overheating")
    print(df.head())
    df.to_csv("tests/ml/synthetic_overheat.csv", index=False)
