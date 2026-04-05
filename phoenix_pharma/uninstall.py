import frappe


def before_uninstall():
    """
    Runs before the app is removed via `bench remove-app phoenix_pharma`.
    Clean up any data or configurations that were created during installation
    and are not automatically removed with the app's DocTypes.
    """
    remove_stock_entry_types()
    frappe.db.commit()
    print("Phoenix Pharma uninstalled.")


def remove_stock_entry_types():
    """Remove custom Stock Entry Types added by this app (only if unused)."""
    custom_types = ["Preshipment Batch Creation", "Preshipment Batch Deletion", "Destruction"]
    for entry_type in custom_types:
        if frappe.db.exists("Stock Entry Type", entry_type):
            in_use = frappe.db.exists("Stock Entry", {"stock_entry_type": entry_type})
            if not in_use:
                frappe.delete_doc("Stock Entry Type", entry_type, ignore_permissions=True)
