"""
Test Suite for Phase 5 - UI Components Implementation

Comprehensive tests for component modules:
- Dialog components (BaseDialog, IndicatorsDialog, PortfolioDialogs)
- Chart components (BaseChart and implementations)
- Form components (BaseForm and implementations) 
- Widget components (BaseWidget and implementations)
- Utility modules (data, chart, indicator utilities)
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import components
try:
    from components.dialogs.base_dialog import BaseDialog, dialog_component
    from components.dialogs.indicators_dialog import IndicatorsDialog
    from components.dialogs.portfolio_dialogs import CreatePortfolioDialog, CopyPortfolioDialog
    from components.charts.base_chart import BaseChart, CandlestickChart, LineChart
    from components.forms.base_form import BaseForm, ValidationMixin
    from components.widgets.base_widget import BaseWidget, MetricWidget, SelectorWidget
except ImportError as e:
    pytest.skip(f"Components not available: {e}", allow_module_level=True)


class TestBaseDialog:
    """Test the BaseDialog abstract base class."""
    
    def test_base_dialog_initialization(self):
        """Test BaseDialog initialization."""
        # Create a concrete implementation for testing
        class TestDialog(BaseDialog):
            def render_content(self):
                return {"test": "data"}
        
        dialog = TestDialog("Test Dialog")
        assert dialog.title == "Test Dialog"
        assert dialog.width == "small"
        assert dialog.result is None
    
    def test_dialog_component_decorator(self):
        """Test the dialog_component decorator."""
        @dialog_component("Test Dialog", width="medium")
        class TestDialog(BaseDialog):
            def render_content(self):
                return {"test": "data"}
        
        # Check that decorator attaches streamlit dialog wrapper
        assert hasattr(TestDialog, '_streamlit_dialog')
        assert callable(TestDialog._streamlit_dialog)
    
    def test_dialog_validation(self):
        """Test dialog data validation."""
        class TestDialog(BaseDialog):
            def render_content(self):
                return {"test": "data"}
            
            def validate_data(self, data):
                if not data.get("test"):
                    return False, ["Test field is required"]
                return True, []
        
        dialog = TestDialog("Test Dialog")
        
        # Test valid data
        is_valid, errors = dialog.validate_data({"test": "value"})
        assert is_valid is True
        assert len(errors) == 0
        
        # Test invalid data
        is_valid, errors = dialog.validate_data({"test": ""})
        assert is_valid is False
        assert len(errors) == 1


class TestIndicatorsDialog:
    """Test the IndicatorsDialog component."""
    
    def test_indicators_dialog_initialization(self):
        """Test IndicatorsDialog initialization."""
        dialog = IndicatorsDialog()
        assert dialog.title == "Select Technical Indicators"
        assert dialog.max_selection == 3
        assert len(dialog.available_indicators) > 0
    
    def test_indicators_available(self):
        """Test available indicators list."""
        dialog = IndicatorsDialog()
        
        # Check some expected indicators
        indicator_codes = [code for name, code in dialog.available_indicators]
        assert "rsi_14" in indicator_codes
        assert "macd" in indicator_codes
        assert "sma_20" in indicator_codes
    
    @patch('streamlit.session_state')
    def test_selection_management(self, mock_st):
        """Test indicator selection management."""
        mock_st.get.return_value = []
        
        dialog = IndicatorsDialog()
        current_selection = dialog._get_current_selection()
        assert current_selection == []


class TestPortfolioDialogs:
    """Test portfolio management dialogs."""
    
    def test_create_portfolio_dialog_init(self):
        """Test CreatePortfolioDialog initialization."""
        dialog = CreatePortfolioDialog()
        assert dialog.title == "Create New Portfolio"
    
    def test_copy_portfolio_dialog_init(self):
        """Test CopyPortfolioDialog initialization."""
        dialog = CopyPortfolioDialog("TEST_PORTFOLIO")
        assert dialog.title == "Copy Portfolio"
        assert dialog.source_portfolio_id == "TEST_PORTFOLIO"
    
    def test_portfolio_validation(self):
        """Test portfolio data validation."""
        dialog = CreatePortfolioDialog()
        
        # Test empty data
        error = dialog._validate_portfolio_data("", "")
        assert error == ""
        
        # Test missing name
        error = dialog._validate_portfolio_data("TEST_ID", "")
        assert "required" in error.lower()


class TestBaseChart:
    """Test the BaseChart abstract base class."""
    
    def test_base_chart_initialization(self):
        """Test BaseChart initialization."""
        # Create concrete implementation for testing
        class TestChart(BaseChart):
            def prepare_data(self, data):
                return data
            
            def build_chart(self, data):
                import plotly.graph_objects as go
                return go.Figure()
        
        chart = TestChart(title="Test Chart", height=500)
        assert chart.title == "Test Chart"
        assert chart.height == 500
        assert chart.theme == "plotly"
    
    def test_chart_data_validation(self):
        """Test chart data validation."""
        class TestChart(BaseChart):
            def prepare_data(self, data):
                return data
            
            def build_chart(self, data):
                import plotly.graph_objects as go
                return go.Figure()
        
        chart = TestChart()
        
        # Test None data
        assert chart.validate_data(None) is False
        
        # Test empty DataFrame
        import pandas as pd
        empty_df = pd.DataFrame()
        assert chart.validate_data(empty_df) is False
        
        # Test valid data
        valid_df = pd.DataFrame({"test": [1, 2, 3]})
        assert chart.validate_data(valid_df) is True
    
    def test_candlestick_chart(self):
        """Test CandlestickChart base class."""
        chart = CandlestickChart()
        assert isinstance(chart, BaseChart)
        assert hasattr(chart, 'build_candlestick_trace')
    
    def test_line_chart(self):
        """Test LineChart base class."""
        chart = LineChart()
        assert isinstance(chart, BaseChart)
        assert hasattr(chart, 'build_line_trace')


class TestBaseForm:
    """Test the BaseForm abstract base class."""
    
    def test_base_form_initialization(self):
        """Test BaseForm initialization."""
        # Create concrete implementation for testing
        class TestForm(BaseForm):
            def render_fields(self):
                return {"test_field": "test_value"}
        
        form = TestForm("test_form", title="Test Form")
        assert form.form_key == "test_form"
        assert form.title == "Test Form"
        assert form.submit_label == "Submit"
    
    def test_form_validation(self):
        """Test form validation."""
        class TestForm(BaseForm):
            def render_fields(self):
                return {"test_field": "test_value"}
            
            def validate(self, data):
                if not data.get("test_field"):
                    return False, ["Test field is required"]
                return True, []
        
        form = TestForm("test_form")
        
        # Test valid data
        is_valid, errors = form.validate({"test_field": "value"})
        assert is_valid is True
        assert len(errors) == 0
        
        # Test invalid data
        is_valid, errors = form.validate({"test_field": ""})
        assert is_valid is False
        assert len(errors) == 1


class TestValidationMixin:
    """Test form validation helper methods."""
    
    def test_validate_required(self):
        """Test required field validation."""
        # Test valid values
        assert ValidationMixin.validate_required("value", "Field") is None
        
        # Test invalid values
        assert ValidationMixin.validate_required("", "Field") is not None
        assert ValidationMixin.validate_required(None, "Field") is not None
        assert ValidationMixin.validate_required("   ", "Field") is not None
    
    def test_validate_number(self):
        """Test number validation."""
        # Test valid numbers
        assert ValidationMixin.validate_number("123", "Field") is None
        assert ValidationMixin.validate_number("123.45", "Field") is None
        
        # Test invalid numbers
        assert ValidationMixin.validate_number("abc", "Field") is not None
        
        # Test range validation
        assert ValidationMixin.validate_number("5", "Field", min_val=10) is not None
        assert ValidationMixin.validate_number("15", "Field", max_val=10) is not None
        assert ValidationMixin.validate_number("5", "Field", min_val=1, max_val=10) is None
    
    def test_validate_symbol(self):
        """Test stock symbol validation."""
        # Test valid symbols
        assert ValidationMixin.validate_symbol("AAPL") is None
        assert ValidationMixin.validate_symbol("0005.HK") is None
        
        # Test invalid symbols
        assert ValidationMixin.validate_symbol("") is not None
        assert ValidationMixin.validate_symbol("TOOLONGSYMBOL") is not None
    
    def test_validate_email(self):
        """Test email validation."""
        # Test valid emails
        assert ValidationMixin.validate_email("test@example.com") is None
        assert ValidationMixin.validate_email("") is None  # Optional field
        
        # Test invalid emails
        assert ValidationMixin.validate_email("invalid-email") is not None
        assert ValidationMixin.validate_email("@example.com") is not None


class TestBaseWidget:
    """Test the BaseWidget abstract base class."""
    
    def test_base_widget_initialization(self):
        """Test BaseWidget initialization."""
        # Create concrete implementation for testing
        class TestWidget(BaseWidget):
            def render_content(self):
                return {"test": "data"}
        
        widget = TestWidget("test_widget", title="Test Widget")
        assert widget.widget_id == "test_widget"
        assert widget.title == "Test Widget"
        assert widget.state_key == "widget_test_widget"
    
    @patch('streamlit.session_state')
    def test_widget_state_management(self, mock_st):
        """Test widget state management."""
        mock_st.get.return_value = "test_value"
        mock_st.__setitem__ = Mock()
        mock_st.__contains__ = Mock(return_value=True)
        mock_st.__delitem__ = Mock()
        
        class TestWidget(BaseWidget):
            def render_content(self):
                return {"test": "data"}
        
        widget = TestWidget("test_widget")
        
        # Test state operations
        value = widget.get_state()
        assert value == "test_value"
        
        widget.set_state("new_value")
        mock_st.__setitem__.assert_called()
        
        widget.clear_state()
        mock_st.__delitem__.assert_called()
    
    def test_metric_widget(self):
        """Test MetricWidget base class."""
        widget = MetricWidget("test_metric")
        assert isinstance(widget, BaseWidget)
        assert hasattr(widget, 'render_metric')
    
    def test_selector_widget(self):
        """Test SelectorWidget base class."""
        options = ["option1", "option2", "option3"]
        widget = SelectorWidget("test_selector", options=options, default_option="option1")
        assert isinstance(widget, BaseWidget)
        assert widget.options == options
        assert widget.default_option == "option1"


class TestComponentRegistries:
    """Test component registry systems."""
    
    def test_dialog_registry_exists(self):
        """Test dialog registry exists."""
        from components.dialogs import DIALOG_REGISTRY, get_dialog, create_dialog
        
        assert isinstance(DIALOG_REGISTRY, dict)
        assert callable(get_dialog)
        assert callable(create_dialog)
    
    def test_chart_registry_exists(self):
        """Test chart registry exists."""
        from components.charts import CHART_REGISTRY, get_chart, create_chart
        
        assert isinstance(CHART_REGISTRY, dict)
        assert callable(get_chart)
        assert callable(create_chart)
    
    def test_form_registry_exists(self):
        """Test form registry exists."""
        from components.forms import FORM_REGISTRY, get_form, create_form
        
        assert isinstance(FORM_REGISTRY, dict)
        assert callable(get_form)
        assert callable(create_form)
    
    def test_widget_registry_exists(self):
        """Test widget registry exists."""
        from components.widgets import WIDGET_REGISTRY, get_widget, create_widget
        
        assert isinstance(WIDGET_REGISTRY, dict)
        assert callable(get_widget)
        assert callable(create_widget)


class TestComponentIntegration:
    """Test integration between component types."""
    
    def test_components_package_imports(self):
        """Test that main components package imports work."""
        try:
            from components import BaseDialog, BaseChart, BaseForm, BaseWidget
            
            # Check that all base classes are available
            assert BaseDialog is not None
            assert BaseChart is not None
            assert BaseForm is not None
            assert BaseWidget is not None
        except ImportError:
            pytest.fail("Failed to import base component classes")
    
    def test_component_inheritance(self):
        """Test that specific components inherit from base classes."""
        # Test dialog inheritance
        dialog = IndicatorsDialog()
        assert isinstance(dialog, BaseDialog)
        
        # Test chart inheritance  
        chart = CandlestickChart()
        assert isinstance(chart, BaseChart)
    
    @patch('streamlit')
    def test_streamlit_integration(self, mock_st):
        """Test components integrate with Streamlit."""
        # Mock Streamlit components
        mock_st.markdown = Mock()
        mock_st.button = Mock(return_value=False)
        mock_st.columns = Mock(return_value=[Mock(), Mock()])
        
        # Test that components can render without errors
        dialog = IndicatorsDialog()
        assert dialog is not None
        
        # Note: Full rendering tests require Streamlit context


if __name__ == '__main__':
    # Run tests
    pytest.main([__file__, '-v'])