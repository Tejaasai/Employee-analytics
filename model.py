import streamlit as st
import pandas as pd
import numpy as np
import joblib
import pickle
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt

# ----------------- Authentication System -----------------
def check_login():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        with st.form("Login"):
            st.header("Login")
            username = st.text_input("Username")
            password = st.text_input("Password", type='password')
            submit = st.form_submit_button("Login")
            
            if submit:
                if username == "admin" and password == "admin@123":
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("Invalid credentials")
        return False
    return True

def logout():
    st.session_state.logged_in = False
    # st.rerun()

# ----------------- Resource Loading -----------------
@st.cache_resource
def load_resources():
    model = joblib.load("logistic_regression_model.pkl")
    scaler = joblib.load("scaler.pkl")
    model_columns = joblib.load("model_columns.pkl")
    
    with open("category_mapping.pkl", 'rb') as f:
        category_mapping = pickle.load(f)
    
    return model, scaler, model_columns, category_mapping

# ----------------- Preprocessing Function -----------------
def preprocess_input(input_df, model_columns, scaler):
    """Preprocess input data to match training data format"""
    # Bin numerical features
    age_bins = [21, 29, 37, 46, 54, 62]
    age_labels = ['21-28', '29-36', '37-45', '46-53', '54-61']
    input_df['age_group'] = pd.cut(input_df['age'], bins=age_bins, labels=age_labels, right=False)
    
    tenure_bins = [0, 6, 12, 18, 24, 30]
    tenure_labels = ['0-5', '6-11', '12-17', '18-23', '24-29']
    input_df['tenure_group'] = pd.cut(input_df['tenure'], bins=tenure_bins, labels=tenure_labels, right=False)
    
    salary_bins = [40000, 60000, 80000, 100000, 130000]
    salary_labels = ['low', 'medium', 'high', 'very_high']
    input_df['salary_bin'] = pd.cut(input_df['salary'], bins=salary_bins, labels=salary_labels, right=False)
    
    # Select and encode features
    features = ['no_of_projects', 'salary_bin', 'age_group', 'tenure_group', 
                'dept_name', 'title', 'sex', 'Last_performance_rating']
    processed_df = input_df[features]
    
    # One-hot encode with drop_first=True
    encoded_df = pd.get_dummies(processed_df, drop_first=True)
    
    # Align with model columns
    missing_cols = set(model_columns) - set(encoded_df.columns)
    for col in missing_cols:
        encoded_df[col] = 0
    encoded_df = encoded_df[model_columns]
    
    # Scale features
    scaled_data = scaler.transform(encoded_df)
    return scaled_data

# ----------------- Main Application -----------------
def main_app():
    model, scaler, model_columns, category_mapping = load_resources()
    
    # Add logout button
    st.sidebar.button("Logout", on_click=logout)
    
    st.title('Employee Attrition Prediction')
    
    input_method = st.radio("Choose input method:", ('Upload CSV', 'Manual Input'))

    if input_method == 'Upload CSV':
        uploaded_file = st.file_uploader("Upload CSV file", type=['csv'])
        if uploaded_file:
            df = pd.read_csv(uploaded_file)
            required_cols = ['age', 'tenure', 'salary', 'dept_name', 'title', 
                            'sex', 'Last_performance_rating', 'no_of_projects']
            if all(col in df.columns for col in required_cols):
                # Pass model_columns and scaler to preprocess_input
                processed_data = preprocess_input(df, model_columns, scaler)
                predictions = model.predict(processed_data)
                probabilities = model.predict_proba(processed_data)[:, 1]
                df['Prediction'] = ['Leave' if p == 1 else 'Stay' for p in predictions]
                df['Probability'] = probabilities
                
                # Visualization
                st.subheader("Analysis Results")
                
                # Metrics
                col1, col2, col3 = st.columns(3)
                total = len(df)
                stay = len(df[df['Prediction'] == 'Stay'])
                leave = len(df[df['Prediction'] == 'Leave'])
                
                col1.metric("Total Employees", total)
                col2.metric("Employees Staying", stay, f"{stay/total:.1%}")
                col3.metric("Employees Leaving", leave, f"{leave/total:.1%}")
                
                # Pie chart
                fig, ax = plt.subplots()
                ax.pie([stay, leave], 
                       labels=['Stay', 'Leave'], 
                       colors=['#4CAF50', '#F44336'],
                       autopct='%1.1f%%')
                ax.set_title("Attrition Distribution")
                st.pyplot(fig)
                
                # Show data
                st.subheader("Detailed Predictions")
                st.write(df)
            else:
                st.error(f"Missing required columns: {required_cols}")

    else:
        st.subheader("Employee Details")
        no_of_projects = st.number_input('Number of Projects', min_value=0, max_value=20, value=2)
        salary = st.number_input('Annual Salary ($)', min_value=40000, max_value=130000, value=50000)
        age = st.slider('Age', 21, 61, 30)
        tenure = st.slider('Tenure (Years)', 0, 29, 2)
        
        # Get full category lists from mapping
        dept_name = st.selectbox('Department', category_mapping['dept_name'])
        title = st.selectbox('Job Title', category_mapping['title'])
        sex = st.selectbox('Gender', category_mapping['sex'])
        rating = st.selectbox('Performance Rating', category_mapping['Last_performance_rating'])
        
        if st.button('Predict'):
            input_data = {
                'age': [age],
                'tenure': [tenure],
                'salary': [salary],
                'no_of_projects': [no_of_projects],
                'dept_name': [dept_name],
                'title': [title],
                'sex': [sex],
                'Last_performance_rating': [rating]
            }
            input_df = pd.DataFrame(input_data)
            # Pass model_columns and scaler to preprocess_input
            processed_data = preprocess_input(input_df, model_columns, scaler)
            prediction = model.predict(processed_data)[0]
            probability = model.predict_proba(processed_data)[0][1]
            
            st.subheader('Result')
            if prediction == 1:
                st.error(f'Prediction: Employee will leave (Probability: {probability:.2f})')
            else:
                st.success(f'Prediction: Employee will stay (Probability: {1 - probability:.2f})')

# ----------------- Run Application -----------------
if __name__ == "__main__":
    if check_login():
        main_app()
