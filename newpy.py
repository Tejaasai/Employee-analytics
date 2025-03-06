import streamlit as st
import hashlib
import os
import pandas as pd
import numpy as np
import plotly.express as px

# ---------------------- Authentication System ----------------------
def authenticate_user(username, password):
    """Secure authentication system with hashed passwords"""
    authorized_users = {
        "admin": hashlib.sha256(os.getenv("ADMIN_PW", "admin@123").encode()).hexdigest(),
        "user": hashlib.sha256(os.getenv("USER_PW", "user@123").encode()).hexdigest()
    }
    return authorized_users.get(username) == hashlib.sha256(password.encode()).hexdigest()

def login_form():
    """Display login form and handle authentication"""
    with st.form("Login"):
        st.subheader("🔒 Administrator Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            if authenticate_user(username, password):
                st.session_state.authenticated = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("Invalid credentials")

def logout():
    """Clear session state for logout"""
    st.session_state.clear()

# Check authentication state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    login_form()
    st.stop()

# Logout button in sidebar
st.sidebar.button("Logout", on_click=logout)

# Load environment variable
DRIVE_CSV_URL = st.secrets["DRIVE_CSV_URL"] #for streamlit to collect drivelink from secrets to load data

# Read CSV from Google Drive
df = pd.read_csv(DRIVE_CSV_URL,encoding='utf-8')

# Ensure date columns are in datetime format
df['hire_date'] = pd.to_datetime(df['hire_date'], dayfirst=True)
df['last_date'] = pd.to_datetime(df['last_date'], dayfirst=True)

# Create unique employees dataset for analysis
unique_employees = df.drop_duplicates(subset=['emp_no']).copy()
unique_employees.loc[:, 'tenure'] = np.where(
    unique_employees['last_date'].notna(),
    (unique_employees['last_date'] - unique_employees['hire_date']).dt.days // 365,
    (unique_employees['last_date'].max() - unique_employees['hire_date']).dt.days // 365
)

# ======================
# Key Metrics Section
# ======================
st.title("📈 Employee Analytics Dashboard")
st.header("📊 Key Metrics")
col1, col2, col3, col4 = st.columns(4)
with col1:
    # Total Employees
    total_employees = df['emp_no'].nunique()
    st.metric("Total Employees", f"{total_employees:,}")
    
with col2:
    # Total Departments
    total_depts = df['dept_name'].nunique()
    st.metric("Total Departments", f"{total_depts:,}")

with col3:
    # Average Salary
    avg_salary = unique_employees['salary'].mean()
    st.metric("Average Salary", f"₹{avg_salary:,.2f}")

with col4:
    # Employees Left
    left_count = unique_employees['last_date'].notna().sum()
    st.metric("Employees Left", f"{left_count:,}")

# ======================
# Interactive Filters (Dropdowns)
# ======================
st.sidebar.header("🔍 Filters")

# Department Filter (Dropdown)
dept_options = ['All'] + sorted(df['dept_name'].unique().tolist())
selected_dept = st.sidebar.selectbox("Department Name", options=dept_options, index=0)

# Employment Status Filter (Dropdown)
status_options = ['All', 'Active', 'Left']
selected_status = st.sidebar.selectbox("Employment Status", options=status_options, index=0)

# Apply Filters
if selected_dept == 'All' and selected_status == 'All':
    filtered_df = df.copy()
elif selected_dept == 'All':
    if selected_status == 'Active':
        filtered_df = df[df['last_date'].isna()]
    else:  # Left
        filtered_df = df[df['last_date'].notna()]
elif selected_status == 'All':
    filtered_df = df[df['dept_name'] == selected_dept]
else:
    if selected_status == 'Active':
        filtered_df = df[(df['dept_name'] == selected_dept) & (df['last_date'].isna())]
    else:  # Left
        filtered_df = df[(df['dept_name'] == selected_dept) & (df['last_date'].notna())]

# Create filtered unique employees dataset for analysis
unique_filtered_employees = filtered_df.drop_duplicates(subset=['emp_no']).copy()
cutoff=unique_filtered_employees['last_date'].max()
unique_filtered_employees.loc[:, 'tenure'] = np.where(
    unique_filtered_employees['last_date'].notna(),
    (unique_filtered_employees['last_date'] - unique_filtered_employees['hire_date']).dt.days // 365,
    (cutoff - unique_filtered_employees['hire_date']).dt.days // 365
)

# ======================
# Visualizations Grid
# ======================
st.header("📈 Detailed Analysis")

# First Row
col1, col2 = st.columns(2)
with col1:
    # Salary Distribution
    st.subheader("Salary Distribution")
    fig = px.histogram(unique_filtered_employees, x='salary', nbins=20, 
                      color_discrete_sequence=['#1f77b4'])
    fig.update_layout(bargap=0.1)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    # Tenure Distribution
    st.subheader("Tenure Distribution")
    fig = px.histogram(unique_filtered_employees, x='tenure', nbins=20,
                      color_discrete_sequence=['#2ca02c'])
    st.plotly_chart(fig, use_container_width=True)

# Third Row - Additional Metrics
st.subheader("📌 Deep Dive Analytics")
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Gender Analysis", "Hiring Trends","Rating Distribution","Employee Attrition Based on Tenure" , "Manager Overview"])

with tab1:
    gender_col1, gender_col2 = st.columns(2)
    
    with gender_col1:
        st.markdown("**Gender Distribution**")
        x = filtered_df[['emp_no','sex']].drop_duplicates()
        gender_counts = x['sex'].value_counts()
        
        # Create pie chart with gender count
        fig = px.pie(gender_counts, 
                     values=gender_counts.values, 
                     names=gender_counts.index,
                     category_orders={"sex": ["M", "F"]},
                     color_discrete_sequence=['#1f77b4', '#ff7f0e'])  # Blue for M, Orange for F
        fig.update_layout(showlegend=True, legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.4
        ))
        st.plotly_chart(fig, use_container_width=True)

    # title="Gender Distribution Across Departments"
    with gender_col1:
        st.markdown("**Department-wise Gender Distribution**")
        emp_df = (filtered_df.groupby(['dept_name','sex'])[['emp_no']]
                  .agg(count_of_emp=('emp_no', np.count_nonzero))
                  .reset_index())
        
        # Create bar chart with matching color sequence
        fig = px.bar(emp_df, 
                     x='dept_name', 
                     y='count_of_emp', 
                     color='sex',
                     barmode='group',
                     category_orders={"sex": ["M", "F"]},
                     color_discrete_map={'M': '#1f77b4', 'F': '#ff7f0e'})
        
        fig.update_layout(
            xaxis=dict(tickangle=90),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.5
            ),
            xaxis_title="Department",
            yaxis_title="Employee Count",
            
        )
        st.plotly_chart(fig, use_container_width=True)



    with gender_col2:
        st.markdown("**Employees Left by Gender**")

        # Filter only employees who left
        left_employees = filtered_df[filtered_df['left'] == 1]  

        # Get unique employee records based on emp_no and sex
        x = left_employees[['emp_no', 'sex']].drop_duplicates()
        
        # Count employees who left by gender
        gender_counts = x['sex'].value_counts()

        # Create pie chart
        fig = px.pie(
            gender_counts, 
            values=gender_counts.values, 
            names=gender_counts.index,
            category_orders={"sex": ["M", "F"]},
            color_discrete_sequence=['#1f77b4', '#ff7f0e']  # Blue for M, Orange for F
        )

        fig.update_layout(
            # title="Employees Left by Gender",
            showlegend=True, 
            legend=dict(orientation="h", yanchor="bottom", y=-0.4)
        )

        st.plotly_chart(fig, use_container_width=True)


    with gender_col2:
        st.markdown("**Employees Left by Department and Gender**")

        # Filter only employees who left
        left_emp_df = filtered_df[filtered_df['left'] == 1]

        # Group by department and gender
        emp_left_df = (left_emp_df.groupby(['dept_name', 'sex'])[['emp_no']]
                    .agg(count_of_emp=('emp_no', np.count_nonzero))
                    .reset_index())

        # Create bar chart
        fig = px.bar(
            emp_left_df, 
            x='dept_name', 
            y='count_of_emp', 
            color='sex',
            barmode='group',  # Group bars by gender
            category_orders={"sex": ["M", "F"]},
            color_discrete_map={'M': '#1f77b4', 'F': '#ff7f0e'}  # Blue for M, Orange for F
        )

        fig.update_layout(
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.5
            ),
            xaxis_title="Department",
            yaxis_title="Employees Left",
            # title="Employees Left by Department and Gender"
        )

        st.plotly_chart(fig, use_container_width=True)
  

with tab2:
        hiring_trends = unique_filtered_employees.groupby(filtered_df['hire_date'].dt.year)['emp_no'].count()
        fig = px.line(hiring_trends, x=hiring_trends.index, y=hiring_trends.values,markers=True,
                    title="Year-wise Hiring Trends")
        st.plotly_chart(fig, use_container_width=True)

        # Filter only employees who left
        left_emp_df = unique_filtered_employees[ unique_filtered_employees['left'] == 1]
        hiring_trends = left_emp_df.groupby(filtered_df['hire_date'].dt.year)['emp_no'].count()
        fig = px.line(hiring_trends, x=hiring_trends.index, y=hiring_trends.values,markers=True,
                    title="Year-wise Employees Left in Hiring Years ")
        st.plotly_chart(fig, use_container_width=True)
    

with tab3:
        # Group by department and count performance ratings
        performance_count = filtered_df.groupby('dept_name').agg(
            A=('Last_performance_rating', lambda x: (x == 'A').sum()),
            B=('Last_performance_rating', lambda x: (x == 'B').sum()),
            C=('Last_performance_rating', lambda x: (x == 'C').sum()),
            S=('Last_performance_rating', lambda x: (x == 'S').sum()),
            PIP=('Last_performance_rating', lambda x: (x == 'PIP').sum())
        ).reset_index()

        # Melt the data for Plotly
        performance_count_melted = performance_count.melt(
            id_vars=['dept_name'], 
            var_name='Performance Rating', 
            value_name='Count'
        )

        # Define custom color mapping (PIP in Red)
        custom_colors = {
            'A': '#2ca02c',   # Green
            'B': '#1f77b4',   # Blue
            'C': '#ffbb78',   # Light Orange
            'S': '#9467bd',   # Purple
            'PIP': '#d62728'  # Red (for least rating)
        }

        # Create stacked bar chart using Plotly
        fig = px.bar(
            performance_count_melted, 
            x='dept_name', 
            y='Count', 
            color='Performance Rating',
            barmode='stack', 
            title="Performance Rating Distribution by Department",
            labels={'dept_name': 'Department', 'Count': 'Number of Employees'},
            color_discrete_map=custom_colors  # Change color theme
        )

        st.plotly_chart(fig, use_container_width=True)


                # Filter only employees who left
        left_emp_df = filtered_df[filtered_df['left'] == 1]

        # Group by department and count performance ratings for employees who left
        performance_left_count = left_emp_df.groupby('dept_name').agg(
            A=('Last_performance_rating', lambda x: (x == 'A').sum()),
            B=('Last_performance_rating', lambda x: (x == 'B').sum()),
            C=('Last_performance_rating', lambda x: (x == 'C').sum()),
            S=('Last_performance_rating', lambda x: (x == 'S').sum()),
            PIP=('Last_performance_rating', lambda x: (x == 'PIP').sum())
        ).reset_index()

        # Melt the data for Plotly
        performance_left_melted = performance_left_count.melt(
            id_vars=['dept_name'], 
            var_name='Performance Rating', 
            value_name='Count'
        )

        # Define custom color mapping (PIP in Red)
        custom_colors = {
            'A': '#2ca02c',   # Green
            'B': '#1f77b4',   # Blue
            'C': '#ffbb78',   # Light Orange
            'S': '#9467bd',   # Purple
            'PIP': '#d62728'  # Red (for least rating)
        }

        # Create stacked bar chart using Plotly
        fig = px.bar(
            performance_left_melted, 
            x='dept_name', 
            y='Count', 
            color='Performance Rating',
            barmode='stack', 
            title="Performance Rating Distribution of Employees Who Left by Department",
            labels={'dept_name': 'Department', 'Count': 'Number of Employees Left'},
            color_discrete_map=custom_colors  # Change color theme
        )

        # Display in Streamlit
        st.plotly_chart(fig, use_container_width=True)


                # Create KDE (density) plot using Plotly
with tab4:
        fig = px.histogram(
            unique_filtered_employees, 
            x="tenure", 
            color="left",  # Different colors for employees who left vs stayed
            nbins=50,  # More bins for smoother density
            histnorm='probability density',  # Ensures sum of densities = 1
            barmode='overlay',  # Overlay both distributions
            opacity=0.5,  # Similar to alpha in Seaborn
            title="Employee Attrition Based on Tenure",
            labels={"tenure": "Tenure (Years)", "left": "Attrition Status"},
            color_discrete_map={1: '#ff7f0e', 0: '#1f77b4'}  # Orange for left, Blue for stayed
        )

        # Display in Streamlit
        st.plotly_chart(fig, use_container_width=True)

with tab5:
    st.markdown("**Manager Overview**")
    managers_df = df.loc[df['title']=='Manager',['title','emp_no','dept_no','dept_name','first_name','last_name','hire_date','salary']]
    st.dataframe(
        managers_df[['dept_name', 'first_name', 'last_name', 'hire_date', 'salary']],
        column_config={
            "dept_name": "Department",
            "first_name": "First Name",
            "last_name": "Last Name",
            "hire_date": "Hire Date",
            "salary": "Salary"
        },
        use_container_width=True
    )
