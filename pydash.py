import streamlit as st
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.express as px
from datetime import datetime
import os

# Load environment variable
DRIVE_CSV_URL = os.getenv("DRIVE_CSV_URL")

# Read CSV from Google Drive
df = pd.read_csv(DRIVE_CSV_URL,encoding='utf-8')

# Ensure date columns are in datetime format
df['hire_date'] = pd.to_datetime(df['hire_date'],dayfirst=True)
df['last_date'] = pd.to_datetime(df['last_date'],dayfirst=True)


# ======================
# Key Metrics Section
# ======================
st.title("📈 Employee Analytics Dashboard")
st.header("📊 Key Metrics")
col1, col2, col3, col4 = st.columns(4)
with col1:
    #Total Employees
    total_employees = df['emp_no'].nunique()
    st.metric("Total Employees", f"{total_employees:,}")
    
    #Total Departments
with col2:
    total_depts = df['dept_name'].nunique()
    st.metric("Total Departments", f"{total_depts:,}")

with col3:
    #Average Salary
    # Remove duplicate employee records, keeping only the first occurrence
    unique_employees = df.drop_duplicates(subset=['emp_no']).copy()
    avg_salary = unique_employees['salary'].mean()
    st.metric("Average Salary", f"₹{avg_salary:,.2f}")

with col4:
    #Average Tenure by removing employees who work in two different departments
    # unique_employees = df.drop_duplicates(subset=['emp_no']).copy()
    unique_employees.loc[:,'tenure'] = np.where(
    unique_employees['last_date'].notna(),
    (unique_employees['last_date'] - unique_employees['hire_date']).dt.days // 365,
    (unique_employees['hire_date'].max() - unique_employees['hire_date']).dt.days // 365
)
    
    avg_tenure = unique_employees['tenure'].mean()
    st.metric("Average Tenure", f"{avg_tenure:.1f} years")

# ======================
# Interactive Filters
# ======================
# Sidebar Filters
st.sidebar.header("🔍 Filters")

# Department Filter
with st.sidebar.expander("**Departments**", expanded=True):
    # Select All checkbox
    all_depts = st.checkbox("Select All Departments", 
                          value=True,
                          key="all_depts")
    
    # Search box for departments
    dept_search = st.text_input("Search Departments:", key="dept_search")
    
    # Filtered department list
    filtered_depts = [dept for dept in df["dept_name"].unique() 
                     if dept_search.lower() in dept.lower()]
    
    # Create columns for better layout
    cols = st.columns(2)
    selected_depts = []
    
    # Show checkboxes in 2 columns
    for idx, dept in enumerate(filtered_depts):
        with cols[idx % 2]:
            if all_depts:
                selected = st.checkbox(dept, value=True, key=f"dept_{dept}")
            else:
                selected = st.checkbox(dept, key=f"dept_{dept}")
            if selected:
                selected_depts.append(dept)

# Job Title Filter
with st.sidebar.expander("**Job Titles**", expanded=True):
    # Select All checkbox
    all_titles = st.checkbox("Select All Titles", 
                           value=True,
                           key="all_titles")
    
    # Search box for titles
    title_search = st.text_input("Search Titles:", key="title_search")
    
    # Filtered title list
    filtered_titles = [title for title in df["title"].unique() 
                      if title_search.lower() in title.lower()]
    
    # Create columns for better layout
    cols = st.columns(2)
    selected_titles = []
    
    # Show checkboxes in 2 columns
    for idx, title in enumerate(filtered_titles):
        with cols[idx % 2]:
            if all_titles:
                selected = st.checkbox(title, value=True, key=f"title_{title}")
            else:
                selected = st.checkbox(title, key=f"title_{title}")
            if selected:
                selected_titles.append(title)

# Apply filters
filtered_df = df[
    (df["dept_name"].isin(selected_depts)) &
    (df["title"].isin(selected_titles))
]

# Create filtered unique employees dataset for analysis where employee count should not be repeated
unique_filtered_employees = filtered_df.drop_duplicates(subset=['emp_no']).copy()
unique_filtered_employees.loc[:,'tenure'] = np.where(
    unique_filtered_employees['last_date'].notna(),
    (unique_filtered_employees['last_date'] - unique_filtered_employees['hire_date']).dt.days // 365,
    (unique_filtered_employees['hire_date'].max() - unique_filtered_employees['hire_date']).dt.days // 365
)

# Display Filtered Data
st.write("### Filtered Data")
st.dataframe(filtered_df)

# ======================
# Visualizations Grid
# ======================
st.header("📈 Detailed Analysis")

# First Row
col1, col2 = st.columns(2)
with col1:
    #"Salary Distribution"
    st.subheader("Salary Distribution")
    fig = px.histogram(unique_filtered_employees, x='salary', nbins=20, 
                      color_discrete_sequence=['#1f77b4'])
    fig.update_layout(bargap=0.1)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    #Tenure Distribution
    st.subheader("Tenure Distribution")
    fig = px.histogram(unique_filtered_employees, x='tenure', nbins=20,
                      color_discrete_sequence=['#2ca02c'])
    st.plotly_chart(fig, use_container_width=True)



# Third Row - Additional Metrics
st.subheader("📌 Deep Dive Analytics")
tab1, tab2, tab3, tab4 = st.tabs(["Gender Analysis", "Hiring Trends","Rating Distribution", "Manager Overview"])

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
    with gender_col2:
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
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.5
            ),
            xaxis_title="Department",
            yaxis_title="Employee Count",
            
        )
        st.plotly_chart(fig, use_container_width=True)
  

with tab2:
    hiring_trends = unique_filtered_employees.groupby(filtered_df['hire_date'].dt.year)['emp_no'].count()
    fig = px.line(hiring_trends, x=hiring_trends.index, y=hiring_trends.values,markers=True,
                 title="Year-wise Hiring Trends")
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

with tab4:
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


# ======================
# Raw Data Section
# ======================
st.header("🔍 Data Explorer")
with st.expander("View Filtered Data"):
    st.dataframe(filtered_df, use_container_width=True)
    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Filtered Data",
        data=csv,
        file_name="employee_data.csv",
        mime="text/csv"
    )
