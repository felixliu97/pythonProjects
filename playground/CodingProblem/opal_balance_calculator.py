"""
Opal Card Negative Balance Calculator

Analyzes when your Opal card balance can go negative based on:
- Your travel pattern (Mon-Thu one-way, Friday two-way)
- Daily and weekly fare caps
- Minimum tap-on requirements

The "negative balance sweet spot" occurs when:
  min_tap_on <= balance < single_trip_cost
"""

# === CONFIGURATION ===
ONE_WAY_FARE = 8.28  # Single trip cost
RETURN_TRIP_FARE = ONE_WAY_FARE * 2  # Return trip (2 ways)

# Daily caps
DAILY_CAP_MON_THU = 19.30
DAILY_CAP_FRI_SUN = 9.65

# Weekly cap
WEEKLY_CAP = 50.00

# Minimum balance to tap on
MIN_TAP_ON_PEAK = 4.33
MIN_TAP_ON_OFFPEAK = 3.02

# Since the user always travels at peak hours:
ACTIVE_MIN_TAP_ON = MIN_TAP_ON_PEAK

# Starting balance options
STARTING_BALANCES = [20, 30, 40, 50, 60, 70, 80, 90, 100]


def get_plan_segments(plan_name: str, day: str) -> list[float]:
    """Return trip costs for a specific plan and day."""
    is_monday = day == "Monday"
    is_tuesday = day == "Tuesday"
    is_friday = day == "Friday"
    
    legs_mon_thu = [ONE_WAY_FARE, ONE_WAY_FARE]  # 8.28 + 8.28 = 16.56
    legs_friday = [5.79, 3.86]  # 5.79 + 3.86 = 9.65 (Capped)
    
    if plan_name == "Tuesday Only":
        return legs_mon_thu if is_tuesday else []
    elif plan_name == "Tue + Fri":
        if is_tuesday: return legs_mon_thu
        if is_friday: return legs_friday
        return []
    elif plan_name == "Mon + Tue + Fri":
        if is_monday or is_tuesday: return legs_mon_thu
        if is_friday: return legs_friday
        return []
    return []


def simulate_plan(plan_name: str, starting_balance: float) -> tuple[int, float, str, int, bool]:
    """Simulate a plan and return when it goes negative or gets blocked."""
    balance = starting_balance
    week = 0
    
    while week < 100:  # Safety limit for low frequency plans
        week += 1
        weekly_spent = 0
        
        for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]:
            legs = get_plan_segments(plan_name, day)
            for i, raw_cost in enumerate(legs):
                remaining_to_weekly = max(0, WEEKLY_CAP - weekly_spent)
                actual_cost = min(raw_cost, remaining_to_weekly)
                
                # Check for negative balance opportunity (Must be between 4.33 and cost)
                if ACTIVE_MIN_TAP_ON <= balance < actual_cost:
                    return week, balance - actual_cost, day, i + 1, True
                
                if balance >= ACTIVE_MIN_TAP_ON:
                    balance -= actual_cost
                    weekly_spent += actual_cost
                else:
                    return week, balance, day, i + 1, False
                    
    return week, balance, "N/A", 0, False


def compare_plans():
    """Compare the 3 remaining travel plans."""
    plans = ["Tuesday Only", "Tue + Fri", "Mon + Tue + Fri"]
    
    print("=" * 95)
    print("OPAL CARD PLAN COMPARISON (PEAK TRAVEL - UPDATED)")
    print("=" * 95)
    print(f"Fare Reference: Mon-Thu Leg: $8.28 | Friday Leg 1: $5.79 | Friday Leg 2: $3.86")
    print(f"Cap Reference:  Friday Day: $9.65  | Weekly: $50.00   | Min Tap-on: $4.33")
    
    for plan in plans:
        print(f"\n\nPLAN: {plan}")
        print("-" * 95)
        print(f"{'Starting':>10} | {'Weeks':>6} | {'Final Day':>10} | {'Leg':>4} | {'After Tap-on':>12} | {'Result'}")
        print("-" * 95)
        
        for start in STARTING_BALANCES:
            weeks, final_bal, day, leg, went_neg = simulate_plan(plan, start)
            
            result_str = "WENT NEGATIVE" if went_neg else "BLOCKED (Low Bal)"
            # Handle cases where Friday Leg 2 is naturally low
            if not went_neg and final_bal < ACTIVE_MIN_TAP_ON and final_bal >= 0:
                result_str = "BLOCKED (Low Bal)"
                
            print(f"${start:>9.2f} | {weeks:>6} | {day:>10} | {leg:>4} | ${final_bal:>11.2f} | {result_str}")


def main():
    compare_plans()
    
    print("\n" + "=" * 95)
    print("COMPARISON SUMMARY")
    print("=" * 95)
    print("""
1. Tuesday Only: High trip cost ($8.28) makes it very easy to go negative.
2. Tue + Fri:    A balanced frequency. $40 or $100 starting balances are the "Negative Sweet Spots".
3. Mon + Tue + Fri: Most frequent travel. Reaches the negative/blocked state the fastest.

PRO TIP: If you want the 'deepest' negative balance, aim for a Tuesday Leg 1 or 2 tap-on 
when your balance is exactly $4.33. This will land you at -$3.95.
""")


if __name__ == "__main__":
    main()
