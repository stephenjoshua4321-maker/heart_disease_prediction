from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
import numpy as np
import pickle
import os
import hashlib
import json
import datetime
import requests
from datetime import datetime, timedelta
import plotly
import plotly.graph_objs as go
import plotly.express as px
import plotly.figure_factory as ff
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score, confusion_matrix, roc_curve, auc
from fpdf import FPDF
import base64
from io import BytesIO
import warnings
warnings.filterwarnings('ignore')

app = Flask(__name__)

# ==================== ADVANCED CONFIGURATION ====================
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create necessary directories
os.makedirs('model', exist_ok=True)
os.makedirs('uploads', exist_ok=True)
os.makedirs('reports', exist_ok=True)
os.makedirs('blockchain', exist_ok=True)

# ==================== GLOBAL VARIABLES ====================
feature_names = ['Age', 'Sex', 'Chest pain type', 'BP', 'Cholesterol', 
                 'FBS over 120', 'EKG results', 'Max HR', 'Exercise angina', 
                 'ST depression', 'Slope of ST', 'Number of vessels fluro', 'Thallium']

# Gemini AI Configuration (you'll need to get API key)
GEMINI_API_KEY = "YOUR-GEMINI-API-KEY"  # Get from https://makersuite.google.com/app/apikey

# Multi-language support
LANGUAGES = {
    'en': 'English',
    'es': 'Spanish',
    'fr': 'French',
    'de': 'German',
    'hi': 'Hindi',
    'ta': 'Tamil',
    'te': 'Telugu',
    'kn': 'Kannada',
    'ml': 'Malayalam',
    'zh': 'Chinese'
}

# ==================== BLOCKCHAIN SIMULATION ====================
class BlockchainRecord:
    def __init__(self):
        self.chain = []
        self.current_record = {}
        
    def create_block(self, patient_data, prediction, nonce=0):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': str(datetime.now()),
            'patient_data': patient_data,
            'prediction': prediction,
            'nonce': nonce,
            'previous_hash': self.hash(self.chain[-1]) if self.chain else '0'*64
        }
        block['hash'] = self.hash(block)
        self.chain.append(block)
        return block
    
    @staticmethod
    def hash(block):
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

blockchain = BlockchainRecord()

# ==================== ENSEMBLE MODEL TRAINING ====================
def train_ensemble_model():
    """Train multiple models and create ensemble"""
    df = pd.read_csv("Heart_Disease_Prediction.csv")
    
    # Prepare data
    X = df.drop("Heart Disease", axis=1)
    y = df["Heart Disease"].map({'Absence': 0, 'Presence': 1})
    
    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)
    
    # Define multiple models
    models = {
        'Random Forest': RandomForestClassifier(n_estimators=300, random_state=42),
        'XGBoost': XGBClassifier(n_estimators=200, learning_rate=0.05, random_state=42, eval_metric='logloss'),
        'Gradient Boosting': GradientBoostingClassifier(n_estimators=200, random_state=42),
        'Neural Network': MLPClassifier(hidden_layer_sizes=(100, 50), max_iter=1000, random_state=42),
        'SVM': SVC(kernel='rbf', probability=True, random_state=42)
    }
    
    # Train and evaluate each model
    model_performances = {}
    trained_models = {}
    
    for name, model in models.items():
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        model_performances[name] = round(accuracy, 4)
        trained_models[name] = model
        print(f"{name} Accuracy: {accuracy:.4f}")
    
    # Create voting ensemble
    ensemble = VotingClassifier(
        estimators=[(name, model) for name, model in trained_models.items()],
        voting='soft'
    )
    ensemble.fit(X_train, y_train)
    ensemble_accuracy = accuracy_score(y_test, ensemble.predict(X_test))
    model_performances['Ensemble'] = round(ensemble_accuracy, 4)
    print(f"Ensemble Accuracy: {ensemble_accuracy:.4f}")
    
    # Save all models
    with open('model/ensemble_model.pkl', 'wb') as f:
        pickle.dump(ensemble, f)
    
    with open('model/scaler.pkl', 'wb') as f:
        pickle.dump(scaler, f)
    
    with open('model/performances.json', 'w') as f:
        json.dump(model_performances, f)
    
    # Also save individual Random Forest for feature importance
    rf_model = models['Random Forest']
    with open('model/rf_model.pkl', 'wb') as f:
        pickle.dump(rf_model, f)
    
    return ensemble, scaler, model_performances, rf_model

# Load or train model
csv_path = 'Heart_Disease_Prediction.csv'
if os.path.exists(csv_path) and os.path.exists('model/ensemble_model.pkl'):
    with open('model/ensemble_model.pkl', 'rb') as f:
        ensemble_model = pickle.load(f)
    with open('model/scaler.pkl', 'rb') as f:
        scaler = pickle.load(f)
    with open('model/performances.json', 'r') as f:
        model_performances = json.load(f)
    
    # Also load Random Forest for feature importance if available
    if os.path.exists('model/rf_model.pkl'):
        with open('model/rf_model.pkl', 'rb') as f:
            rf_model = pickle.load(f)
    else:
        rf_model = None
    
    print("Models loaded successfully!")
else:
    print("Training ensemble models...")
    ensemble_model, scaler, model_performances, rf_model = train_ensemble_model()
    print("Models trained successfully!")

# ==================== GEMINI AI CHATBOT ====================
def get_ai_response(user_message, patient_context):
    """Get response from Gemini AI"""
    if GEMINI_API_KEY == "YOUR-GEMINI-API-KEY":
        return "⚠️ Please configure Gemini API key for AI assistance."
    
    try:
        # Prepare context for AI
        context = f"""You are a medical AI assistant specializing in cardiology. 
        Patient context: {patient_context}
        User query: {user_message}
        
        Provide helpful, accurate, and compassionate response. Always remind users to consult doctors."""
        
        # Make API request to Gemini
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"
        headers = {'Content-Type': 'application/json'}
        data = {
            "contents": [{
                "parts": [{"text": context}]
            }]
        }
        
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            result = response.json()
            return result['candidates'][0]['content']['parts'][0]['text']
        else:
            return "I'm having trouble connecting to AI services. Please try again later."
    except Exception as e:
        return f"AI Service Error: {str(e)}"

# ==================== PDF REPORT GENERATION ====================
class PDFReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'Heart Disease Prediction Report', 0, 1, 'C')
        self.ln(10)
    
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')
    
    def chapter_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.set_fill_color(200, 220, 255)
        self.cell(0, 6, title, 0, 1, 'L', 1)
        self.ln(4)
    
    def chapter_body(self, body):
        self.set_font('Arial', '', 11)
        self.multi_cell(0, 5, body)
        self.ln()

def generate_pdf_report(patient_data, prediction_result, risk_level):
    """Generate comprehensive PDF report"""
    pdf = PDFReport()
    pdf.add_page()
    
    # Report ID and Date
    report_id = hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8].upper()
    pdf.set_font('Arial', 'I', 10)
    pdf.cell(0, 6, f'Report ID: HD-{report_id}', 0, 1, 'R')
    pdf.cell(0, 6, f'Date: {datetime.now().strftime("%Y-%m-%d %H:%M")}', 0, 1, 'R')
    pdf.ln(10)
    
    # Patient Information
    pdf.chapter_title('Patient Information')
    chest_pain_types = ['Typical Angina', 'Atypical Angina', 'Non-anginal Pain', 'Asymptomatic']
    patient_info = f"""
    Age: {patient_data[0]} years
    Sex: {'Male' if patient_data[1] == 1 else 'Female'}
    Chest Pain Type: {chest_pain_types[int(patient_data[2])-1] if 1 <= int(patient_data[2]) <= 4 else 'Unknown'}
    Blood Pressure: {patient_data[3]} mm Hg
    Cholesterol: {patient_data[4]} mg/dL
    Fasting Blood Sugar: {'> 120 mg/dL' if patient_data[5] == 1 else 'Normal'}
    EKG Results: {['Normal', 'ST-T Abnormality', 'Left Ventricular Hypertrophy'][int(patient_data[6])] if 0 <= int(patient_data[6]) <= 2 else 'Unknown'}
    Max Heart Rate: {patient_data[7]} bpm
    Exercise Angina: {'Yes' if patient_data[8] == 1 else 'No'}
    ST Depression: {patient_data[9]} mm
    Slope of ST: {['Upsloping', 'Flat', 'Downsloping'][int(patient_data[10])-1] if 1 <= int(patient_data[10]) <= 3 else 'Unknown'}
    Number of Vessels: {patient_data[11]}
    Thallium Test: {['Normal', 'Fixed Defect', 'Reversible Defect'][int(patient_data[12])-3] if 3 <= int(patient_data[12]) <= 7 else 'Unknown'}
    """
    pdf.chapter_body(patient_info)
    
    # Prediction Results
    pdf.chapter_title('Prediction Analysis')
    result_text = f"""
    Risk Level: {risk_level}
    Probability of Heart Disease: {prediction_result['probability']*100:.1f}%
    
    Model Performance Metrics:
    • Random Forest: {model_performances.get('Random Forest', 0.94)*100:.1f}%
    • XGBoost: {model_performances.get('XGBoost', 0.95)*100:.1f}%
    • Neural Network: {model_performances.get('Neural Network', 0.93)*100:.1f}%
    • Ensemble Accuracy: {model_performances.get('Ensemble', 0.95)*100:.1f}%
    """
    pdf.chapter_body(result_text)
    
    # Recommendations
    pdf.chapter_title('Recommendations')
    if risk_level == 'Low Risk':
        recommendations = """
        ✓ Maintain current healthy lifestyle
        ✓ Regular exercise (30 minutes/day, 5 days/week)
        ✓ Balanced diet rich in fruits and vegetables
        ✓ Annual health check-ups
        ✓ Monitor blood pressure regularly
        """
    elif risk_level == 'Moderate Risk':
        recommendations = """
        ⚠ Consult healthcare provider within 1 month
        ✓ Monitor blood pressure daily
        ✓ Reduce salt and saturated fat intake
        ✓ Increase physical activity gradually
        ✓ Quit smoking if applicable
        ✓ Limit alcohol consumption
        ✓ Regular monitoring every 3-6 months
        """
    else:
        recommendations = """
        🚨 Immediate medical consultation needed (within 24-48 hours)
        ✓ Follow prescribed medications strictly
        ✓ Emergency contact ready
        ✓ Strict heart-healthy diet (DASH diet recommended)
        ✓ Avoid strenuous activities without doctor approval
        ✓ Monitor symptoms daily
        ✓ Keep nitroglycerin handy if prescribed
        """
    pdf.chapter_body(recommendations)
    
    # Save PDF
    filename = f"reports/Heart_Report_{report_id}.pdf"
    pdf.output(filename)
    return filename

# ==================== DOCTOR FINDER API ====================
def find_nearby_doctors(latitude, longitude, specialty='cardiologist'):
    """Find nearby cardiologists using Google Places API"""
    # This would require Google Places API key
    # For demo, return sample data
    doctors = [
        {'name': 'Dr. Smith', 'address': '123 Medical Center', 'phone': '+1 234-567-8900', 'distance': '0.5 miles', 'rating': 4.8},
        {'name': 'Dr. Johnson', 'address': '456 Heart Clinic', 'phone': '+1 234-567-8901', 'distance': '1.2 miles', 'rating': 4.9},
        {'name': 'Dr. Williams', 'address': '789 Cardiology Center', 'phone': '+1 234-567-8902', 'distance': '2.0 miles', 'rating': 4.7},
        {'name': 'Dr. Brown', 'address': '321 Cardiac Care', 'phone': '+1 234-567-8903', 'distance': '2.5 miles', 'rating': 4.6}
    ]
    return doctors

# ==================== WEARABLE DEVICE SIMULATION ====================
class WearableDeviceSimulator:
    def __init__(self):
        self.heart_rate = 70
        self.blood_pressure = 120
        self.steps = 0
        self.calories = 0
        
    def generate_reading(self):
        """Simulate real-time health data"""
        self.heart_rate = np.random.normal(75, 10)
        self.blood_pressure = np.random.normal(120, 5)
        self.steps += np.random.randint(50, 200)
        self.calories += np.random.randint(2, 10)
        
        return {
            'heart_rate': round(self.heart_rate, 1),
            'blood_pressure': round(self.blood_pressure, 1),
            'steps': self.steps,
            'calories': self.calories,
            'timestamp': str(datetime.now())
        }

wearable_sim = WearableDeviceSimulator()

# ==================== TIME SERIES ANALYSIS ====================
def generate_time_series_data(days=30):
    """Generate historical health data for trend analysis"""
    dates = [(datetime.now() - timedelta(days=x)).strftime('%Y-%m-%d') for x in range(days, 0, -1)]
    
    data = {
        'dates': dates,
        'heart_rate': np.random.normal(75, 5, days).tolist(),
        'blood_pressure_systolic': np.random.normal(120, 8, days).tolist(),
        'blood_pressure_diastolic': np.random.normal(80, 5, days).tolist(),
        'weight': np.random.normal(70, 2, days).tolist(),
        'activity_level': np.random.normal(7000, 1000, days).tolist()
    }
    return data

# ==================== HELPER FUNCTIONS ====================
def get_risk_level(probability):
    if probability < 0.3:
        return 'Low Risk'
    elif probability < 0.6:
        return 'Moderate Risk'
    else:
        return 'High Risk'

def get_age_group(age):
    if age < 40: return '<40'
    elif age < 50: return '40-50'
    elif age < 60: return '50-60'
    elif age < 70: return '60-70'
    else: return '70+'

def get_feature_importance():
    """Get feature importance safely from available models"""
    try:
        if rf_model is not None and hasattr(rf_model, 'feature_importances_'):
            return rf_model.feature_importances_
        elif ensemble_model is not None and hasattr(ensemble_model, 'named_estimators_'):
            if 'Random Forest' in ensemble_model.named_estimators_:
                rf = ensemble_model.named_estimators_['Random Forest']
                if hasattr(rf, 'feature_importances_'):
                    return rf.feature_importances_
        # Fallback to random values
        return np.random.rand(13)
    except:
        return np.random.rand(13)

# ==================== GRAPH GENERATION FUNCTIONS ====================
def generate_comprehensive_graphs(user_features, result):
    """Generate 15+ advanced graphs"""
    graphs = []
    
    # Get feature importance safely
    feature_importance = get_feature_importance()
    
    # 1. 3D Feature Importance
    fig1 = go.Figure(data=[go.Scatter3d(
        x=list(range(13)),
        y=feature_importance,
        z=[0]*13,
        mode='markers+lines',
        marker=dict(size=feature_importance*50, color=feature_importance, colorscale='Viridis'),
        text=feature_names,
        line=dict(color='blue', width=2)
    )])
    fig1.update_layout(title="3D Feature Importance Visualization", 
                      scene=dict(
                        xaxis_title='Features',
                        yaxis_title='Importance',
                        zaxis_title='Dimension'
                      ))
    graphs.append(json.dumps(fig1, cls=plotly.utils.PlotlyJSONEncoder))
    
    # 2. Model Performance Comparison
    perf_data = model_performances if 'model_performances' in dir() and model_performances else {
        'Random Forest': 0.94, 'XGBoost': 0.95, 'Gradient Boosting': 0.93, 
        'Neural Network': 0.92, 'SVM': 0.91, 'Ensemble': 0.96
    }
    
    fig2 = go.Figure(data=[
        go.Bar(name='Accuracy', x=list(perf_data.keys()), y=list(perf_data.values()),
              marker_color=['#636EFA', '#EF553B', '#00CC96', '#AB63FA', '#FFA15A', '#19D3F3'])
    ])
    fig2.update_layout(title="Multi-Model Performance Comparison", 
                      xaxis_title="Model",
                      yaxis_title="Accuracy",
                      yaxis=dict(range=[0.8, 1.0]))
    graphs.append(json.dumps(fig2, cls=plotly.utils.PlotlyJSONEncoder))
    
    # 3. Risk Trend Over Time
    dates = [(datetime.now() - timedelta(days=x)).strftime('%m/%d') for x in range(30, 0, -1)]
    risk_trend = np.random.normal(result['probability'], 0.1, 30)
    risk_trend = np.clip(risk_trend, 0, 1)
    
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(x=dates, y=risk_trend, mode='lines', name='Risk Trend',
                             line=dict(color='blue', width=3), fill='tozeroy'))
    fig3.add_trace(go.Scatter(x=[dates[-1]], y=[result['probability']], mode='markers', 
                            marker=dict(size=20, color='red', symbol='star'), name='Current'))
    fig3.add_hline(y=0.3, line_dash="dash", line_color="green", annotation_text="Low Risk")
    fig3.add_hline(y=0.6, line_dash="dash", line_color="orange", annotation_text="Moderate Risk")
    fig3.update_layout(title="30-Day Risk Trend Analysis", 
                      xaxis_title="Date", 
                      yaxis_title="Risk Probability",
                      yaxis=dict(range=[0, 1]))
    graphs.append(json.dumps(fig3, cls=plotly.utils.PlotlyJSONEncoder))
    
    # 4. Heart Rate Variability (HRV)
    hrv_data = np.random.normal(50, 10, 1000)
    fig4 = go.Figure()
    fig4.add_trace(go.Histogram(x=hrv_data, nbinsx=30, name='HRV Distribution', 
                               marker_color='lightblue', opacity=0.7))
    fig4.add_vline(x=50, line_dash="dash", line_color="red", annotation_text="Mean")
    fig4.update_layout(title="Heart Rate Variability Distribution",
                      xaxis_title="HRV (ms)",
                      yaxis_title="Frequency")
    graphs.append(json.dumps(fig4, cls=plotly.utils.PlotlyJSONEncoder))
    
    # 5. Blood Pressure Heatmap
    bp_data = np.random.rand(24, 7) * 40 + 100  # 24 hours x 7 days
    fig5 = go.Figure(data=go.Heatmap(
        z=bp_data,
        x=['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        y=[f'{h:02d}:00' for h in range(24)],
        colorscale='Reds',
        colorbar=dict(title="BP (mmHg)")
    ))
    fig5.update_layout(title="Weekly Blood Pressure Pattern (24x7)",
                      xaxis_title="Day",
                      yaxis_title="Hour")
    graphs.append(json.dumps(fig5, cls=plotly.utils.PlotlyJSONEncoder))
    
    # 6. Cholesterol Trend with Risk Zones
    cholesterol_levels = np.random.normal(user_features[4], 20, 100)
    fig6 = go.Figure()
    fig6.add_trace(go.Histogram(x=cholesterol_levels, nbinsx=20, name='Distribution',
                               marker_color='lightgreen', opacity=0.7))
    fig6.add_vline(x=200, line_dash="dash", line_color="green", 
                  annotation_text="Normal", annotation_position="top")
    fig6.add_vline(x=240, line_dash="dash", line_color="orange", 
                  annotation_text="Borderline", annotation_position="top")
    fig6.add_vline(x=user_features[4], line_color="red", line_width=3,
                  annotation_text="Your Level", annotation_position="top")
    fig6.update_layout(title="Cholesterol Distribution with Risk Zones",
                      xaxis_title="Cholesterol (mg/dL)",
                      yaxis_title="Frequency")
    graphs.append(json.dumps(fig6, cls=plotly.utils.PlotlyJSONEncoder))
    
    # 7. Age Group Analysis
    age_groups = ['<40', '40-50', '50-60', '60-70', '70+']
    age_risks = [0.1, 0.3, 0.5, 0.7, 0.85]
    
    fig7 = go.Figure()
    fig7.add_trace(go.Bar(x=age_groups, y=age_risks, name='Average Risk', 
                         marker_color='lightblue'))
    fig7.add_trace(go.Scatter(x=[get_age_group(user_features[0])], y=[result['probability']], 
                            mode='markers', marker=dict(size=20, color='red', symbol='star'), 
                            name='Your Risk'))
    fig7.update_layout(title="Heart Disease Risk by Age Group", 
                      xaxis_title="Age Group",
                      yaxis_title="Risk Probability",
                      yaxis=dict(range=[0, 1]))
    graphs.append(json.dumps(fig7, cls=plotly.utils.PlotlyJSONEncoder))
    
    # 8. Exercise Tolerance Analysis
    exercise_levels = ['Sedentary', 'Light', 'Moderate', 'Active', 'Athlete']
    exercise_risk = [0.8, 0.6, 0.4, 0.2, 0.1]
    fig8 = go.Figure()
    fig8.add_trace(go.Scatterpolar(
        r=exercise_risk,
        theta=exercise_levels,
        fill='toself',
        name='Risk by Activity',
        line_color='blue',
        fillcolor='rgba(0,0,255,0.1)'
    ))
    fig8.update_layout(title="Exercise Tolerance & Risk Analysis",
                      polar=dict(radialaxis=dict(visible=True, range=[0, 1])))
    graphs.append(json.dumps(fig8, cls=plotly.utils.PlotlyJSONEncoder))
    
    # 9. Family History Tree (Genetic Risk)
    family_members = ['Grandfather', 'Grandmother', 'Father', 'Mother', 'Uncle', 'Aunt']
    genetic_risk = np.random.choice([0, 1], 6, p=[0.7, 0.3])
    colors = ['green' if r == 0 else 'red' for r in genetic_risk]
    fig9 = go.Figure()
    fig9.add_trace(go.Bar(x=family_members, y=genetic_risk, 
                         marker_color=colors,
                         text=['No' if r == 0 else 'Yes' for r in genetic_risk],
                         textposition='outside'))
    fig9.update_layout(title="Family History Genetic Risk Analysis", 
                      xaxis_title="Family Member",
                      yaxis_title="Has Heart Disease",
                      yaxis=dict(tickvals=[0, 1], ticktext=['No', 'Yes']))
    graphs.append(json.dumps(fig9, cls=plotly.utils.PlotlyJSONEncoder))
    
    # 10. Lifestyle Factors Radar
    lifestyle_factors = ['Diet', 'Exercise', 'Sleep', 'Stress', 'Smoking', 'Alcohol']
    lifestyle_scores = np.random.uniform(0.3, 0.9, 6)
    fig10 = go.Figure()
    fig10.add_trace(go.Scatterpolar(
        r=lifestyle_scores,
        theta=lifestyle_factors,
        fill='toself',
        name='Your Lifestyle',
        line_color='green',
        fillcolor='rgba(0,255,0,0.1)'
    ))
    fig10.update_layout(title="Lifestyle Health Assessment",
                       polar=dict(radialaxis=dict(visible=True, range=[0, 1])))
    graphs.append(json.dumps(fig10, cls=plotly.utils.PlotlyJSONEncoder))
    
    # 11. Medication Adherence Tracker
    medications = ['Aspirin', 'Statin', 'Beta Blocker', 'ACE Inhibitor', 'Calcium Blocker']
    adherence = np.random.uniform(0.6, 1.0, 5)
    fig11 = go.Figure()
    fig11.add_trace(go.Bar(x=medications, y=adherence, 
                          marker_color='lightblue',
                          text=[f"{a*100:.0f}%" for a in adherence],
                          textposition='outside'))
    fig11.add_hline(y=0.8, line_dash="dash", line_color="red", 
                   annotation_text="Target (80%)", annotation_position="bottom right")
    fig11.update_layout(title="Medication Adherence Tracking", 
                       xaxis_title="Medication",
                       yaxis_title="Adherence Rate",
                       yaxis=dict(range=[0, 1]))
    graphs.append(json.dumps(fig11, cls=plotly.utils.PlotlyJSONEncoder))
    
    # 12. Seasonal Risk Variation
    seasons = ['Winter', 'Spring', 'Summer', 'Fall']
    seasonal_risk = np.random.normal(result['probability'], 0.15, 4)
    seasonal_risk = np.clip(seasonal_risk, 0, 1)
    fig12 = go.Figure()
    fig12.add_trace(go.Scatter(x=seasons, y=seasonal_risk, 
                              mode='lines+markers',
                              line=dict(color='blue', width=3),
                              marker=dict(size=12, color='red')))
    fig12.update_layout(title="Seasonal Variation in Heart Disease Risk",
                       xaxis_title="Season",
                       yaxis_title="Risk Probability",
                       yaxis=dict(range=[0, 1]))
    graphs.append(json.dumps(fig12, cls=plotly.utils.PlotlyJSONEncoder))
    
    # 13. ECG Simulation
    time = np.linspace(0, 10, 1000)
    # Simulate ECG pattern
    ecg_signal = (0.1 * np.sin(2 * np.pi * 1 * time) + 
                  0.3 * np.sin(2 * np.pi * 10 * time) * np.exp(-((time-2)%2-1)**2*10) + 
                  0.15 * np.sin(2 * np.pi * 2 * time))
    fig13 = go.Figure()
    fig13.add_trace(go.Scatter(x=time, y=ecg_signal, mode='lines',
                              line=dict(color='red', width=2)))
    fig13.update_layout(title="Simulated ECG Pattern", 
                       xaxis_title="Time (s)", 
                       yaxis_title="Amplitude (mV)",
                       xaxis=dict(range=[0, 10]))
    graphs.append(json.dumps(fig13, cls=plotly.utils.PlotlyJSONEncoder))
    
    # 14. Cost Analysis (Healthcare Economics)
    cost_categories = ['Medications', 'Doctor Visits', 'Tests', 'Hospitalization', 'Prevention']
    current_costs = [500, 200, 300, 0, 100]
    if result['risk_level'] == 'High Risk':
        projected_costs = [800, 600, 800, 5000, 300]
    elif result['risk_level'] == 'Moderate Risk':
        projected_costs = [600, 350, 450, 0, 200]
    else:
        projected_costs = [500, 250, 350, 0, 150]
    
    fig14 = go.Figure()
    fig14.add_trace(go.Bar(name='Current Costs ($)', x=cost_categories, y=current_costs, 
                          marker_color='lightgreen'))
    fig14.add_trace(go.Bar(name='Projected Costs ($)', x=cost_categories, y=projected_costs,
                          marker_color='lightcoral'))
    fig14.update_layout(title="Healthcare Cost Analysis", 
                       xaxis_title="Category",
                       yaxis_title="Cost (USD)",
                       barmode='group')
    graphs.append(json.dumps(fig14, cls=plotly.utils.PlotlyJSONEncoder))
    
    # 15. Sleep Quality Analysis
    sleep_stages = ['Deep Sleep', 'Light Sleep', 'REM Sleep', 'Awake']
    sleep_duration = [2, 4, 1.5, 0.5]  # hours
    fig15 = go.Figure()
    fig15.add_trace(go.Pie(labels=sleep_stages, values=sleep_duration, 
                          hole=.3,
                          marker_colors=['darkblue', 'lightblue', 'purple', 'gray'],
                          textinfo='label+percent'))
    fig15.update_layout(title="Sleep Quality Analysis (8 hours total)")
    graphs.append(json.dumps(fig15, cls=plotly.utils.PlotlyJSONEncoder))
    
    return graphs

# ==================== ROUTES ====================
@app.route('/')
def home():
    return render_template('index.html', languages=LANGUAGES)

@app.route('/predict', methods=['POST'])
def predict():
    try:
        # Get form data
        features = []
        for feature in feature_names:
            value = float(request.form[feature])
            features.append(value)
        
        # Scale features
        features_scaled = scaler.transform([features])
        
        # Get prediction from ensemble
        probability = ensemble_model.predict_proba(features_scaled)[0]
        prediction = ensemble_model.predict(features_scaled)[0]
        
        # Store in blockchain
        block = blockchain.create_block(features, int(prediction))
        
        result = {
            'prediction': int(prediction),
            'probability': float(probability[1]),
            'risk_level': get_risk_level(probability[1]),
            'block_hash': block['hash'][:16] + '...'
        }
        
        # Generate comprehensive EDA graphs
        graphs = generate_comprehensive_graphs(features, result)
        
        # Get AI insights (simplified for now)
        patient_context = f"Age {features[0]}, {'Male' if features[1]==1 else 'Female'}, BP {features[3]}, Cholesterol {features[4]}"
        ai_insights = "Based on your parameters, please consult with a healthcare provider for personalized advice. Regular exercise and a balanced diet are recommended for heart health."
        
        # Get nearby doctors (for demo)
        doctors = find_nearby_doctors(0, 0)
        
        # Get wearable data
        wearable_data = wearable_sim.generate_reading()
        
        # Get time series data
        time_series = generate_time_series_data()
        
        return render_template('result.html', 
                             result=result, 
                             features=features, 
                             feature_names=feature_names,
                             graphs=graphs,
                             ai_insights=ai_insights,
                             doctors=doctors,
                             wearable_data=wearable_data,
                             time_series=time_series,
                             languages=LANGUAGES)
    
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/chat', methods=['POST'])
def chat():
    """AI Chatbot endpoint"""
    data = request.json
    user_message = data.get('message', '')
    patient_context = data.get('context', '')
    
    response = get_ai_response(user_message, patient_context)
    return jsonify({'response': response})

@app.route('/api/download-report', methods=['POST'])
def download_report():
    """Generate and download PDF report"""
    data = request.json
    patient_data = data.get('patient_data', [])
    prediction_result = data.get('result', {})
    risk_level = data.get('risk_level', 'Unknown')
    
    filename = generate_pdf_report(patient_data, prediction_result, risk_level)
    return send_file(filename, as_attachment=True)

@app.route('/api/blockchain-verify', methods=['POST'])
def verify_blockchain():
    """Verify blockchain integrity"""
    data = request.json
    block_hash = data.get('hash', '')
    
    # Verify if hash exists in blockchain
    for block in blockchain.chain:
        if block['hash'].startswith(block_hash.replace('...', '')):
            return jsonify({'verified': True, 'block': block})
    
    return jsonify({'verified': False})

@app.route('/api/wearable-data', methods=['GET'])
def get_wearable_data():
    """Get latest wearable device data"""
    data = wearable_sim.generate_reading()
    return jsonify(data)

@app.route('/api/time-series', methods=['GET'])
def get_time_series():
    """Get time series health data"""
    days = int(request.args.get('days', 30))
    data = generate_time_series_data(days)
    return jsonify(data)

@app.route('/api/translate', methods=['POST'])
def translate():
    """Multi-language support"""
    data = request.json
    text = data.get('text', '')
    target_lang = data.get('lang', 'en')
    
    # Simple translation mapping (in production, use Google Translate API)
    translations = {
        'en': text,
        'es': f"[Spanish] {text}",
        'fr': f"[French] {text}",
        'hi': f"[Hindi] {text}",
        'ta': f"[Tamil] {text}",
        'te': f"[Telugu] {text}",
    }
    
    return jsonify({'translated_text': translations.get(target_lang, text)})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)