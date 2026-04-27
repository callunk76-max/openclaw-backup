from trading_signal import get_all_strengths, calculate_powers
strengths = get_all_strengths()
print("Pair Strengths:", strengths)
powers, raw = calculate_powers()
print("Powers:", powers)
