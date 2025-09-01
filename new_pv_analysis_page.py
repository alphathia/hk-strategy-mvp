"""
New Portfolio Analysis Dashboard Implementation
To be integrated into the main dashboard.py file
"""

# Portfolio Analysis Dashboard page content to replace lines 1539-2049 in dashboard.py

portfolio_analysis_page_code = '''
elif st.session_state.current_page == 'pv_analysis':
    # Portfolio Analysis Dashboard
    st.subheader("📈 Portfolio Analysis Dashboard")
    
    # Initialize Portfolio Analysis Manager
    if 'portfolio_analysis_manager' not in st.session_state:
        from portfolio_analysis_manager import PortfolioAnalysisManager
        st.session_state.portfolio_analysis_manager = PortfolioAnalysisManager(st.session_state.db_manager)
    
    # Check if portfolio is selected
    selected_portfolio = st.session_state.get('selected_portfolio')
    
    if not selected_portfolio:
        # Show "Load Portfolio" page
        st.markdown("## 📂 Load Portfolio")
        st.markdown("Select a portfolio to begin analysis.")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            portfolio_keys = list(st.session_state.portfolios.keys())
            if portfolio_keys:
                selected = st.selectbox(
                    "Choose Portfolio:",
                    options=portfolio_keys,
                    format_func=lambda x: f"{st.session_state.portfolios[x]['name']}"
                )
                
                if st.button("📂 Load Portfolio", type="primary"):
                    st.session_state.selected_portfolio = selected
                    st.rerun()
            else:
                st.error("No portfolios available. Please create a portfolio first.")
                
        with col2:
            st.markdown("### Quick Actions")
            if st.button("🔙 Back to Overview"):
                st.session_state.current_page = 'overview'
                st.rerun()
        st.stop()
    
    # Portfolio is selected - show analysis interface
    current_portfolio = st.session_state.portfolios[selected_portfolio]
    
    # Header with portfolio name and create button
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"### Portfolio Analysis: **{current_portfolio['name']}**")
    with col2:
        if st.button("➕ Create New Portfolio Analysis", type="primary"):
            st.session_state.show_create_analysis_dialog = True
            st.rerun()
    
    # Create New Analysis Dialog
    if st.session_state.get('show_create_analysis_dialog', False):
        with st.container():
            st.markdown("---")
            st.markdown("### ➕ Create New Portfolio Analysis")
            
            col1, col2 = st.columns(2)
            with col1:
                analysis_name = st.text_input(
                    "Analysis Name*",
                    placeholder="e.g., Q1 2024 Performance Review",
                    help="Enter a unique name for this analysis"
                )
                start_date = st.date_input(
                    "Start Date*",
                    value=date.today() - timedelta(days=90),
                    max_value=date.today()
                )
            
            with col2:
                start_cash = st.number_input(
                    "Start Cash (HKD)*",
                    min_value=0.0,
                    value=100000.0,
                    step=10000.0,
                    format="%.2f"
                )
                end_date = st.date_input(
                    "End Date*",
                    value=date.today(),
                    max_value=date.today()
                )
            
            # Validation and buttons
            error_msg = ""
            if not analysis_name.strip():
                error_msg = "Analysis name is required"
            elif end_date <= start_date:
                error_msg = "End date must be after start date"
            elif not st.session_state.portfolio_analysis_manager.validate_analysis_name(selected_portfolio, analysis_name.strip()):
                error_msg = f"Analysis name '{analysis_name.strip()}' already exists for this portfolio"
            
            if error_msg:
                st.error(f"❌ {error_msg}")
            
            col_save, col_cancel = st.columns(2)
            with col_save:
                if st.button("💾 Save", disabled=bool(error_msg), type="primary", use_container_width=True):
                    success, message, analysis_id = st.session_state.portfolio_analysis_manager.create_analysis(
                        portfolio_id=selected_portfolio,
                        analysis_name=analysis_name.strip(),
                        start_date=start_date,
                        end_date=end_date,
                        start_cash=start_cash
                    )
                    
                    if success:
                        st.success(f"✅ {message}")
                        st.session_state.show_create_analysis_dialog = False
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
            
            with col_cancel:
                if st.button("❌ Cancel", use_container_width=True):
                    st.session_state.show_create_analysis_dialog = False
                    st.rerun()
            
            st.markdown("---")
    
    # Portfolio Analysis Table
    st.markdown("### 📊 Portfolio Analyses")
    
    # Get analyses for this portfolio
    analyses_df = st.session_state.portfolio_analysis_manager.get_analysis_summary(selected_portfolio)
    
    if analyses_df.empty:
        st.info("No portfolio analyses found. Create your first analysis using the button above.")
    else:
        # Create responsive table with all required columns
        st.markdown("#### Analysis Summary")
        
        # Prepare display data with formatting
        display_data = []
        for _, row in analyses_df.iterrows():
            display_data.append({
                "Name": row['name'],
                "Start Date": row['start_date'].strftime("%Y-%m-%d") if pd.notna(row['start_date']) else "-",
                "End Date": row['end_date'].strftime("%Y-%m-%d") if pd.notna(row['end_date']) else "-",
                "Start Cash": f"${row['start_cash']:,.0f}" if pd.notna(row['start_cash']) else "-",
                "End Cash": f"${row['end_cash']:,.0f}" if pd.notna(row['end_cash']) and row['end_cash'] != 0 else "-",
                "Start Equity Value": f"${row['start_equity_value']:,.0f}" if pd.notna(row['start_equity_value']) and row['start_equity_value'] != 0 else "-",
                "End Equity Value": f"${row['end_equity_value']:,.0f}" if pd.notna(row['end_equity_value']) and row['end_equity_value'] != 0 else "-", 
                "Start Total Value": f"${row['start_total_value']:,.0f}" if pd.notna(row['start_total_value']) and row['start_total_value'] != 0 else "-",
                "End Total Value": f"${row['end_total_value']:,.0f}" if pd.notna(row['end_total_value']) and row['end_total_value'] != 0 else "-",
                "Total Equity Gain/Loss": f"${row['total_equity_gain_loss']:+,.0f}" if pd.notna(row['total_equity_gain_loss']) and row['total_equity_gain_loss'] != 0 else "-",
                "Total Value Gain/Loss": f"${row['total_value_gain_loss']:+,.0f}" if pd.notna(row['total_value_gain_loss']) and row['total_value_gain_loss'] != 0 else "-",
                "Compare": False,  # Checkbox column
                "_id": row['id']  # Hidden ID for actions
            })
        
        # Display table with custom CSS for font sizing
        st.markdown("""
        <style>
        .stDataFrame {
            font-size: 11px !important;
        }
        .stDataFrame th {
            font-size: 10px !important;
            background-color: #f0f0f0;
        }
        .stDataFrame td {
            font-size: 11px !important;
            padding: 4px 8px !important;
        }
        .clickable-name {
            color: #1f77b4;
            cursor: pointer;
            text-decoration: underline;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Create editable dataframe without the _id column for display
        display_df = pd.DataFrame(display_data)
        edited_df = st.data_editor(
            display_df.drop('_id', axis=1),
            column_config={
                "Name": st.column_config.TextColumn("Name", help="Click to drill down to Portfolio-Analysis-Equity"),
                "Compare": st.column_config.CheckboxColumn("Compare", help="Select analyses to compare")
            },
            hide_index=True,
            use_container_width=True,
            key="analysis_table"
        )
        
        # Handle table interactions
        if st.button("🔄 Refresh Table"):
            st.rerun()
        
        # Compare functionality
        selected_for_compare = []
        for idx, row in edited_df.iterrows():
            if row['Compare']:
                selected_for_compare.append(display_data[idx]['_id'])
        
        if selected_for_compare:
            st.info(f"📊 Selected {len(selected_for_compare)} analyses for comparison")
            if st.button("📊 Compare Selected Analyses"):
                st.info("🚧 Comparison feature coming soon!")
        
        # Action buttons for management
        if len(analyses_df) > 0:
            st.markdown("#### Analysis Actions")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                selected_analysis = st.selectbox(
                    "Select Analysis:",
                    options=range(len(analyses_df)),
                    format_func=lambda x: analyses_df.iloc[x]['name']
                )
            
            with col2:
                if st.button("🗑️ Delete Selected"):
                    analysis_id = analyses_df.iloc[selected_analysis]['id']
                    success, message = st.session_state.portfolio_analysis_manager.delete_analysis(analysis_id)
                    if success:
                        st.success(f"✅ {message}")
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
            
            with col3:
                if st.button("📝 View Transactions"):
                    analysis_id = analyses_df.iloc[selected_analysis]['id']
                    transactions_df = st.session_state.portfolio_analysis_manager.get_analysis_transactions(analysis_id)
                    
                    if not transactions_df.empty:
                        st.markdown("#### Transaction History")
                        st.dataframe(transactions_df, use_container_width=True)
                    else:
                        st.info("No transactions found for this analysis")
    
    # Quick navigation
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🔙 Back to Portfolio Dashboard"):
            st.session_state.current_page = 'portfolio'
            st.rerun()
    with col2:
        if st.button("📊 All Portfolios Overview"):
            st.session_state.current_page = 'overview'
            st.rerun()
    with col3:
        if st.button("🔄 Load Different Portfolio"):
            st.session_state.selected_portfolio = None
            st.rerun()
'''

print("New Portfolio Analysis Dashboard code generated successfully!")
print("This needs to be manually integrated into dashboard.py")