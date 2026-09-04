"""
Calculation utilities for Win Spares Quotation & Invoice Management System.
All monetary calculations are performed server-side for authoritative accuracy.
"""

def calculate_item_amount(qty: float, rate: float) -> float:
    """Calculate total amount for a single item row."""
    if qty is None or rate is None:
        return 0.0
    try:
        q = float(qty)
        r = float(rate)
        if q < 0 or r < 0:
            return 0.0
        return round(q * r, 2)
    except (ValueError, TypeError):
        return 0.0


def calculate_subtotal(items: list) -> float:
    """Calculate total subtotal from a list of item dicts."""
    subtotal = 0.0
    for item in items or []:
        qty = item.get('qty', 0)
        rate = item.get('rate', 0)
        amount = calculate_item_amount(qty, rate)
        # update amount in item dict for consistency
        item['amount'] = amount
        subtotal += amount
    return round(subtotal, 2)


def calculate_tax_amounts(subtotal: float, sgst_rate: float = 9.0, cgst_rate: float = 9.0) -> dict:
    """Calculate SGST and CGST amounts from subtotal."""
    try:
        s_rate = float(sgst_rate) if sgst_rate is not None else 9.0
        c_rate = float(cgst_rate) if cgst_rate is not None else 9.0
    except (ValueError, TypeError):
        s_rate = 9.0
        c_rate = 9.0

    sgst_amount = round((subtotal * s_rate) / 100.0, 2)
    cgst_amount = round((subtotal * c_rate) / 100.0, 2)

    return {
        'sgstRate': s_rate,
        'cgstRate': c_rate,
        'sgstAmount': sgst_amount,
        'cgstAmount': cgst_amount
    }


def calculate_quotation_totals(items: list, sgst_rate: float = 9.0, cgst_rate: float = 9.0) -> dict:
    """
    Calculate complete totals breakdown:
    - Recalculates amount for each item
    - Subtotal
    - SGST & CGST amounts
    - Grand Total
    """
    processed_items = []
    subtotal = 0.0

    for item in items or []:
        qty = float(item.get('qty', 0))
        rate = float(item.get('rate', 0))
        amount = calculate_item_amount(qty, rate)

        # format qty display if whole number
        qty_display = int(qty) if qty.is_integer() else qty

        processed_items.append({
            'item': str(item.get('item', '')).strip(),
            'qty': qty_display,
            'rate': rate,
            'amount': amount,
            'unit': str(item.get('unit', '')).strip() # e.g. "Units"
        })
        subtotal += amount

    subtotal = round(subtotal, 2)
    tax_info = calculate_tax_amounts(subtotal, sgst_rate, cgst_rate)
    grand_total = round(subtotal + tax_info['sgstAmount'] + tax_info['cgstAmount'], 2)

    return {
        'items': processed_items,
        'subtotal': subtotal,
        'tax': tax_info,
        'grandTotal': grand_total
    }
