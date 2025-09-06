"""
Strategy Editor Page for HK Strategy Dashboard.
Manages trading strategy bases (BBRK, SBDN, BDIV, etc.) and their signal magnitudes (1-9).

Extracted from dashboard.py lines 4319-4849.
"""

import streamlit as st
import logging
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
import re

from src.pages.base_page import BasePage

# Setup logging
logger = logging.getLogger(__name__)


class StrategyEditorPage(BasePage):
    """Strategy editor page for managing TXYZN trading strategies."""
    
    def __init__(self):
        super().__init__('strategy_editor')
    
    def _render_content(self) -> None:
        """Render the strategy editor page content."""
        st.subheader("⚙️ Strategy Editor")
        st.markdown("*Manage trading strategy bases (BBRK, SBDN, BDIV, etc.) and their signal magnitudes (1-9)*")
        
        # Initialize database connection
        conn = self._get_database_connection()
        if not conn:
            return
        
        try:
            # Tab navigation
            tab1, tab2, tab3, tab4 = st.tabs([
                "🎯 Strategy Bases", 
                "📊 Signal Magnitudes", 
                "📈 Recent Signals", 
                "⚙️ Configuration"
            ])
            
            with tab1:
                self._render_strategy_bases_tab(conn)
            
            with tab2:
                self._render_signal_magnitudes_tab(conn)
            
            with tab3:
                self._render_recent_signals_tab(conn)
            
            with tab4:
                self._render_configuration_tab(conn)
            
            # Navigation buttons
            self._render_navigation_buttons()
            
        finally:
            # Close database connection
            try:
                conn.close()
            except:
                pass
    
    def _get_database_connection(self) -> Optional[Any]:
        """Get database connection."""
        try:
            if hasattr(st.session_state, 'db_manager'):
                return st.session_state.db_manager.get_connection()
            else:
                st.error("❌ Database manager not available")
                return None
        except Exception as e:
            logger.error(f"Database connection failed: {str(e)}")
            st.error(f"❌ Database connection failed: {str(e)}")
            return None
    
    def _render_strategy_bases_tab(self, conn: Any) -> None:
        """Render strategy bases management tab."""
        st.markdown("### Strategy Base Catalog")
        st.markdown("*These are the actual strategies - the 'XYZ' part of TXYZN format*")
        
        try:
            cur = conn.cursor()
            
            # Get strategy base statistics
            cur.execute("""
            SELECT 
                COUNT(*) as total_base_strategies,
                COUNT(DISTINCT category) as categories,
                COUNT(CASE WHEN signal_side = 'B' THEN 1 END) as buy_strategies,
                COUNT(CASE WHEN signal_side = 'S' THEN 1 END) as sell_strategies,
                COUNT(CASE WHEN signal_side = 'H' THEN 1 END) as hold_strategies
            FROM strategy_catalog
            """)
            stats = cur.fetchone()
            
            if stats:
                col1, col2, col3, col4, col5 = st.columns(5)
                with col1:
                    st.metric("Base Strategies", stats[0] or 0)
                with col2:
                    st.metric("Categories", stats[1] or 0)
                with col3:
                    st.metric("Buy Strategies", stats[2] or 0)
                with col4:
                    st.metric("Sell Strategies", stats[3] or 0)
                with col5:
                    st.metric("Hold Strategies", stats[4] or 0)
            
            # Strategy filters
            self._render_strategy_filters(cur)
            
        except Exception as e:
            logger.error(f"Error loading strategy bases: {str(e)}")
            st.error(f"Error loading strategy bases: {str(e)}")
    
    def _render_strategy_filters(self, cur: Any) -> None:
        """Render strategy base filters and display."""
        col1, col2, col3 = st.columns(3)
        with col1:
            category_filter = st.selectbox(
                "Category Filter:",
                ["All", "breakout", "mean-reversion", "trend", "divergence", "level"]
            )
        with col2:
            side_filter = st.selectbox("Signal Side Filter:", ["All", "B", "S", "H"])
        with col3:
            complexity_filter = st.selectbox("Complexity Filter:", ["All", "simple", "moderate", "complex"])
        
        # Build query with filters
        query = """
        SELECT strategy_base, strategy_name, signal_side, category, description, 
               required_indicators, optional_indicators, usage_guidelines, 
               risk_considerations, market_conditions, implementation_complexity, priority
        FROM strategy_catalog WHERE 1=1
        """
        params = []
        
        if category_filter != "All":
            query += " AND category = %s"
            params.append(category_filter)
        if side_filter != "All":
            query += " AND signal_side = %s"
            params.append(side_filter)
        if complexity_filter != "All":
            query += " AND implementation_complexity = %s"
            params.append(complexity_filter)
        
        query += " ORDER BY priority, category, strategy_base"
        
        try:
            cur.execute(query, params)
            base_strategies = cur.fetchall()
            
            # Display strategy bases
            st.markdown("### Available Strategy Bases")
            if base_strategies:
                self._display_strategy_bases(base_strategies)
            else:
                st.info("No strategy bases found matching the selected filters.")
        
        except Exception as e:
            logger.error(f"Error querying strategy bases: {str(e)}")
            st.error(f"Error loading strategy bases: {str(e)}")
    
    def _display_strategy_bases(self, base_strategies: List[Tuple]) -> None:
        """Display strategy bases in expandable format."""
        for strategy in base_strategies:
            (base, name, side, category, description, req_indicators, 
             opt_indicators, usage, risks, conditions, complexity, priority) = strategy
            
            # Create TXYZN example with different magnitudes
            side_name = {"B": "Buy", "S": "Sell", "H": "Hold"}[side]
            side_color = {"B": "🟢", "S": "🔴", "H": "🟡"}[side]
            
            with st.expander(f"{side_color} **{base}** - {name} ({side_name})"):
                col1, col2 = st.columns([3, 2])
                
                with col1:
                    st.markdown(f"**Description:** {description}")
                    st.markdown(f"**Category:** {category.title()}")
                    st.markdown(f"**Complexity:** {complexity.title()}")
                    
                    if usage:
                        st.markdown(f"**Best Used:** {usage}")
                    if risks:
                        st.markdown(f"**Risk Notes:** {risks}")
                    
                    # Show market conditions if available
                    if conditions:
                        conditions_list = conditions if isinstance(conditions, list) else []
                        if conditions_list:
                            st.markdown(f"**Market Conditions:** {', '.join(conditions_list)}")
                
                with col2:
                    st.markdown("**TXYZN Signal Examples:**")
                    st.markdown(f"• `{base}1` - Weak signal (magnitude 1)")
                    st.markdown(f"• `{base}5` - Moderate signal (magnitude 5)")  
                    st.markdown(f"• `{base}9` - Strong signal (magnitude 9)")
                    
                    # Show required indicators
                    if req_indicators:
                        indicators_list = req_indicators if isinstance(req_indicators, list) else []
                        if indicators_list and len(indicators_list) > 0:
                            st.markdown("**Required Indicators:**")
                            for indicator in indicators_list[:3]:  # Show first 3
                                st.markdown(f"• {indicator}")
                            if len(indicators_list) > 3:
                                st.markdown(f"• ... and {len(indicators_list) - 3} more")
    
    def _render_signal_magnitudes_tab(self, conn: Any) -> None:
        """Render signal magnitudes management tab."""
        st.markdown("### Signal Magnitude Management")
        st.markdown("*Configure how magnitude (1-9) reflects signal strength/confidence*")
        
        # Magnitude explanation
        st.info("""
        **Understanding Signal Magnitude (The 'N' in TXYZN):**
        - Magnitude 1-3: Weak signals (experimental/low confidence)
        - Magnitude 4-6: Moderate signals (standard trading signals)  
        - Magnitude 7-9: Strong signals (high confidence/institutional grade)
        """)
        
        # Interactive magnitude simulator
        self._render_magnitude_simulator(conn)
        
        # Show recent trading signals if any exist
        self._render_magnitude_statistics(conn)
    
    def _render_magnitude_simulator(self, conn: Any) -> None:
        """Render magnitude simulator interface."""
        st.markdown("### Signal Magnitude Simulator")
        col1, col2 = st.columns([2, 3])
        
        with col1:
            try:
                cur = conn.cursor()
                cur.execute("SELECT strategy_base, strategy_name FROM strategy_catalog ORDER BY strategy_base")
                available_bases = cur.fetchall()
                
                if available_bases:
                    base_options = [f"{base} - {name}" for base, name in available_bases]
                    selected_base_display = st.selectbox("Select Strategy Base:", base_options)
                    selected_base = selected_base_display.split(" - ")[0] if selected_base_display else "BBRK"
                    
                    # Magnitude slider
                    magnitude = st.slider("Signal Magnitude", min_value=1, max_value=9, value=5)
                    
                    # Generate example signal
                    example_signal = f"{selected_base}{magnitude}"
                    st.markdown(f"**Generated Signal:** `{example_signal}`")
                else:
                    st.warning("No strategy bases available")
            
            except Exception as e:
                logger.error(f"Error loading strategy bases: {str(e)}")
                st.error(f"Error loading strategy bases: {str(e)}")
        
        with col2:
            # Show magnitude characteristics
            st.markdown("### Magnitude Characteristics")
            
            magnitude_info = self._get_magnitude_info()
            
            for mag, info in magnitude_info.items():
                if 'magnitude' in locals() and mag == magnitude:
                    st.markdown(f"**{info['color']} {mag}: {info['label']}** - {info['desc']} ← *Selected*")
                else:
                    st.markdown(f"{info['color']} {mag}: {info['label']} - {info['desc']}")
    
    def _render_magnitude_statistics(self, conn: Any) -> None:
        """Render magnitude statistics from database."""
        st.markdown("---")
        
        try:
            cur = conn.cursor()
            cur.execute("""
            SELECT 
                COUNT(*) as total_signals,
                COUNT(DISTINCT symbol) as symbols_with_signals,
                COUNT(DISTINCT strategy_base) as unique_bases_used,
                AVG(signal_magnitude) as avg_magnitude,
                MAX(created_at) as latest_signal
            FROM trading_signals
            WHERE signal_type IS NOT NULL AND strategy_base IS NOT NULL
            """)
            signal_stats = cur.fetchone()
            
            if signal_stats and signal_stats[0] and signal_stats[0] > 0:
                st.markdown("### Recent Trading Signals")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Signals", signal_stats[0])
                with col2:
                    st.metric("Symbols", signal_stats[1])  
                with col3:
                    st.metric("Strategy Bases", signal_stats[2])
                with col4:
                    st.metric("Avg Magnitude", f"{signal_stats[3]:.1f}" if signal_stats[3] else "N/A")
                
                self._render_recent_magnitude_signals(cur)
            else:
                st.info("No trading signals found in database. Generate some signals to see them here.")
        
        except Exception as e:
            logger.error(f"Error loading signal statistics: {str(e)}")
            st.error(f"Error loading signals: {str(e)}")
    
    def _render_recent_magnitude_signals(self, cur: Any) -> None:
        """Render recent signals with magnitude information."""
        try:
            cur.execute("""
            SELECT ts.symbol, ts.signal_type, ts.strategy_base, ts.signal_magnitude, 
                   ts.price, ts.created_at, sc.strategy_name
            FROM trading_signals ts
            LEFT JOIN strategy_catalog sc ON ts.strategy_base = sc.strategy_base
            WHERE ts.signal_type IS NOT NULL
            ORDER BY ts.created_at DESC
            LIMIT 10
            """)
            recent_signals = cur.fetchall()
            
            if recent_signals:
                magnitude_info = self._get_magnitude_info()
                
                for signal in recent_signals:
                    symbol, signal_type, base, magnitude, price, timestamp, strategy_name = signal
                    magnitude_info_display = magnitude_info.get(magnitude, {"color": "⚪", "label": "Unknown"})
                    
                    with st.expander(f"**{symbol}** - {signal_type} {magnitude_info_display['color']}"):
                        col1, col2 = st.columns([2, 1])
                        with col1:
                            st.markdown(f"**Strategy Base:** {base} ({strategy_name or 'Unknown'})")
                            st.markdown(f"**Signal:** {signal_type}")
                            st.markdown(f"**Price:** ${price:.2f}")
                            st.markdown(f"**Timestamp:** {str(timestamp)[:16]}")
                        with col2:
                            st.markdown(f"**Magnitude:** {magnitude}/9")
                            st.markdown(f"**Level:** {magnitude_info_display['label']}")
        
        except Exception as e:
            logger.error(f"Error loading recent signals: {str(e)}")
    
    def _render_recent_signals_tab(self, conn: Any) -> None:
        """Render recent TXYZN signals tab."""
        st.markdown("### Recent TXYZN Signals")
        st.markdown("*View recently generated signals from the trading_signals table*")
        
        try:
            cur = conn.cursor()
            
            # Get recent signals with full details
            cur.execute("""
            SELECT 
                ts.symbol,
                ts.signal_type,
                ts.strategy_base,
                ts.signal_magnitude,
                ts.signal_strength,
                ts.price,
                ts.volume,
                ts.rsi,
                ts.created_at,
                sc.strategy_name,
                sc.category
            FROM trading_signals ts
            LEFT JOIN strategy_catalog sc ON ts.strategy_base = sc.strategy_base
            WHERE ts.signal_type IS NOT NULL
            ORDER BY ts.created_at DESC
            LIMIT 20
            """)
            signals = cur.fetchall()
            
            if signals:
                self._render_signals_summary(signals)
                self._render_signals_details(signals)
            else:
                self._render_no_signals_message()
        
        except Exception as e:
            logger.error(f"Error loading recent signals: {str(e)}")
            st.error(f"Error loading signals: {str(e)}")
            self._render_signals_debug_info()
    
    def _render_signals_summary(self, signals: List[Tuple]) -> None:
        """Render signals summary statistics."""
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Recent Signals", len(signals))
        with col2:
            unique_symbols = len(set([s[0] for s in signals]))
            st.metric("Unique Symbols", unique_symbols)
        with col3:
            unique_bases = len(set([s[2] for s in signals if s[2]]))
            st.metric("Strategy Bases Used", unique_bases)
        with col4:
            avg_magnitude = sum([s[3] for s in signals if s[3]]) / len([s[3] for s in signals if s[3]]) if any(s[3] for s in signals) else 0
            st.metric("Avg Magnitude", f"{avg_magnitude:.1f}")
    
    def _render_signals_details(self, signals: List[Tuple]) -> None:
        """Render detailed signals grouped by symbol."""
        st.markdown("---")
        st.markdown("### Signal Details")
        
        # Group signals by symbol
        signals_by_symbol = defaultdict(list)
        for signal in signals:
            signals_by_symbol[signal[0]].append(signal)
        
        for symbol, symbol_signals in signals_by_symbol.items():
            with st.expander(f"**{symbol}** ({len(symbol_signals)} signals)"):
                for signal in symbol_signals:
                    self._render_signal_detail(signal)
    
    def _render_signal_detail(self, signal: Tuple) -> None:
        """Render individual signal detail."""
        (symbol, signal_type, strategy_base, magnitude, strength, 
         price, volume, rsi, timestamp, strategy_name, category) = signal
        
        col1, col2, col3 = st.columns([3, 2, 2])
        
        with col1:
            # Signal info
            magnitude_color = "🟢" if magnitude and magnitude >= 7 else "🟡" if magnitude and magnitude >= 4 else "🔴"
            st.markdown(f"**{magnitude_color} {signal_type}** - {strategy_name or 'Unknown Strategy'}")
            st.markdown(f"Category: {category or 'Unknown'}")
            st.markdown(f"Time: {str(timestamp)[:16] if timestamp else 'Unknown'}")
        
        with col2:
            # Strategy details
            st.markdown(f"**Strategy Base:** {strategy_base or 'N/A'}")
            st.markdown(f"**Magnitude:** {magnitude or 'N/A'}/9")
            st.markdown(f"**Strength:** {strength or 'N/A'}")
        
        with col3:
            # Market data
            st.markdown(f"**Price:** ${price:.2f}" if price else "Price: N/A")
            st.markdown(f"**Volume:** {volume:,}" if volume else "Volume: N/A")
            st.markdown(f"**RSI:** {rsi:.1f}" if rsi else "RSI: N/A")
        
        st.markdown("---")
    
    def _render_no_signals_message(self) -> None:
        """Render message when no signals are found."""
        st.info("No signals found in trading_signals table.")
        st.markdown("**To generate signals:**")
        st.markdown("1. Run the HK Strategy Engine")
        st.markdown("2. Signals will be stored in trading_signals table")
        st.markdown("3. New TXYZN format signals will appear here")
        
        # Show signal generation button
        if st.button("🎯 Generate Test Signals"):
            st.info("Signal generation feature would be implemented here")
    
    def _render_signals_debug_info(self) -> None:
        """Render debug information for signals."""
        st.markdown("**Debugging Info:**")
        st.markdown("- Check if trading_signals table exists")
        st.markdown("- Verify database connection")
        st.markdown("- Ensure migration was successful")
    
    def _render_configuration_tab(self, conn: Any) -> None:
        """Render system configuration tab."""
        st.markdown("### System Configuration")
        st.markdown("*Configure TXYZN strategy system and monitor database status*")
        
        try:
            cur = conn.cursor()
            
            # Database schema status
            self._render_database_status(cur)
            
            # Strategy base configuration
            self._render_strategy_summary(cur)
            
            # Migration status
            self._render_migration_status(cur)
            
        except Exception as e:
            logger.error(f"Error loading system configuration: {str(e)}")
            st.error(f"Error loading system configuration: {str(e)}")
    
    def _render_database_status(self, cur: Any) -> None:
        """Render database schema status."""
        st.markdown("### Database Schema Status")
        
        # Check key tables
        tables_to_check = [
            ('strategy_catalog', 'Strategy Base Definitions'),
            ('trading_signals', 'Generated Trading Signals'),
            ('portfolio_positions', 'Portfolio Holdings'),
            ('signal_analysis_view', 'Signal Analysis View')
        ]
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Table Status:**")
            self._check_tables_status(cur, tables_to_check)
        
        with col2:
            st.markdown("**TXYZN Format Validation:**")
            self._validate_txyzn_format()
    
    def _check_tables_status(self, cur: Any, tables_to_check: List[Tuple[str, str]]) -> None:
        """Check status of database tables."""
        for table, description in tables_to_check:
            try:
                if table == 'signal_analysis_view':
                    # Check if view exists
                    cur.execute("""
                    SELECT COUNT(*) FROM information_schema.views 
                    WHERE table_name = 'signal_analysis_view'
                    """)
                    exists = cur.fetchone()[0] > 0
                    status = "✅" if exists else "⚠️"
                    st.markdown(f"{status} **{table}**: {'Available' if exists else 'Missing'}")
                else:
                    cur.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cur.fetchone()[0]
                    status = "✅" if count >= 0 else "❌"
                    st.markdown(f"{status} **{table}**: {count} records")
            except Exception as e:
                st.markdown(f"❌ **{table}**: Error ({str(e)[:50]}...)")
    
    def _validate_txyzn_format(self) -> None:
        """Validate TXYZN format patterns."""
        test_signals = ["BBRK5", "SOBR7", "BDIV9", "INVALID", "SMAC6"]
        for test_signal in test_signals:
            # Updated pattern to include H for Hold signals
            is_valid = bool(re.match(r'^[BSH][A-Z]{3}[1-9]$', test_signal))
            status = "✅" if is_valid else "❌"
            st.markdown(f"{status} **{test_signal}**: {'Valid TXYZN' if is_valid else 'Invalid'}")
    
    def _render_strategy_summary(self, cur: Any) -> None:
        """Render strategy base summary."""
        st.markdown("---")
        st.markdown("### Strategy Base Summary")
        
        try:
            cur.execute("""
            SELECT 
                signal_side,
                category,
                COUNT(*) as count,
                string_agg(strategy_base, ', ' ORDER BY strategy_base) as bases
            FROM strategy_catalog 
            GROUP BY signal_side, category 
            ORDER BY signal_side, category
            """)
            catalog_summary = cur.fetchall()
            
            if catalog_summary:
                for side, category, count, bases in catalog_summary:
                    side_name = {"B": "Buy", "S": "Sell", "H": "Hold"}[side]
                    side_color = {"B": "🟢", "S": "🔴", "H": "🟡"}[side]
                    
                    with st.expander(f"{side_color} {side_name} - {category.title()} ({count} strategies)"):
                        st.markdown(f"**Strategy Bases:** {bases}")
                        st.markdown(f"**Category:** {category}")
                        st.markdown(f"**Possible Magnitudes:** 1-9 (each base can generate 9 different signal strengths)")
                        st.markdown(f"**Total Combinations:** {count * 9} possible {side_name.lower()} signals")
            else:
                st.warning("No strategy bases found in catalog")
        
        except Exception as e:
            logger.error(f"Error loading strategy summary: {str(e)}")
            st.error(f"Error loading strategy summary: {str(e)}")
    
    def _render_migration_status(self, cur: Any) -> None:
        """Render migration status information."""
        st.markdown("---")
        st.markdown("### Migration Status")
        
        try:
            # Check if migration was successful
            cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'trading_signals' 
            AND column_name IN ('strategy_base', 'signal_magnitude', 'strategy_category')
            ORDER BY column_name
            """)
            migration_columns = [row[0] for row in cur.fetchall()]
            
            expected_columns = ['signal_magnitude', 'strategy_base', 'strategy_category']
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Migration Columns:**")
                for col in expected_columns:
                    status = "✅" if col in migration_columns else "❌"
                    st.markdown(f"{status} {col}")
            
            with col2:
                # Check constraint status
                st.markdown("**TXYZN Constraints:**")
                cur.execute("""
                SELECT constraint_name 
                FROM information_schema.table_constraints 
                WHERE table_name = 'trading_signals' 
                AND constraint_type = 'CHECK'
                AND constraint_name LIKE '%txyzn%'
                """)
                constraints = cur.fetchall()
                
                if constraints:
                    for constraint in constraints:
                        st.markdown(f"✅ {constraint[0]}")
                else:
                    st.markdown("⚠️ TXYZN constraints not found")
            
            # Overall migration status
            migration_success = len(migration_columns) == len(expected_columns)
            if migration_success:
                st.success("✅ Database migration to TXYZN format completed successfully!")
            else:
                st.warning(f"⚠️ Migration incomplete. Found {len(migration_columns)}/{len(expected_columns)} expected columns.")
        
        except Exception as e:
            logger.error(f"Error checking migration status: {str(e)}")
            st.error(f"Error checking migration status: {str(e)}")
    
    def _render_navigation_buttons(self) -> None:
        """Render navigation buttons."""
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🔙 Back to Strategy Section", type="secondary"):
                self.navigate_to_page('equity_analysis')
                st.rerun()
        with col2:
            if st.button("📊 View Portfolios", type="primary"):
                self.navigate_to_page('overview')
                st.rerun()
        with col3:
            if st.button("🔄 Refresh Data", type="secondary"):
                st.rerun()
    
    def _get_magnitude_info(self) -> Dict[int, Dict[str, str]]:
        """Get magnitude information mapping."""
        return {
            1: {"label": "Experimental", "color": "🔴", "desc": "New/untested signals"},
            2: {"label": "Weak", "color": "🟠", "desc": "Low confidence signals"},  
            3: {"label": "Light", "color": "🟡", "desc": "Cautionary signals"},
            4: {"label": "Moderate-", "color": "🟡", "desc": "Below-average confidence"},
            5: {"label": "Moderate", "color": "🟢", "desc": "Standard trading signal"},
            6: {"label": "Moderate+", "color": "🟢", "desc": "Above-average confidence"},
            7: {"label": "Strong", "color": "🔵", "desc": "High confidence signal"},
            8: {"label": "Very Strong", "color": "🟣", "desc": "Professional grade"},
            9: {"label": "Extreme", "color": "⚫", "desc": "Institutional grade"}
        }