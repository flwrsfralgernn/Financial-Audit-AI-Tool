import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Travel Audit Analysis", layout="wide")

st.title("📊 Travel Audit Analysis Tool")
st.write("Upload an Excel file to analyze spending patterns and distributions")

# File upload
uploaded_file = st.file_uploader("Choose an Excel file", type=['xlsx', 'xls'])

if uploaded_file is not None:
    try:
        # Read Excel file
        df = pd.read_excel(uploaded_file)
        
        st.success(f"File uploaded successfully! Found {len(df)} records.")
        
        # Display first few rows
        with st.expander("Preview Data"):
            st.dataframe(df.head())
        
        # Analysis options
        analysis_type = st.selectbox(
            "Select Analysis Type:",
            ["Spending Distribution", "College Spending Comparison", "Over-Budget Analysis"]
        )
        
        if analysis_type == "Spending Distribution":
            st.subheader("💰 Spending Distribution Analysis")
            
            # Assume amount column exists
            amount_cols = [col for col in df.columns if 'amount' in col.lower() or 'cost' in col.lower() or 'expense' in col.lower() or 'spend' in col.lower()]
            
            if amount_cols:
                amount_col = st.selectbox("Select amount column:", amount_cols)
                
                # Basic stats
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Spent", f"${df[amount_col].sum():,.2f}")
                with col2:
                    st.metric("Average", f"${df[amount_col].mean():,.2f}")
                with col3:
                    st.metric("Median", f"${df[amount_col].median():,.2f}")
                with col4:
                    st.metric("Max Expense", f"${df[amount_col].max():,.2f}")
                
                # Distribution chart
                fig = px.histogram(df, x=amount_col, nbins=30, title="Spending Distribution")
                st.plotly_chart(fig, use_container_width=True)
                
        elif analysis_type == "College Spending Comparison":
            st.subheader("🏫 College Spending Comparison")
            
            # Find college/department column
            college_cols = [col for col in df.columns if any(word in col.lower() for word in ['college', 'department', 'school', 'unit'])]
            amount_cols = [col for col in df.columns if 'amount' in col.lower() or 'cost' in col.lower() or 'expense' in col.lower() or 'spend' in col.lower()]
            
            if college_cols and amount_cols:
                college_col = st.selectbox("Select college/department column:", college_cols)
                amount_col = st.selectbox("Select amount column:", amount_cols)
                
                # Group by college
                college_spending = df.groupby(college_col)[amount_col].agg(['sum', 'count', 'mean']).reset_index()
                college_spending.columns = [college_col, 'Total_Spent', 'Number_of_Expenses', 'Average_Expense']
                college_spending = college_spending.sort_values('Total_Spent', ascending=False)
                
                # Top spender
                top_college = college_spending.iloc[0]
                st.success(f"🏆 Highest Spending: {top_college[college_col]} - ${top_college['Total_Spent']:,.2f}")
                
                # Bar chart
                fig = px.bar(college_spending.head(10), x=college_col, y='Total_Spent', 
                           title="Top 10 Colleges by Total Spending")
                fig.update_xaxis(tickangle=45)
                st.plotly_chart(fig, use_container_width=True)
                
                # Summary table
                st.dataframe(college_spending, use_container_width=True)
                
        elif analysis_type == "Over-Budget Analysis":
            st.subheader("⚠️ Over-Budget Analysis")
            
            # Look for budget vs actual columns
            budget_cols = [col for col in df.columns if 'budget' in col.lower()]
            actual_cols = [col for col in df.columns if 'actual' in col.lower() or 'spent' in col.lower() or 'expense' in col.lower()]
            
            if budget_cols and actual_cols:
                budget_col = st.selectbox("Select budget column:", budget_cols)
                actual_col = st.selectbox("Select actual spending column:", actual_cols)
                
                # Calculate over-budget
                df['over_budget'] = df[actual_col] - df[budget_col]
                df['over_budget_pct'] = (df['over_budget'] / df[budget_col]) * 100
                
                over_budget_items = df[df['over_budget'] > 0]
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Over-Budget Items", len(over_budget_items))
                with col2:
                    st.metric("Total Over-Budget Amount", f"${over_budget_items['over_budget'].sum():,.2f}")
                with col3:
                    st.metric("Percentage Over-Budget", f"{(len(over_budget_items)/len(df)*100):.1f}%")
                
                if len(over_budget_items) > 0:
                    # Over-budget chart
                    fig = px.scatter(over_budget_items, x=budget_col, y=actual_col, 
                                   hover_data=['over_budget_pct'], 
                                   title="Budget vs Actual Spending (Over-Budget Items)")
                    fig.add_line(x=[0, df[budget_col].max()], y=[0, df[budget_col].max()], 
                               line_dash="dash", line_color="red")
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Top over-budget items
                    st.subheader("Top Over-Budget Items")
                    top_over = over_budget_items.nlargest(10, 'over_budget')
                    st.dataframe(top_over[['over_budget', 'over_budget_pct', budget_col, actual_col]], use_container_width=True)
                else:
                    st.success("🎉 No items went over budget!")
            else:
                st.warning("Please ensure your Excel file has budget and actual spending columns.")
                st.info("Expected column names should contain: 'budget', 'actual', 'spent', or 'expense'")
        
    except Exception as e:
        st.error(f"Error reading file: {str(e)}")
        st.info("Please ensure your Excel file is properly formatted.")
else:
    st.info("👆 Please upload an Excel file to begin analysis")
    
    # Sample data format
    st.subheader("Expected Data Format")
    sample_data = {
        'College': ['Engineering', 'Business', 'Arts'],
        'Budget': [10000, 8000, 6000],
        'Actual_Expense': [12000, 7500, 6500],
        'Description': ['Lab Equipment', 'Software License', 'Art Supplies']
    }
    st.dataframe(pd.DataFrame(sample_data))