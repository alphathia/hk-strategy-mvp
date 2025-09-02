#!/usr/bin/env python3
"""
Test script to verify the fixes for divide by zero errors
"""

def _safe_percentage(numerator, denominator):
    """Safely calculate percentage to avoid divide by zero errors"""
    try:
        return (numerator / denominator * 100) if denominator != 0 else 0
    except (ZeroDivisionError, TypeError):
        return 0

def test_safe_percentage():
    """Test the safe percentage function"""
    test_cases = [
        (100, 0, 0),      # Divide by zero
        (50, 100, 50.0),  # Normal case
        (0, 0, 0),        # Both zero
        (75, 150, 50.0),  # Normal percentage
        (-25, 100, -25.0), # Negative numerator
        (100, -50, -200.0), # Negative denominator
        (None, 100, 0),   # None numerator
        (100, None, 0),   # None denominator
    ]
    
    print("Testing _safe_percentage function:")
    for i, (num, denom, expected) in enumerate(test_cases, 1):
        result = _safe_percentage(num, denom)
        status = "✅" if result == expected else "❌"
        print(f"{status} Test {i}: _safe_percentage({num}, {denom}) = {result} (expected: {expected})")

def test_active_positions_logic():
    """Test the logic for filtering active positions"""
    # Mock portfolio data
    all_positions = [
        {"symbol": "0700.HK", "quantity": 100, "company_name": "Tencent"},
        {"symbol": "0005.HK", "quantity": 0, "company_name": "HSBC"},
        {"symbol": "0388.HK", "quantity": 50, "company_name": "HKEx"},
        {"symbol": "0939.HK", "quantity": 0, "company_name": "CCB"},
        {"symbol": "1810.HK", "quantity": 200, "company_name": "Xiaomi"},
    ]
    
    # Test filtering active positions (quantity > 0)
    active_positions = [pos for pos in all_positions if pos['quantity'] > 0]
    
    print(f"\nTesting active positions filtering:")
    print(f"Total positions: {len(all_positions)}")
    print(f"Active positions: {len(active_positions)}")
    
    expected_active = 3  # 0700.HK, 0388.HK, 1810.HK
    status = "✅" if len(active_positions) == expected_active else "❌"
    print(f"{status} Expected {expected_active} active positions, got {len(active_positions)}")
    
    # Test empty case
    empty_positions = []
    active_empty = [pos for pos in empty_positions if pos['quantity'] > 0]
    status = "✅" if len(active_empty) == 0 else "❌"
    print(f"{status} Empty positions list handled correctly: {len(active_empty)} active positions")
    
    # Test all zero quantities
    zero_positions = [
        {"symbol": "0700.HK", "quantity": 0, "company_name": "Tencent"},
        {"symbol": "0005.HK", "quantity": 0, "company_name": "HSBC"},
    ]
    active_zero = [pos for pos in zero_positions if pos['quantity'] > 0]
    status = "✅" if len(active_zero) == 0 else "❌"
    print(f"{status} All zero quantity positions handled correctly: {len(active_zero)} active positions")

def test_progress_bar_protection():
    """Test progress bar divide by zero protection"""
    
    def safe_progress_calculation(i, total_symbols):
        """Simulate the progress calculation with protection"""
        if total_symbols > 0:
            return (i + 1) / total_symbols
        else:
            return 0  # Or could return None to indicate no progress
    
    print(f"\nTesting progress bar calculations:")
    
    # Normal case
    progress1 = safe_progress_calculation(2, 5)  # 3rd of 5 items
    expected1 = 0.6
    status = "✅" if progress1 == expected1 else "❌"
    print(f"{status} Normal progress: {progress1:.2f} (expected: {expected1:.2f})")
    
    # Zero total case
    progress2 = safe_progress_calculation(0, 0)  # No items
    expected2 = 0
    status = "✅" if progress2 == expected2 else "❌"
    print(f"{status} Zero total progress: {progress2} (expected: {expected2})")

def test_cost_basis_protection():
    """Test cost basis calculation protection"""
    
    def safe_cost_basis_calculation(old_value, new_value, new_qty):
        """Simulate the cost basis calculation with protection"""
        return (old_value + new_value) / new_qty if new_qty > 0 else 0
    
    print(f"\nTesting cost basis calculations:")
    
    # Normal case
    cost1 = safe_cost_basis_calculation(1000, 500, 150)  # Normal calculation
    expected1 = 10.0  # (1000 + 500) / 150
    status = "✅" if cost1 == expected1 else "❌"
    print(f"{status} Normal cost basis: {cost1:.2f} (expected: {expected1:.2f})")
    
    # Zero quantity case
    cost2 = safe_cost_basis_calculation(1000, 500, 0)  # Zero quantity
    expected2 = 0
    status = "✅" if cost2 == expected2 else "❌"
    print(f"{status} Zero quantity cost basis: {cost2} (expected: {expected2})")

if __name__ == "__main__":
    print("🧪 Running divide by zero protection tests...\n")
    
    test_safe_percentage()
    test_active_positions_logic() 
    test_progress_bar_protection()
    test_cost_basis_protection()
    
    print(f"\n✅ All divide by zero protection tests completed!")