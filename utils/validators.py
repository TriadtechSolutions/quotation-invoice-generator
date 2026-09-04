"""
Validation functions for Quotation form data and customer details.
"""

def validate_quotation_data(data: dict) -> tuple[bool, list[str]]:
    """
    Validate incoming quotation dictionary.
    Returns (is_valid, list_of_error_messages).
    """
    errors = []
    if not isinstance(data, dict):
        return False, ["Invalid request payload."]

    # Date validation
    date_val = data.get('date', '').strip()
    if not date_val:
        errors.append("Quotation date is required.")

    # Customer validation
    customer = data.get('customer', {})
    if not isinstance(customer, dict):
        errors.append("Customer details are invalid.")
    else:
        cust_name = customer.get('name', '').strip()
        cust_address = customer.get('address', '').strip()
        if not cust_name:
            errors.append("Customer name is required.")
        if not cust_address:
            errors.append("Customer address is required.")

    # Items validation
    items = data.get('items', [])
    if not isinstance(items, list) or len(items) == 0:
        errors.append("Please add at least one quotation item.")
    else:
        for idx, item in enumerate(items, 1):
            item_name = str(item.get('item', '')).strip()
            if not item_name:
                errors.append(f"Item #{idx}: Item name is required.")

            try:
                qty = float(item.get('qty', 0))
                if qty <= 0:
                    errors.append(f"Item #{idx}: Quantity must be greater than 0.")
            except (ValueError, TypeError):
                errors.append(f"Item #{idx}: Invalid quantity value.")

            try:
                rate = float(item.get('rate', 0))
                if rate <= 0:
                    errors.append(f"Item #{idx}: Rate must be greater than 0.")
            except (ValueError, TypeError):
                errors.append(f"Item #{idx}: Invalid rate value.")

    # Scope validation
    scope = data.get('scope', [])
    if not isinstance(scope, list) or len(scope) == 0:
        errors.append("At least one scope item is required.")
    else:
        valid_scope = [str(s).strip() for s in scope if str(s).strip()]
        if not valid_scope:
            errors.append("At least one non-empty scope item is required.")

    # Tax rates validation
    tax = data.get('tax', {})
    if isinstance(tax, dict):
        for tax_field in ['sgstRate', 'cgstRate']:
            try:
                val = float(tax.get(tax_field, 9.0))
                if val < 0 or val > 100:
                    errors.append(f"{tax_field} must be between 0 and 100%.")
            except (ValueError, TypeError):
                errors.append(f"Invalid value for {tax_field}.")

    return len(errors) == 0, errors
