#!/usr/bin/env python3
"""
New Modular HK Strategy Dashboard Entry Point.

This is the main entry point for the fully modular dashboard architecture.
Integrates all phases: Core (1) + Services (2) + Navigation (3) + Pages (4) + Components (5).
"""

import sys
import os
import logging

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st

# Configure page first
st.set_page_config(
    page_title="HK Strategy Dashboard",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    """Main application entry point."""
    try:
        # Import core modules
        from src.dashboard import DashboardApp
        from src.navigation import render_sidebar
        from src.pages import render_current_page
        
        # Initialize dashboard app
        app = DashboardApp()
        
        # Initialize application
        if not app.initialize_app():
            st.error("❌ Failed to initialize dashboard")
            st.stop()
        
        # Show header with version info
        if st.session_state.get('debug_mode', False):
            st.markdown("### 🏦 HK Strategy Dashboard (Modular Architecture)")
            with st.expander("🔧 Debug Information", expanded=False):
                st.json({
                    "Architecture": "Modular (Phases 1-4 Complete)",
                    "Phase 1": "✅ Core Modules",
                    "Phase 2": "✅ Services Layer", 
                    "Phase 3": "✅ Navigation System",
                    "Phase 4": "✅ Page Modules",
                    "Phase 5": "🚧 UI Components",
                    "Session State Keys": len(st.session_state),
                    "Current Page": st.session_state.get('current_page', 'unknown'),
                    "Current Section": st.session_state.get('current_section', 'unknown')
                })
            st.markdown("---")
        
        # Render sidebar navigation
        render_sidebar()
        
        # Render current page content
        render_current_page()
        
    except ImportError as e:
        st.error(f"❌ Import Error: {str(e)}")
        st.error("🔧 This likely means the modular architecture is not complete.")
        st.info("💡 Try running the original dashboard: `streamlit run dashboard.py`")
        
        # Show troubleshooting info
        with st.expander("🛠️ Troubleshooting"):
            st.markdown("""
            **Missing Components:**
            
            The modular dashboard requires all phases to be implemented:
            
            - ✅ **Phase 1**: `src/dashboard/` (Core modules)
            - ✅ **Phase 2**: `src/services/` (Services layer) 
            - ✅ **Phase 3**: `src/navigation/` (Navigation system)
            - ✅ **Phase 4**: `src/pages/` (Page modules)
            - 🚧 **Phase 5**: `src/components/` (UI components - optional)
            
            **Quick Fixes:**
            1. Ensure you're in the project root directory
            2. Check that all `src/` subdirectories exist
            3. Verify all `__init__.py` files are present
            4. Try: `python -c "import src.dashboard; import src.pages; print('OK')"`
            """)
        
    except Exception as e:
        st.error(f"❌ Unexpected Error: {str(e)}")
        
        # Show error details in debug mode
        if st.session_state.get('debug_mode', False):
            import traceback
            st.code(traceback.format_exc())
        
        st.error("🔧 Please check the application logs for more details.")


if __name__ == "__main__":
    main()