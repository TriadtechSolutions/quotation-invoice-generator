"""
Formatting utilities for Indian currency, dates, and sanitized strings.
"""
from datetime import datetime


def format_indian_currency(amount: float, include_symbol: bool = True, suffix_dash: bool = False) -> str:
    """
    Format a number in Indian numbering system (Lakhs, Crores).
    Examples:
    - 2500 -> ₹2,500
    - 15000 -> ₹15,000/- (if suffix_dash=True)
    - 150000 -> ₹1,50,000
    """
    if amount is None:
        amount = 0.0

    try:
        val = float(amount)
    except (ValueError, TypeError):
        val = 0.0

    is_negative = val < 0
    val = abs(val)

    # Format integer part and decimal part
    int_part = int(val)
    decimal_part = round(val - int_part, 2)

    s = str(int_part)
    if len(s) <= 3:
        formatted_int = s
    else:
        last3 = s[-3:]
        other = s[:-3]
        res = []
        while len(other) > 2:
            res.append(other[-2:])
            other = other[:-2]
        if other:
            res.append(other)
        res.reverse()
        formatted_int = ",".join(res) + "," + last3

    if decimal_part > 0:
        dec_str = f".{int(round(decimal_part * 100)):02d}"
    else:
        dec_str = ""

    formatted_num = f"{formatted_int}{dec_str}"
    if is_negative:
        formatted_num = f"-{formatted_num}"

    symbol = "₹" if include_symbol else ""
    suffix = "/-" if suffix_dash else ""

    return f"{symbol}{formatted_num}{suffix}"


def format_date_display(date_str: str) -> str:
    """Format ISO date YYYY-MM-DD to DD/MM/YYYY."""
    if not date_str:
        return datetime.now().strftime("%d/%m/%Y")
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%d/%m/%Y")
    except ValueError:
        return date_str


def sanitize_filename(name: str) -> str:
    """Sanitize string for safe filenames (e.g. customer name)."""
    if not name:
        return "Customer"
    # Keep alphanumeric and spaces/hyphens
    clean = "".join(c if c.isalnum() or c in (" ", "-", "_") else "" for c in name)
    return "-".join(clean.split())
