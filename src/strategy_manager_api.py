"""
Strategy Manager API - REST Endpoints for Dashboard CRUD Operations
Comprehensive API for managing strategies, signals, and indicators via dashboard
"""

from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from typing import Dict, List, Any, Optional, Tuple
import json
import logging
from datetime import datetime, date
import traceback
from functools import wraps

from src.strategy_dictionary import StrategyDictionary, StrategyCategory, SignalSide
from src.signal_dictionary import SignalDictionary, SignalType, SignalPriority
from src.indicator_dictionary import IndicatorDictionary, IndicatorCategory
from src.signal_validation import SignalValidationEngine, ValidationResult
from src.strategic_database_manager import StrategicDatabaseManager

logger = logging.getLogger(__name__)

class StrategyManagerAPI:
    """REST API for strategy and signal management"""
    
    def __init__(self, app: Optional[Flask] = None):
        self.app = app or Flask(__name__)
        CORS(self.app)  # Enable CORS for dashboard access
        
        # Initialize components
        self.strategy_dict = StrategyDictionary()
        self.signal_dict = SignalDictionary()
        self.indicator_dict = IndicatorDictionary()
        self.validator = SignalValidationEngine()
        self.db_manager = StrategicDatabaseManager()
        
        # Register routes
        self._register_routes()
        
        # Configure error handling
        self._configure_error_handlers()
    
    def _register_routes(self):
        """Register all API routes"""
        
        # Strategy Management Routes
        self.app.add_url_rule('/api/strategies', 'get_strategies', 
                             self.get_strategies, methods=['GET'])
        self.app.add_url_rule('/api/strategies', 'create_strategy', 
                             self.create_strategy, methods=['POST'])
        self.app.add_url_rule('/api/strategies/<strategy_key>', 'get_strategy', 
                             self.get_strategy, methods=['GET'])
        self.app.add_url_rule('/api/strategies/<strategy_key>', 'update_strategy', 
                             self.update_strategy, methods=['PUT'])
        self.app.add_url_rule('/api/strategies/<strategy_key>', 'delete_strategy', 
                             self.delete_strategy, methods=['DELETE'])
        
        # Strategy Validation Routes
        self.app.add_url_rule('/api/strategies/validate', 'validate_strategy', 
                             self.validate_strategy, methods=['POST'])
        self.app.add_url_rule('/api/strategies/validate/batch', 'validate_strategy_batch', 
                             self.validate_strategy_batch, methods=['POST'])
        
        # Signal Management Routes
        self.app.add_url_rule('/api/signals', 'get_signals', 
                             self.get_signals, methods=['GET'])
        self.app.add_url_rule('/api/signals/types', 'get_signal_types', 
                             self.get_signal_types, methods=['GET'])
        self.app.add_url_rule('/api/signals/validate', 'validate_signal', 
                             self.validate_signal, methods=['POST'])
        
        # Indicator Management Routes
        self.app.add_url_rule('/api/indicators', 'get_indicators', 
                             self.get_indicators, methods=['GET'])
        self.app.add_url_rule('/api/indicators/<indicator_key>', 'get_indicator', 
                             self.get_indicator, methods=['GET'])
        self.app.add_url_rule('/api/indicators/<indicator_key>/config', 'update_indicator_config', 
                             self.update_indicator_config, methods=['PUT'])
        
        # Dashboard Configuration Routes
        self.app.add_url_rule('/api/dashboard/config', 'get_dashboard_config', 
                             self.get_dashboard_config, methods=['GET'])
        self.app.add_url_rule('/api/dashboard/validation-rules', 'get_validation_rules', 
                             self.get_validation_rules, methods=['GET'])
        
        # System Status Routes
        self.app.add_url_rule('/api/system/status', 'get_system_status', 
                             self.get_system_status, methods=['GET'])
        self.app.add_url_rule('/api/system/health', 'health_check', 
                             self.health_check, methods=['GET'])
    
    def _configure_error_handlers(self):
        """Configure error handling for API"""
        
        @self.app.errorhandler(400)
        def bad_request(error):
            return jsonify({
                'error': 'Bad Request',
                'message': str(error),
                'status': 400
            }), 400
        
        @self.app.errorhandler(404)
        def not_found(error):
            return jsonify({
                'error': 'Not Found',
                'message': 'Resource not found',
                'status': 404
            }), 404
        
        @self.app.errorhandler(500)
        def internal_error(error):
            logger.error(f"Internal server error: {error}")
            logger.error(traceback.format_exc())
            return jsonify({
                'error': 'Internal Server Error',
                'message': 'An unexpected error occurred',
                'status': 500
            }), 500
    
    # ==============================================
    # Strategy Management Endpoints
    # ==============================================
    
    def get_strategies(self):
        """GET /api/strategies - Get all strategies with filtering"""
        try:
            # Query parameters
            category = request.args.get('category')
            side = request.args.get('side')
            active_only = request.args.get('active', 'true').lower() == 'true'
            include_metadata = request.args.get('metadata', 'false').lower() == 'true'
            
            # Get strategies from dictionary
            strategies = self.strategy_dict.get_all_strategies()
            
            # Apply filters
            if category:
                try:
                    cat_enum = StrategyCategory(category)
                    strategies = {k: v for k, v in strategies.items() 
                                if v.category == cat_enum}
                except ValueError:
                    return jsonify({'error': f'Invalid category: {category}'}), 400
            
            if side:
                try:
                    side_enum = SignalSide(side)
                    strategies = {k: v for k, v in strategies.items() 
                                if v.side == side_enum}
                except ValueError:
                    return jsonify({'error': f'Invalid side: {side}'}), 400
            
            # Format response
            result = []
            for base_strategy, metadata in strategies.items():
                strategy_info = {
                    'base_strategy': base_strategy,
                    'name': metadata.name_template,
                    'description': metadata.description_template,
                    'side': metadata.side.value,
                    'category': metadata.category.value,
                    'priority': metadata.priority,
                    'supports_provisional': metadata.supports_provisional,
                    'implementation_complexity': metadata.implementation_complexity,
                    'market_conditions': metadata.market_conditions
                }
                
                if include_metadata:
                    strategy_info.update({
                        'required_indicators': metadata.required_indicators,
                        'optional_indicators': metadata.optional_indicators,
                        'default_parameters': metadata.default_parameters,
                        'parameter_ranges': metadata.parameter_ranges,
                        'detailed_explanation': metadata.detailed_explanation,
                        'usage_guidelines': metadata.usage_guidelines,
                        'risk_considerations': metadata.risk_considerations
                    })
                
                result.append(strategy_info)
            
            return jsonify({
                'strategies': result,
                'count': len(result),
                'filters_applied': {
                    'category': category,
                    'side': side,
                    'active_only': active_only
                }
            })
            
        except Exception as e:
            logger.error(f"Error getting strategies: {e}")
            return jsonify({'error': 'Failed to retrieve strategies'}), 500
    
    def create_strategy(self):
        """POST /api/strategies - Create new strategy"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            # Validate strategy definition
            validation_result = self.validator.validate_strategy_definition(data)
            
            if not validation_result.is_valid:
                return jsonify({
                    'error': 'Strategy validation failed',
                    'validation_errors': validation_result.errors,
                    'warnings': validation_result.warnings
                }), 400
            
            # Create strategy in database
            try:
                # Insert base strategy variations (strength 1-9)
                base_strategy = data['base_strategy']
                created_strategies = []
                
                for strength in range(1, 10):
                    strategy_key = f"{base_strategy}{strength}"
                    
                    # Insert into database
                    success = self._create_strategy_in_db(strategy_key, data, strength)
                    
                    if success:
                        created_strategies.append(strategy_key)
                    else:
                        logger.warning(f"Failed to create strategy: {strategy_key}")
                
                return jsonify({
                    'message': 'Strategy created successfully',
                    'base_strategy': base_strategy,
                    'created_strategies': created_strategies,
                    'count': len(created_strategies),
                    'validation_warnings': validation_result.warnings
                }), 201
                
            except Exception as e:
                logger.error(f"Error creating strategy in database: {e}")
                return jsonify({'error': 'Failed to create strategy in database'}), 500
            
        except Exception as e:
            logger.error(f"Error creating strategy: {e}")
            return jsonify({'error': 'Failed to create strategy'}), 500
    
    def get_strategy(self, strategy_key: str):
        """GET /api/strategies/<strategy_key> - Get specific strategy"""
        try:
            # Parse strategy key
            if len(strategy_key) == 5:
                # Full TXYZn format
                parsed = self.validator._parse_signal_key(strategy_key)
                base_strategy = parsed['base_strategy']
            elif len(strategy_key) == 4:
                # Base strategy format
                base_strategy = strategy_key
            else:
                return jsonify({'error': 'Invalid strategy key format'}), 400
            
            # Get strategy metadata
            metadata = self.strategy_dict.get_strategy_metadata(base_strategy)
            if not metadata:
                return jsonify({'error': f'Strategy not found: {base_strategy}'}), 404
            
            # Get database entries for this strategy
            db_strategies = self._get_strategy_from_db(strategy_key)
            
            result = {
                'base_strategy': base_strategy,
                'metadata': {
                    'name_template': metadata.name_template,
                    'description_template': metadata.description_template,
                    'side': metadata.side.value,
                    'category': metadata.category.value,
                    'required_indicators': metadata.required_indicators,
                    'optional_indicators': metadata.optional_indicators,
                    'default_parameters': metadata.default_parameters,
                    'parameter_ranges': metadata.parameter_ranges,
                    'detailed_explanation': metadata.detailed_explanation,
                    'usage_guidelines': metadata.usage_guidelines,
                    'risk_considerations': metadata.risk_considerations,
                    'market_conditions': metadata.market_conditions,
                    'implementation_complexity': metadata.implementation_complexity,
                    'computational_cost': metadata.computational_cost,
                    'color_scheme': metadata.color_scheme,
                    'priority': metadata.priority
                },
                'database_entries': db_strategies,
                'total_variants': len(db_strategies) if db_strategies else 9
            }
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"Error getting strategy {strategy_key}: {e}")
            return jsonify({'error': 'Failed to retrieve strategy'}), 500
    
    def update_strategy(self, strategy_key: str):
        """PUT /api/strategies/<strategy_key> - Update strategy"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            # Validate strategy exists
            base_strategy = strategy_key[:4] if len(strategy_key) >= 4 else strategy_key
            if not self.strategy_dict.get_strategy_metadata(base_strategy):
                return jsonify({'error': f'Strategy not found: {base_strategy}'}), 404
            
            # Update strategy in database
            updated_count = self._update_strategy_in_db(strategy_key, data)
            
            return jsonify({
                'message': 'Strategy updated successfully',
                'strategy_key': strategy_key,
                'updated_variants': updated_count
            })
            
        except Exception as e:
            logger.error(f"Error updating strategy {strategy_key}: {e}")
            return jsonify({'error': 'Failed to update strategy'}), 500
    
    def delete_strategy(self, strategy_key: str):
        """DELETE /api/strategies/<strategy_key> - Delete strategy"""
        try:
            # Parse strategy key
            base_strategy = strategy_key[:4] if len(strategy_key) >= 4 else strategy_key
            
            # Check if strategy exists
            if not self.strategy_dict.get_strategy_metadata(base_strategy):
                return jsonify({'error': f'Strategy not found: {base_strategy}'}), 404
            
            # Delete from database
            deleted_count = self._delete_strategy_from_db(strategy_key)
            
            return jsonify({
                'message': 'Strategy deleted successfully',
                'strategy_key': strategy_key,
                'deleted_variants': deleted_count
            })
            
        except Exception as e:
            logger.error(f"Error deleting strategy {strategy_key}: {e}")
            return jsonify({'error': 'Failed to delete strategy'}), 500
    
    # ==============================================
    # Validation Endpoints
    # ==============================================
    
    def validate_strategy(self):
        """POST /api/strategies/validate - Validate strategy definition"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            validation_result = self.validator.validate_strategy_definition(data)
            
            return jsonify({
                'is_valid': validation_result.is_valid,
                'errors': validation_result.errors,
                'warnings': validation_result.warnings,
                'suggestions': validation_result.suggestions,
                'metadata': validation_result.metadata
            })
            
        except Exception as e:
            logger.error(f"Error validating strategy: {e}")
            return jsonify({'error': 'Validation failed'}), 500
    
    def validate_strategy_batch(self):
        """POST /api/strategies/validate/batch - Validate multiple strategies"""
        try:
            data = request.get_json()
            if not data or 'strategies' not in data:
                return jsonify({'error': 'No strategies provided'}), 400
            
            strategies = data['strategies']
            results = self.validator.validate_strategy_batch(strategies)
            
            # Convert results to JSON-serializable format
            json_results = []
            for i, result in results.items():
                json_results.append({
                    'index': i,
                    'is_valid': result.is_valid,
                    'errors': result.errors,
                    'warnings': result.warnings,
                    'suggestions': result.suggestions
                })
            
            summary = self.validator.get_validation_summary(list(results.values()))
            
            return jsonify({
                'results': json_results,
                'summary': summary
            })
            
        except Exception as e:
            logger.error(f"Error validating strategy batch: {e}")
            return jsonify({'error': 'Batch validation failed'}), 500
    
    def validate_signal(self):
        """POST /api/signals/validate - Validate signal format"""
        try:
            data = request.get_json()
            if not data or 'signal' not in data:
                return jsonify({'error': 'No signal provided'}), 400
            
            signal_value = data['signal']
            context = data.get('context', {})
            
            validation_result = self.validator.validate_strategic_signal(signal_value, context)
            
            return jsonify({
                'is_valid': validation_result.is_valid,
                'errors': validation_result.errors,
                'warnings': validation_result.warnings,
                'suggestions': validation_result.suggestions,
                'parsed': validation_result.metadata
            })
            
        except Exception as e:
            logger.error(f"Error validating signal: {e}")
            return jsonify({'error': 'Signal validation failed'}), 500
    
    # ==============================================
    # Signal Management Endpoints  
    # ==============================================
    
    def get_signals(self):
        """GET /api/signals - Get signal events with filtering"""
        try:
            # Query parameters
            symbol = request.args.get('symbol')
            strategy_key = request.args.get('strategy_key')
            min_strength = int(request.args.get('min_strength', 1))
            limit = int(request.args.get('limit', 100))
            
            # Get signals from database
            signals_df = self.db_manager.get_signal_events(
                symbol=symbol,
                strategy_key=strategy_key,
                min_strength=min_strength,
                limit=limit
            )
            
            if signals_df.empty:
                return jsonify({'signals': [], 'count': 0})
            
            # Convert to JSON format
            signals = []
            for _, row in signals_df.iterrows():
                signals.append({
                    'signal_id': int(row['signal_id']) if 'signal_id' in row else None,
                    'symbol': row['symbol'],
                    'bar_date': row['bar_date'].isoformat() if 'bar_date' in row else None,
                    'strategy_key': row['strategy_key'],
                    'action': row['action'],
                    'strength': int(row['strength']),
                    'close_at_signal': float(row['close_at_signal']) if 'close_at_signal' in row else None,
                    'volume_at_signal': int(row['volume_at_signal']) if 'volume_at_signal' in row else None,
                    'reasons': row['reasons_json'] if 'reasons_json' in row else [],
                    'created_at': row['created_at'].isoformat() if 'created_at' in row else None
                })
            
            return jsonify({
                'signals': signals,
                'count': len(signals),
                'filters': {
                    'symbol': symbol,
                    'strategy_key': strategy_key,
                    'min_strength': min_strength,
                    'limit': limit
                }
            })
            
        except Exception as e:
            logger.error(f"Error getting signals: {e}")
            return jsonify({'error': 'Failed to retrieve signals'}), 500
    
    def get_signal_types(self):
        """GET /api/signals/types - Get all signal type definitions"""
        try:
            signal_definitions = self.signal_dict.get_all_signal_definitions()
            
            result = []
            for signal_id, definition in signal_definitions.items():
                result.append({
                    'signal_id': signal_id,
                    'name': definition.name,
                    'description': definition.description,
                    'signal_type': definition.signal_type.value,
                    'category': definition.category,
                    'format_pattern': definition.format_pattern,
                    'format_example': definition.format_example,
                    'validation_rules': definition.validation_rules,
                    'supports_strength': definition.supports_strength,
                    'supports_provisional': definition.supports_provisional,
                    'is_active': definition.is_active,
                    'color_mapping': definition.color_mapping
                })
            
            return jsonify({
                'signal_types': result,
                'count': len(result)
            })
            
        except Exception as e:
            logger.error(f"Error getting signal types: {e}")
            return jsonify({'error': 'Failed to retrieve signal types'}), 500
    
    # ==============================================
    # Indicator Management Endpoints
    # ==============================================
    
    def get_indicators(self):
        """GET /api/indicators - Get all indicators"""
        try:
            category = request.args.get('category')
            chart_overlay_only = request.args.get('overlay_only', 'false').lower() == 'true'
            
            indicators = self.indicator_dict.INDICATORS
            
            # Apply filters
            if category:
                try:
                    cat_enum = IndicatorCategory(category)
                    indicators = {k: v for k, v in indicators.items() 
                                if v["category"] == cat_enum}
                except ValueError:
                    return jsonify({'error': f'Invalid category: {category}'}), 400
            
            if chart_overlay_only:
                overlay_indicators = self.indicator_dict.get_chart_overlay_indicators()
                indicators = {k: v for k, v in indicators.items() 
                            if k in overlay_indicators}
            
            # Format response
            result = []
            for indicator_key, definition in indicators.items():
                result.append({
                    'indicator_key': indicator_key,
                    'name': definition['name'],
                    'full_name': definition['full_name'],
                    'category': definition['category'].value,
                    'description': definition['description'],
                    'usage': definition['usage'],
                    'is_overlay': indicator_key in self.indicator_dict.get_chart_overlay_indicators(),
                    'is_oscillator': indicator_key in self.indicator_dict.get_oscillator_indicators(),
                    'signal_interpretation': definition.get('signal_interpretation', {})
                })
            
            return jsonify({
                'indicators': result,
                'count': len(result),
                'categories': [cat.value for cat in IndicatorCategory]
            })
            
        except Exception as e:
            logger.error(f"Error getting indicators: {e}")
            return jsonify({'error': 'Failed to retrieve indicators'}), 500
    
    def get_indicator(self, indicator_key: str):
        """GET /api/indicators/<indicator_key> - Get specific indicator"""
        try:
            if indicator_key not in self.indicator_dict.INDICATORS:
                return jsonify({'error': f'Indicator not found: {indicator_key}'}), 404
            
            definition = self.indicator_dict.INDICATORS[indicator_key]
            ui_config = self.indicator_dict.get_ui_display_config(indicator_key)
            
            return jsonify({
                'indicator_key': indicator_key,
                'definition': {
                    'name': definition['name'],
                    'full_name': definition['full_name'],
                    'category': definition['category'].value,
                    'description': definition['description'],
                    'detailed_explanation': definition['detailed_explanation'],
                    'usage': definition['usage'],
                    'signal_interpretation': definition.get('signal_interpretation', {})
                },
                'ui_config': ui_config,
                'is_overlay': indicator_key in self.indicator_dict.get_chart_overlay_indicators(),
                'is_oscillator': indicator_key in self.indicator_dict.get_oscillator_indicators()
            })
            
        except Exception as e:
            logger.error(f"Error getting indicator {indicator_key}: {e}")
            return jsonify({'error': 'Failed to retrieve indicator'}), 500
    
    def update_indicator_config(self, indicator_key: str):
        """PUT /api/indicators/<indicator_key>/config - Update indicator configuration"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No configuration data provided'}), 400
            
            # Validate indicator exists
            if indicator_key not in self.indicator_dict.INDICATORS:
                return jsonify({'error': f'Indicator not found: {indicator_key}'}), 404
            
            # Validate configuration
            validation_result = self.validator.validate_indicator_config(indicator_key, data)
            
            if not validation_result.is_valid:
                return jsonify({
                    'error': 'Configuration validation failed',
                    'validation_errors': validation_result.errors,
                    'warnings': validation_result.warnings
                }), 400
            
            # TODO: Save configuration to database
            # For now, return success with warnings
            return jsonify({
                'message': 'Indicator configuration updated',
                'indicator_key': indicator_key,
                'warnings': validation_result.warnings
            })
            
        except Exception as e:
            logger.error(f"Error updating indicator config {indicator_key}: {e}")
            return jsonify({'error': 'Failed to update indicator configuration'}), 500
    
    # ==============================================
    # Dashboard Configuration Endpoints
    # ==============================================
    
    def get_dashboard_config(self):
        """GET /api/dashboard/config - Get dashboard configuration"""
        try:
            config = {
                'strategy': self.strategy_dict.get_dashboard_config(),
                'signal': self.signal_dict.get_dashboard_config(), 
                'indicator': {
                    'categories': [cat.value for cat in IndicatorCategory],
                    'total_indicators': len(self.indicator_dict.INDICATORS),
                    'overlay_indicators': self.indicator_dict.get_chart_overlay_indicators(),
                    'oscillator_indicators': self.indicator_dict.get_oscillator_indicators(),
                    'volume_indicators': self.indicator_dict.get_volume_indicators()
                },
                'validation': self.validator.get_validation_config_for_dashboard()
            }
            
            return jsonify(config)
            
        except Exception as e:
            logger.error(f"Error getting dashboard config: {e}")
            return jsonify({'error': 'Failed to retrieve dashboard configuration'}), 500
    
    def get_validation_rules(self):
        """GET /api/dashboard/validation-rules - Get validation rules for forms"""
        try:
            rules = self.validator.get_validation_config_for_dashboard()
            
            return jsonify({
                'validation_rules': rules,
                'patterns': {
                    'strategic_signal': r'^[BS][A-Z]{3}[1-9]$',
                    'base_strategy': r'^[BS][A-Z]{3}$',
                    'symbol': r'^[0-9]{4}\.HK$'
                },
                'ranges': {
                    'strength': {'min': 1, 'max': 9},
                    'rsi_overbought': {'min': 60, 'max': 90},
                    'rsi_oversold': {'min': 10, 'max': 40},
                    'volume_threshold': {'min': 0.1, 'max': 10.0}
                }
            })
            
        except Exception as e:
            logger.error(f"Error getting validation rules: {e}")
            return jsonify({'error': 'Failed to retrieve validation rules'}), 500
    
    # ==============================================
    # System Status Endpoints
    # ==============================================
    
    def get_system_status(self):
        """GET /api/system/status - Get system status"""
        try:
            status = {
                'system': 'Strategic Signal Management API',
                'version': '1.0.0',
                'timestamp': datetime.now().isoformat(),
                'components': {
                    'strategy_dictionary': {
                        'total_base_strategies': len(self.strategy_dict.get_all_strategies()),
                        'total_strategy_combinations': len(self.strategy_dict.get_all_strategies()) * 9,
                        'categories': len([cat for cat in StrategyCategory])
                    },
                    'signal_dictionary': {
                        'total_signal_types': len(self.signal_dict.get_all_signal_definitions()),
                        'active_signal_types': len(self.signal_dict.get_active_signals())
                    },
                    'indicator_dictionary': {
                        'total_indicators': len(self.indicator_dict.INDICATORS),
                        'categories': len([cat for cat in IndicatorCategory])
                    },
                    'database': {
                        'connected': self._test_database_connection(),
                        'tables_available': self._check_database_tables()
                    }
                }
            }
            
            return jsonify(status)
            
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return jsonify({'error': 'Failed to retrieve system status'}), 500
    
    def health_check(self):
        """GET /api/system/health - Health check endpoint"""
        try:
            # Quick health checks
            db_healthy = self._test_database_connection()
            
            health_status = {
                'status': 'healthy' if db_healthy else 'unhealthy',
                'timestamp': datetime.now().isoformat(),
                'checks': {
                    'database': 'ok' if db_healthy else 'error',
                    'dictionaries': 'ok',  # Always ok if code loads
                    'validation': 'ok'     # Always ok if code loads
                }
            }
            
            status_code = 200 if db_healthy else 503
            return jsonify(health_status), status_code
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return jsonify({
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }), 503
    
    # ==============================================
    # Helper Methods
    # ==============================================
    
    def _create_strategy_in_db(self, strategy_key: str, data: Dict, strength: int) -> bool:
        """Create strategy in database"""
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    query = """
                    INSERT INTO strategy (strategy_key, base_strategy, side, strength, 
                                        name, description, category, active)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (strategy_key) DO UPDATE SET
                        name = EXCLUDED.name,
                        description = EXCLUDED.description,
                        active = EXCLUDED.active
                    """
                    
                    # Generate strength-specific name and description
                    strength_names = {
                        1: "Weak", 2: "Very Light", 3: "Light",
                        4: "Moderate-", 5: "Moderate", 6: "Moderate+", 
                        7: "Strong", 8: "Very Strong", 9: "Extreme"
                    }
                    
                    name = data['name_template'].format(strength=strength_names[strength])
                    description = data['description_template']
                    
                    cur.execute(query, (
                        strategy_key,
                        data['base_strategy'],
                        data['side'],
                        strength,
                        name,
                        description,
                        data['category'],
                        True
                    ))
                    
                    conn.commit()
                    return True
                    
        except Exception as e:
            logger.error(f"Error creating strategy in DB: {e}")
            return False
    
    def _get_strategy_from_db(self, strategy_key: str) -> Optional[List[Dict]]:
        """Get strategy from database"""
        try:
            with self.db_manager.get_connection() as conn:
                if len(strategy_key) == 4:
                    # Base strategy - get all variants
                    query = """
                    SELECT * FROM strategy 
                    WHERE base_strategy = %s 
                    ORDER BY strength
                    """
                    params = [strategy_key]
                else:
                    # Specific strategy key
                    query = """
                    SELECT * FROM strategy 
                    WHERE strategy_key = %s
                    """
                    params = [strategy_key]
                
                import pandas as pd
                df = pd.read_sql(query, conn, params=params)
                
                if df.empty:
                    return None
                
                return df.to_dict('records')
                
        except Exception as e:
            logger.error(f"Error getting strategy from DB: {e}")
            return None
    
    def _update_strategy_in_db(self, strategy_key: str, data: Dict) -> int:
        """Update strategy in database"""
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    # Update query - simplified for now
                    query = """
                    UPDATE strategy 
                    SET name = %s, description = %s, active = %s
                    WHERE strategy_key = %s OR base_strategy = %s
                    """
                    
                    cur.execute(query, (
                        data.get('name', ''),
                        data.get('description', ''),
                        data.get('active', True),
                        strategy_key,
                        strategy_key[:4] if len(strategy_key) >= 4 else strategy_key
                    ))
                    
                    updated_count = cur.rowcount
                    conn.commit()
                    return updated_count
                    
        except Exception as e:
            logger.error(f"Error updating strategy in DB: {e}")
            return 0
    
    def _delete_strategy_from_db(self, strategy_key: str) -> int:
        """Delete strategy from database"""
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    query = """
                    DELETE FROM strategy 
                    WHERE strategy_key = %s OR base_strategy = %s
                    """
                    
                    cur.execute(query, (strategy_key, strategy_key[:4] if len(strategy_key) >= 4 else strategy_key))
                    
                    deleted_count = cur.rowcount
                    conn.commit()
                    return deleted_count
                    
        except Exception as e:
            logger.error(f"Error deleting strategy from DB: {e}")
            return 0
    
    def _test_database_connection(self) -> bool:
        """Test database connection"""
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    return True
        except Exception:
            return False
    
    def _check_database_tables(self) -> List[str]:
        """Check which required tables exist"""
        required_tables = ['strategy', 'parameter_set', 'signal_run', 
                          'signal_event', 'indicator_snapshot']
        existing_tables = []
        
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    for table in required_tables:
                        cur.execute("""
                            SELECT COUNT(*) FROM information_schema.tables 
                            WHERE table_name = %s
                        """, (table,))
                        
                        if cur.fetchone()[0] > 0:
                            existing_tables.append(table)
        except Exception:
            pass
        
        return existing_tables
    
    def run(self, host='0.0.0.0', port=5000, debug=False):
        """Run the API server"""
        self.app.run(host=host, port=port, debug=debug)

# Example usage
if __name__ == "__main__":
    # Create and run API
    api = StrategyManagerAPI()
    
    print("🚀 Starting Strategy Manager API...")
    print("📊 Dashboard endpoints:")
    print("  GET  /api/strategies - List all strategies")
    print("  POST /api/strategies - Create new strategy")
    print("  GET  /api/signals - List signal events")
    print("  GET  /api/indicators - List all indicators")
    print("  GET  /api/dashboard/config - Dashboard configuration")
    print("  GET  /api/system/health - Health check")
    
    api.run(debug=True)