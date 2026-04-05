import frappe


def after_install():
    """
    Runs after the app is installed via `bench install-app phoenix_pharma`.
    Use this to set up default configurations, seed master data, or run
    one-time migrations that cannot be expressed as fixtures.
    """
    create_stock_entry_types()
    frappe.db.commit()
    print("Phoenix Pharma installed successfully.")


def create_stock_entry_types():
    """Ensure custom Stock Entry Types used by this app exist."""
    custom_types = ["Preshipment Batch Creation", "Preshipment Batch Deletion", "Destruction"]
    for entry_type in custom_types:
        if not frappe.db.exists("Stock Entry Type", entry_type):
            frappe.get_doc({"doctype": "Stock Entry Type", "name": entry_type}).insert(
                ignore_permissions=True
            )
