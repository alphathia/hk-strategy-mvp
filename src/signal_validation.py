"""
Signal Validation System - Comprehensive TXYZn Format Compliance
Unified validation for all signal types, strategies, and indicators
"""

from typing import Dict, List, Any, Optional, Tuple, Set, Union
from dataclasses import dataclass
from datetime import datetime, date
import re
import json
import logging

from src.strategy_dictionary import StrategyDictionary, StrategyCategory, SignalSide
from src.signal_dictionary import SignalDictionary, SignalType, SignalPriority
from src.indicator_dictionary import IndicatorDictionary, IndicatorCategory

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Result of validation operation"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]
    metadata: Dict[str, Any]
    
    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0
    
    @property
    def has_warnings(self) -> bool:
        return len(self.warnings) > 0
    
    def add_error(self, message: str):
        self.errors.append(message)
        self.is_valid = False
    
    def add_warning(self, message: str):
        self.warnings.append(message)
    
    def add_suggestion(self, message: str):
        self.suggestions.append(message)

class SignalValidationEngine:
    """
    Comprehensive validation engine for all signal system components
    """
    
    def __init__(self):
        self.strategy_dict = StrategyDictionary()
        self.signal_dict = SignalDictionary()
        self.indicator_dict = IndicatorDictionary()
        
        # Validation rules cache
        self._validation_cache = {}
    
    # ==============================================
    # TXYZn Strategic Signal Validation
    # ==============================================
    
    def validate_strategic_signal(self, signal_key: str, context: Optional[Dict] = None) -> ValidationResult:
        """Comprehensive validation of TXYZn strategic signal"""
        result = ValidationResult(
            is_valid=True,
            errors=[],
            warnings=[],
            suggestions=[],
            metadata={"signal_key": signal_key, "validation_type": "strategic_signal"}
        )
        
        context = context or {}
        
        # Basic format validation
        if not self._validate_basic_format(signal_key, result):
            return result
        
        # Parse signal components
        parsed = self._parse_signal_key(signal_key)
        result.metadata.update(parsed)
        
        # Validate base strategy exists
        if not self._validate_base_strategy(parsed["base_strategy"], result):
            return result
        
        # Validate side consistency
        if not self._validate_side_consistency(parsed, result):
            return result
        
        # Validate strength level
        if not self._validate_strength_level(parsed["strength"], result):
            return result
        
        # Advanced contextual validation
        self._validate_strategy_context(parsed, context, result)
        
        # Generate suggestions
        self._generate_strategic_suggestions(parsed, result)
        
        return result
    
    def _validate_basic_format(self, signal_key: str, result: ValidationResult) -> bool:
        """Validate basic TXYZn format"""
        if not isinstance(signal_key, str):
            result.add_error("Signal key must be a string")
            return False
        
        if len(signal_key) != 5:
            result.add_error(f"Signal key must be exactly 5 characters, got {len(signal_key)}")
            return False
        
        pattern = r'^[BS][A-Z]{3}[1-9]$'
        if not re.match(pattern, signal_key):
            result.add_error(f"Signal key '{signal_key}' does not match TXYZn pattern")
            result.add_suggestion("Format should be: [B/S][XXX][1-9] (e.g., BBRK7)")
            return False
        
        return True
    
    def _parse_signal_key(self, signal_key: str) -> Dict[str, Any]:
        """Parse TXYZn signal into components"""
        return {
            "side": signal_key[0],
            "base_strategy": signal_key[:4],
            "strategy_code": signal_key[1:4],
            "strength": int(signal_key[4]),
            "is_buy": signal_key[0] == "B",
            "is_sell": signal_key[0] == "S"
        }
    
    def _validate_base_strategy(self, base_strategy: str, result: ValidationResult) -> bool:
        """Validate base strategy exists in dictionary"""
        if not self.strategy_dict.get_strategy_metadata(base_strategy):
            result.add_error(f"Unknown base strategy: {base_strategy}")
            
            # Suggest similar strategies
            all_strategies = list(self.strategy_dict.get_all_strategies().keys())
            similar = self._find_similar_strings(base_strategy, all_strategies)
            if similar:
                result.add_suggestion(f"Did you mean: {', '.join(similar[:3])}")
            
            return False
        
        return True
    
    def _validate_side_consistency(self, parsed: Dict, result: ValidationResult) -> bool:
        """Validate signal side matches strategy definition"""
        strategy_metadata = self.strategy_dict.get_strategy_metadata(parsed["base_strategy"])
        if not strategy_metadata:
            return False
        
        expected_side = strategy_metadata.side.value
        actual_side = parsed["side"]
        
        if actual_side != expected_side:
            result.add_error(
                f"Side mismatch: '{parsed['base_strategy']}' expects '{expected_side}', got '{actual_side}'"
            )
            correct_signal = f"{expected_side}{parsed['base_strategy'][1:]}{parsed['strength']}"
            result.add_suggestion(f"Correct format: {correct_signal}")
            return False
        
        return True
    
    def _validate_strength_level(self, strength: int, result: ValidationResult) -> bool:
        """Validate strength level is in valid range"""
        if not (1 <= strength <= 9):
            result.add_error(f"Strength level must be 1-9, got {strength}")
            return False
        
        # Add contextual warnings for strength levels
        if strength <= 3:
            result.add_warning("Low strength signal (1-3) - use with caution")
        elif strength >= 8:
            result.add_warning("Very high strength signal (8-9) - rare occurrence")
        
        return True
    
    def _validate_strategy_context(self, parsed: Dict, context: Dict, result: ValidationResult):
        """Validate strategy in context of market conditions and parameters"""
        strategy_metadata = self.strategy_dict.get_strategy_metadata(parsed["base_strategy"])
        if not strategy_metadata:
            return
        
        # Market condition validation
        if "market_condition" in context:
            market_condition = context["market_condition"]
            if market_condition not in strategy_metadata.market_conditions:
                result.add_warning(
                    f"Strategy {parsed['base_strategy']} not optimal for {market_condition} markets"
                )
                suitable_conditions = ", ".join(strategy_metadata.market_conditions)
                result.add_suggestion(f"Better suited for: {suitable_conditions}")
        
        # Required indicators validation
        if "available_indicators" in context:
            available = set(context["available_indicators"])
            required = set(strategy_metadata.required_indicators)
            missing = required - available
            
            if missing:
                result.add_error(f"Missing required indicators: {', '.join(missing)}")
            
            # Check optional indicators
            optional = set(strategy_metadata.optional_indicators)
            available_optional = optional & available
            if available_optional:
                result.add_suggestion(f"Consider using optional indicators: {', '.join(available_optional)}")
        
        # Parameter validation
        if "parameters" in context:
            param_errors = self.strategy_dict.validate_strategy_parameters(
                parsed["base_strategy"], context["parameters"]
            )
            for error in param_errors:
                result.add_error(f"Parameter error: {error}")
    
    def _generate_strategic_suggestions(self, parsed: Dict, result: ValidationResult):
        """Generate helpful suggestions for strategic signals"""
        strategy_metadata = self.strategy_dict.get_strategy_metadata(parsed["base_strategy"])
        if not strategy_metadata:
            return
        
        # Strength-based suggestions
        strength = parsed["strength"]
        if strength >= 7:
            result.add_suggestion("High strength signal - consider larger position size")
        elif strength <= 3:
            result.add_suggestion("Low strength signal - consider smaller position size")
        
        # Category-based suggestions
        category = strategy_metadata.category
        if category == StrategyCategory.BREAKOUT:
            result.add_suggestion("Breakout signal - confirm with volume and follow-through")
        elif category == StrategyCategory.MEAN_REVERSION:
            result.add_suggestion("Mean reversion signal - watch for support/resistance levels")
        elif category == StrategyCategory.DIVERGENCE:
            result.add_suggestion("Divergence signal - requires patience and confirmation")
    
    # ==============================================
    # Strategy Definition Validation
    # ==============================================
    
    def validate_strategy_definition(self, strategy_data: Dict[str, Any]) -> ValidationResult:
        """Validate new strategy definition for dashboard creation"""
        result = ValidationResult(
            is_valid=True,
            errors=[],
            warnings=[],
            suggestions=[],
            metadata={"validation_type": "strategy_definition"}
        )
        
        # Required fields validation
        required_fields = [
            "base_strategy", "side", "name_template", "description_template",
            "category", "required_indicators", "default_parameters"
        ]
        
        for field in required_fields:
            if field not in strategy_data:
                result.add_error(f"Missing required field: {field}")
        
        if result.has_errors:
            return result
        
        # Base strategy format validation
        base_strategy = strategy_data["base_strategy"]
        if not re.match(r'^[BS][A-Z]{3}$', base_strategy):
            result.add_error("Base strategy must follow [B/S][XXX] pattern (e.g., BBRK)")
        
        # Side validation
        side = strategy_data["side"]
        if isinstance(side, str):
            if side not in ["B", "S"]:
                result.add_error("Side must be 'B' (Buy) or 'S' (Sell)")
        
        # Category validation
        category = strategy_data["category"]
        if isinstance(category, str):
            valid_categories = [cat.value for cat in StrategyCategory]
            if category not in valid_categories:
                result.add_error(f"Invalid category. Must be one of: {', '.join(valid_categories)}")
        
        # Indicator validation
        required_indicators = strategy_data["required_indicators"]
        if isinstance(required_indicators, list):
            valid_indicators = list(self.indicator_dict.INDICATORS.keys())
            invalid_indicators = [ind for ind in required_indicators if ind not in valid_indicators]
            if invalid_indicators:
                result.add_error(f"Invalid indicators: {', '.join(invalid_indicators)}")
        
        # Parameter validation
        self._validate_strategy_parameters(strategy_data.get("default_parameters", {}), result)
        
        return result
    
    def _validate_strategy_parameters(self, parameters: Dict, result: ValidationResult):
        """Validate strategy parameters"""
        if not isinstance(parameters, dict):
            result.add_error("default_parameters must be a dictionary")
            return
        
        # Common parameter validation
        common_params = {
            "volume_threshold": (0.1, 10.0),
            "rsi_overbought": (60, 90),
            "rsi_oversold": (10, 40),
            "breakout_epsilon": (0.001, 0.1),
            "atr_multiplier": (0.5, 5.0)
        }
        
        for param, (min_val, max_val) in common_params.items():
            if param in parameters:
                value = parameters[param]
                if not isinstance(value, (int, float)):
                    result.add_error(f"Parameter '{param}' must be numeric")
                elif not (min_val <= value <= max_val):
                    result.add_error(f"Parameter '{param}' must be between {min_val} and {max_val}")
    
    # ==============================================
    # Signal Event Validation
    # ==============================================
    
    def validate_signal_event(self, signal_data: Dict[str, Any]) -> ValidationResult:
        """Validate signal event data before database insertion"""
        result = ValidationResult(
            is_valid=True,
            errors=[],
            warnings=[],
            suggestions=[],
            metadata={"validation_type": "signal_event"}
        )
        
        # Required fields
        required_fields = [
            "symbol", "bar_date", "strategy_key", "action", "strength",
            "close_at_signal", "thresholds_json", "reasons_json"
        ]
        
        for field in required_fields:
            if field not in signal_data:
                result.add_error(f"Missing required field: {field}")
        
        if result.has_errors:
            return result
        
        # Validate strategy key
        strategy_validation = self.validate_strategic_signal(signal_data["strategy_key"])
        if not strategy_validation.is_valid:
            result.errors.extend(strategy_validation.errors)
        
        # Validate action consistency
        parsed = self._parse_signal_key(signal_data["strategy_key"])
        if signal_data["action"] != parsed["side"]:
            result.add_error("Action field must match strategy key side")
        
        # Validate strength consistency
        if signal_data["strength"] != parsed["strength"]:
            result.add_error("Strength field must match strategy key strength")
        
        # Validate price data
        if not isinstance(signal_data["close_at_signal"], (int, float)):
            result.add_error("close_at_signal must be numeric")
        elif signal_data["close_at_signal"] <= 0:
            result.add_error("close_at_signal must be positive")
        
        # Validate JSON fields
        self._validate_json_field(signal_data, "thresholds_json", result)
        self._validate_json_field(signal_data, "reasons_json", result)
        
        return result
    
    def _validate_json_field(self, data: Dict, field: str, result: ValidationResult):
        """Validate JSON field is properly formatted"""
        if field not in data:
            return
        
        value = data[field]
        
        # Check if it's already a dict/list or needs parsing
        if isinstance(value, str):
            try:
                json.loads(value)
            except json.JSONDecodeError as e:
                result.add_error(f"Invalid JSON in {field}: {e}")
        elif not isinstance(value, (dict, list)):
            result.add_error(f"Field {field} must be JSON-serializable")
    
    # ==============================================
    # Indicator Configuration Validation
    # ==============================================
    
    def validate_indicator_config(self, indicator_key: str, config: Dict[str, Any]) -> ValidationResult:
        """Validate indicator configuration"""
        result = ValidationResult(
            is_valid=True,
            errors=[],
            warnings=[],
            suggestions=[],
            metadata={"indicator_key": indicator_key, "validation_type": "indicator_config"}
        )
        
        # Check if indicator exists
        if indicator_key not in self.indicator_dict.INDICATORS:
            result.add_error(f"Unknown indicator: {indicator_key}")
            similar = self._find_similar_strings(
                indicator_key, list(self.indicator_dict.INDICATORS.keys())
            )
            if similar:
                result.add_suggestion(f"Did you mean: {', '.join(similar[:3])}")
            return result
        
        indicator_def = self.indicator_dict.INDICATORS[indicator_key]
        
        # Validate overbought/oversold levels for oscillators
        if "overbought_level" in indicator_def:
            if "overbought_threshold" in config:
                threshold = config["overbought_threshold"]
                if not (50 <= threshold <= 100):
                    result.add_error("Overbought threshold must be between 50 and 100")
        
        if "oversold_level" in indicator_def:
            if "oversold_threshold" in config:
                threshold = config["oversold_threshold"]
                if not (0 <= threshold <= 50):
                    result.add_error("Oversold threshold must be between 0 and 50")
        
        # Validate period parameters
        if "period" in config:
            period = config["period"]
            if not isinstance(period, int) or period < 1:
                result.add_error("Period must be a positive integer")
            elif period < 5:
                result.add_warning("Very short periods may produce noisy signals")
            elif period > 50:
                result.add_warning("Long periods may produce lagging signals")
        
        return result
    
    # ==============================================
    # Batch Validation
    # ==============================================
    
    def validate_signal_batch(self, signals: List[str]) -> Dict[str, ValidationResult]:
        """Validate a batch of signals"""
        results = {}
        
        for signal in signals:
            results[signal] = self.validate_strategic_signal(signal)
        
        return results
    
    def validate_strategy_batch(self, strategies: List[Dict]) -> Dict[int, ValidationResult]:
        """Validate a batch of strategy definitions"""
        results = {}
        
        for i, strategy in enumerate(strategies):
            results[i] = self.validate_strategy_definition(strategy)
        
        return results
    
    # ==============================================
    # Utility Methods
    # ==============================================
    
    def _find_similar_strings(self, target: str, candidates: List[str], max_results: int = 5) -> List[str]:
        """Find similar strings for suggestions"""
        from difflib import SequenceMatcher
        
        similarities = []
        for candidate in candidates:
            similarity = SequenceMatcher(None, target.upper(), candidate.upper()).ratio()
            similarities.append((candidate, similarity))
        
        # Sort by similarity and return top matches
        similarities.sort(key=lambda x: x[1], reverse=True)
        return [candidate for candidate, similarity in similarities[:max_results] if similarity > 0.3]
    
    def get_validation_summary(self, results: List[ValidationResult]) -> Dict[str, Any]:
        """Get summary statistics for validation results"""
        total = len(results)
        valid = sum(1 for r in results if r.is_valid)
        errors = sum(len(r.errors) for r in results)
        warnings = sum(len(r.warnings) for r in results)
        
        return {
            "total_validated": total,
            "valid_count": valid,
            "invalid_count": total - valid,
            "total_errors": errors,
            "total_warnings": warnings,
            "success_rate": valid / total if total > 0 else 0.0,
            "common_errors": self._get_common_errors(results)
        }
    
    def _get_common_errors(self, results: List[ValidationResult]) -> List[Tuple[str, int]]:
        """Get most common validation errors"""
        error_counts = {}
        
        for result in results:
            for error in result.errors:
                # Normalize error message for counting
                normalized = re.sub(r'\'[^\']*\'', "'...'", error)  # Replace quoted strings
                normalized = re.sub(r'\d+', '#', normalized)        # Replace numbers
                error_counts[normalized] = error_counts.get(normalized, 0) + 1
        
        # Return top 5 most common errors
        return sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    # ==============================================
    # Dashboard Integration
    # ==============================================
    
    def get_validation_config_for_dashboard(self) -> Dict[str, Any]:
        """Get validation configuration for dashboard forms"""
        return {
            "strategic_signal": {
                "pattern": r'^[BS][A-Z]{3}[1-9]$',
                "example": "BBRK7",
                "length": 5,
                "sides": ["B", "S"],
                "strength_range": [1, 9]
            },
            "base_strategies": list(self.strategy_dict.get_all_strategies().keys()),
            "strategy_categories": [cat.value for cat in StrategyCategory],
            "signal_types": [st.value for st in SignalType],
            "indicators": list(self.indicator_dict.INDICATORS.keys()),
            "indicator_categories": [cat.value for cat in IndicatorCategory],
            "validation_rules": {
                "base_strategy_pattern": r'^[BS][A-Z]{3}$',
                "signal_key_pattern": r'^[BS][A-Z]{3}[1-9]$',
                "strength_min": 1,
                "strength_max": 9,
                "required_fields": {
                    "strategy": ["base_strategy", "side", "name_template", "category"],
                    "signal_event": ["symbol", "strategy_key", "action", "strength"]
                }
            }
        }

# Example usage and testing
if __name__ == "__main__":
    # Test the validation engine
    validator = SignalValidationEngine()
    
    # Test strategic signal validation
    test_signals = ["BBRK7", "SOBR3", "INVALID", "BBRK0", "SBRK7"]  # Mix of valid/invalid
    
    for signal in test_signals:
        result = validator.validate_strategic_signal(signal)
        print(f"\n{signal}:")
        print(f"  Valid: {result.is_valid}")
        if result.errors:
            print(f"  Errors: {result.errors}")
        if result.warnings:
            print(f"  Warnings: {result.warnings}")
        if result.suggestions:
            print(f"  Suggestions: {result.suggestions}")
    
    # Test batch validation
    batch_results = validator.validate_signal_batch(test_signals)
    summary = validator.get_validation_summary(list(batch_results.values()))
    print(f"\nBatch Summary: {summary}")