# HK Strategy Dashboard - Core Modules (Phase 1)

## Overview

This directory contains the core modules for the HK Strategy Dashboard decomposition project. Phase 1 focuses on establishing the foundational architecture with proper configuration management, session state handling, and application initialization.

## Phase 1 Implementation Status: ✅ COMPLETED

### Files Created

#### `config.py` - Configuration Management
- **Purpose**: Centralized configuration handling for the entire application
- **Key Features**:
  - Environment variable loading with defaults
  - Database, Redis, caching, and chart configuration
  - Environment validation
  - Logging setup
- **Key Functions**:
  - `get_config()` - Get singleton configuration instance
  - `validate_environment()` - Validate required environment variables
  - `setup_logging()` - Configure application logging

#### `state_manager.py` - Session State Management  
- **Purpose**: Centralized Streamlit session state management
- **Key Features**:
  - Initialize all session state variables with proper defaults
  - Navigation state management
  - Portfolio-specific state handling
  - Price data caching with expiration
  - Modal dialog state management
- **Key Functions**:
  - `SessionStateManager.init_session_state()` - Initialize all states
  - `set_current_page()` - Navigate between pages with cleanup
  - `get_current_portfolio()` - Get selected portfolio data
  - `cache_price_data()` - Cache price data with TTL

#### `main.py` - Main Application Entry Point
- **Purpose**: Application initialization and high-level coordination
- **Key Features**:
  - Streamlit page configuration
  - Error handling and logging
  - Environment validation
  - Database connection verification
- **Key Functions**:
  - `DashboardApp.run()` - Main application entry point
  - `initialize_app()` - Full application initialization
  - `handle_global_error()` - Global error handling

#### `__init__.py` - Module Package
- **Purpose**: Package initialization and public API definition
- **Key Features**:
  - Clean imports for all public functions
  - Phase status tracking
  - Version and metadata management

## Usage

### Running the Dashboard

#### Option 1: New Modular Dashboard (Recommended for Development)
```bash
# Run the new modular dashboard (Phase 1+2 architecture)
streamlit run src/dashboard/main.py

# This provides:
# ✅ Modular architecture with proper separation of concerns
# ✅ Enhanced error handling and logging
# ✅ Configuration management
# ✅ Debug mode and development features
```

#### Option 2: Original Dashboard (Production/Stable)
```bash
# Run the original monolithic dashboard
streamlit run dashboard.py

# This provides:
# ✅ Full feature set (all 6000 lines)
# ✅ Production-tested functionality
# ⚠️ Monolithic architecture (harder to maintain)
```

### Running Tests
```bash
# Test Phase 1 core modules
python test_phase1.py

# Test Phase 2 services (when available)
python test_phase2.py
```

### Using the Modules
```python
from src.dashboard import DashboardApp, get_config, SessionStateManager

# Get configuration
config = get_config()
db_config = config.get('database')

# Initialize session state
SessionStateManager.init_session_state()

# Navigate to different pages
SessionStateManager.set_current_page('portfolio')

# Run the application
app = DashboardApp()
app.run()
```

## Migration Guide

### From Original Dashboard to Modular Architecture

#### Step 1: Environment Setup
Ensure you have all required environment variables set up. Create a `.env` file in your project root:

```bash
# Required Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=hk_strategy
DB_USER=your_db_user
DB_PASSWORD=your_db_password

# Optional Configuration
DEBUG=true                    # Enable debug mode during development
ENVIRONMENT=development       # development, staging, production
REDIS_ENABLED=false          # Enable Redis caching (optional)
CACHE_ENABLED=true           # Enable in-memory caching

# Logging Configuration
LOG_LEVEL=INFO               # DEBUG, INFO, WARNING, ERROR
LOG_FILE_ENABLED=false       # Enable file logging
```

#### Step 2: Install Dependencies
Ensure all required packages are installed:

```bash
pip install streamlit pandas yfinance plotly psycopg2-binary redis python-dotenv
```

#### Step 3: Gradual Migration Process

**Phase 1 (✅ Complete)**: Core modules
- Use `streamlit run src/dashboard/main.py` for development
- Original `dashboard.py` remains fully functional for production

**Phase 2 (✅ Complete)**: Services layer
- All business logic services extracted and modularized
- Data, indicators, portfolio, and analysis services implemented

**Phase 3 (✅ Complete)**: Navigation system  
- Complete navigation architecture with routing and breadcrumbs
- Sidebar navigation and permission system implemented

**Phase 4 (✅ Complete)**: Page modules
- All 9 major pages extracted into modular architecture
- Page manager with routing and lifecycle management

**Phase 5 (🚧 Next)**: UI Components & Dialogs
- Final decomposition of remaining ~1,500 lines
- Reusable component library for dialogs, charts, forms

#### Step 4: Verification
Run tests to ensure everything works:

```bash
# Test core modules
python test_phase1.py

# Compare functionality between versions
streamlit run dashboard.py        # Original
streamlit run src/dashboard/main.py  # New modular version
```

### Migration Benefits

#### Immediate Benefits (Phase 1)
- ✅ **Better Error Handling**: Centralized error management
- ✅ **Configuration Management**: Environment-based configuration
- ✅ **Logging**: Proper application logging
- ✅ **State Management**: Centralized session state handling

#### Future Benefits (Phase 2-5)
- 🚧 **Modularity**: Independent, testable components
- 🚧 **Maintainability**: Single-purpose modules
- 🚧 **Scalability**: Easy to add new features
- 🚧 **Testing**: Comprehensive unit and integration tests

## Configuration

### Environment Variables

The following environment variables are supported:

#### Required
- `DB_HOST` - Database host
- `DB_NAME` - Database name  
- `DB_USER` - Database user

#### Optional
- `DB_PASSWORD` - Database password
- `DB_PORT` - Database port (default: 5432)
- `REDIS_HOST` - Redis host (default: localhost)
- `REDIS_PORT` - Redis port (default: 6379)
- `DEBUG` - Debug mode (default: False)
- `ENVIRONMENT` - Environment name (default: development)

### Configuration Sections

1. **App Configuration**: Page title, layout, debug settings
2. **Database Configuration**: Connection settings, timeouts, SSL
3. **Redis Configuration**: Caching settings, connection details
4. **Chart Configuration**: Default styling, themes, dimensions
5. **Cache Configuration**: TTL settings, cache enablement
6. **Logging Configuration**: Log levels, file logging, formatting

## Architecture Benefits

### 1. **Separation of Concerns**
- Configuration isolated from business logic
- Session state management centralized
- Clear separation between initialization and application logic

### 2. **Maintainability**
- Single source of truth for configuration
- Centralized session state prevents scattered state management
- Clear error handling and logging

### 3. **Testability**
- Each module can be unit tested independently
- Configuration can be mocked for testing
- State management is predictable and testable

### 4. **Scalability**
- Modular structure allows for easy extension
- Configuration system supports multiple environments
- Session state management scales with application complexity

## Migration Notes

### From Original dashboard.py

The following elements have been extracted and modularized:

1. **Configuration** (lines 17-33, 530-534 in original):
   - Environment loading → `config.py`
   - Page configuration → `main.py:setup_page_config()`

2. **Session State** (lines 755-820 in original):
   - All session state initialization → `state_manager.py`
   - Portfolio state management → `SessionStateManager`
   - Navigation state → `get_navigation_state()`

3. **Application Structure** (scattered throughout original):
   - Main entry point → `main.py:DashboardApp.run()`
   - Error handling → `handle_global_error()`
   - Initialization → `initialize_app()`

## Project Progress: 80% Complete! 🎯

**Completed Phases (4/5):**
- ✅ **Phase 1**: Core modules (config, state, main)
- ✅ **Phase 2**: Services layer (data, indicators, portfolio, analysis)  
- ✅ **Phase 3**: Navigation system (router, sidebar, breadcrumbs)
- ✅ **Phase 4**: Page modules (9 pages + manager + architecture)

**Final Phase:**
- 🚧 **Phase 5**: UI Components & Dialogs (~1,500 lines remaining)

2. **Current Directory Structure (80% Complete)**:
   ```
   src/
   ├── dashboard/          # ✅ Phase 1 Complete - Core modules
   ├── services/           # ✅ Phase 2 Complete - Business logic services  
   ├── navigation/         # ✅ Phase 3 Complete - Navigation system
   ├── pages/              # ✅ Phase 4 Complete - Page modules
   └── components/         # 🚧 Phase 5 Next - UI components & dialogs
   ```

## Testing

Run the comprehensive Phase 1 test suite:
```bash
python test_phase1.py
```

The test suite verifies:
- ✅ Directory structure
- ✅ Module imports
- ✅ Configuration management
- ✅ Phase status tracking

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure you're running from the project root directory
2. **Environment Variables**: Check that required database environment variables are set
3. **Database Connection**: Verify database is running and accessible

### Debug Mode

Enable debug mode for additional logging and state information:
```bash
export DEBUG=true
streamlit run src/dashboard/main.py
```

In debug mode, you'll see:
- Environment and version info in the header
- Session state summary in the sidebar
- Detailed configuration information
- Enhanced error messages

## Migration Troubleshooting

### Common Issues and Solutions

#### 1. Import Errors
**Problem**: `ModuleNotFoundError` when running new dashboard
```bash
ModuleNotFoundError: No module named 'src.dashboard'
```
**Solution**: Ensure you're running from the project root directory:
```bash
cd /path/to/hk-strategy-mvp
python -c "import sys; print(sys.path)"  # Verify current directory is in path
streamlit run src/dashboard/main.py
```

#### 2. Environment Variables Not Found
**Problem**: Database connection fails with missing environment variables
**Solution**: Create `.env` file in project root with required variables:
```bash
# Check if .env exists
ls -la .env

# Create if missing
cat > .env << EOF
DB_HOST=localhost
DB_PORT=5432
DB_NAME=hk_strategy
DB_USER=your_username
DB_PASSWORD=your_password
EOF
```

#### 3. Database Connection Issues
**Problem**: `❌ Database connection failed`
**Solution**: 
1. Verify database is running:
   ```bash
   pg_ctl status  # PostgreSQL
   ```
2. Test connection manually:
   ```bash
   psql -h localhost -p 5432 -U your_username -d hk_strategy
   ```
3. Check firewall and network settings

#### 4. Original vs New Dashboard Differences
**Problem**: Missing features in new modular dashboard
**Solution**: During migration (Phase 1-2), use original dashboard for production:
```bash
streamlit run dashboard.py  # Full features
streamlit run src/dashboard/main.py  # Development/testing
```

#### 5. Performance Issues
**Problem**: Slow loading or high memory usage
**Solution**: 
1. Enable Redis caching:
   ```bash
   export REDIS_ENABLED=true
   ```
2. Adjust cache TTL settings:
   ```bash
   export CACHE_PRICE_TTL=1800  # 30 minutes
   ```
3. Monitor debug info in sidebar

#### 6. State Management Issues
**Problem**: Session state not persisting correctly
**Solution**: 
1. Clear browser cache and cookies
2. Use incognito/private browsing mode for testing
3. Check debug info for state summary
4. Restart Streamlit app

### Getting Help

If you encounter issues not covered here:

1. **Check Logs**: Enable debug mode and file logging:
   ```bash
   export DEBUG=true
   export LOG_LEVEL=DEBUG
   export LOG_FILE_ENABLED=true
   ```

2. **Run Tests**: Verify your environment:
   ```bash
   python test_phase1.py
   ```

3. **Compare Versions**: Test against original dashboard:
   ```bash
   streamlit run dashboard.py  # Should work
   streamlit run src/dashboard/main.py  # Test new version
   ```

4. **State Inspection**: Use debug sidebar to inspect session state and configuration