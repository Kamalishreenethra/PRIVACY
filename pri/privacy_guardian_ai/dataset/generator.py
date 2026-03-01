import pandas as pd
import numpy as np
import os

def generate_synthetic_data(num_samples=1000, output_path="privacy_guardian_ai/dataset/student_data.csv"):
    np.random.seed(42)
    
    # Features:
    # 1. Study Hours (0-20)
    # 2. Attendance (0-100)
    # 3. Lab Participation (0-10)
    # 4. Previous Grades (0-100)
    # 5. Quiz Scores (0-100)
    
    study_hours = np.random.uniform(0, 20, num_samples)
    attendance = np.random.uniform(0, 100, num_samples)
    lab_participation = np.random.uniform(0, 10, num_samples)
    prev_grades = np.random.uniform(0, 100, num_samples)
    quiz_scores = np.random.uniform(0, 100, num_samples)
    
    # Probabilistic Risk Label Calculation (0 = Low Risk, 1 = High Risk)
    # Risk increases with low attendance, low study hours, and low lab participation
    risk_score = (
        (20 - study_hours) * 0.3 +
        (100 - attendance) * 0.4 +
        (10 - lab_participation) * 0.3
    ) / 10.0
    
    # Add some noise to the risk score
    risk_score += np.random.normal(0, 0.5, num_samples)
    
    # Label is 1 if risk_score > threshold
    risk_label = (risk_score > 4.5).astype(int)
    
    df = pd.DataFrame({
        'study_hours': study_hours,
        'attendance': attendance,
        'lab_participation': lab_participation,
        'prev_grades': prev_grades,
        'quiz_scores': quiz_scores,
        'risk_label': risk_label
    })
    
    df.to_csv(output_path, index=False)
    print(f"Generated {num_samples} samples at {output_path}")
    return df

if __name__ == "__main__":
    generate_synthetic_data()
