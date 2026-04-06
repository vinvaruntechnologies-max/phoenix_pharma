import frappe


def after_install():
    """
    Runs after `bench install-app phoenix_pharma`.
    Creates custom Stock Entry Types and all custom fields needed by this app.
    """
    create_stock_entry_types()
    create_stock_entry_purity_fields()
    frappe.db.commit()
    print("Phoenix Pharma installed successfully.")


# ---------------------------------------------------------------------------
# Stock Entry Types
# ---------------------------------------------------------------------------

def create_stock_entry_types():
    """Ensure custom Stock Entry Types used by this app exist."""
    custom_types = [
        "Preshipment Batch Creation",
        "Preshipment Batch Deletion",
        "Destruction",
    ]
    for entry_type in custom_types:
        if not frappe.db.exists("Stock Entry Type", entry_type):
            frappe.get_doc(
                {"doctype": "Stock Entry Type", "name": entry_type}
            ).insert(ignore_permissions=True)


# ---------------------------------------------------------------------------
# Custom Fields — API Purity feature
# ---------------------------------------------------------------------------

def create_stock_entry_purity_fields():
    """
    Add custom fields to Stock Entry and Stock Entry Detail (items child table)
    required for the API purity / COA adjustment feature.
    """
    _upsert_custom_fields([
        # ── Stock Entry (parent) ──────────────────────────────────────────
        {
            "dt": "Stock Entry",
            "fieldname": "custom_coa_missing_action",
            "fieldtype": "Select",
            "label": "COA Missing Action",
            "options": "Warn\nBlock",
            "default": "Warn",
            "insert_after": "custom_select_arn_manually",
            "description": "Action when no approved Batch COA is found for an API item",
        },
        {
            "dt": "Stock Entry",
            "fieldname": "custom_excipient_adjustment_mode",
            "fieldtype": "Select",
            "label": "Excipient Adjustment Mode",
            "options": "None\nSingle Excipient\nProportional",
            "default": "None",
            "insert_after": "custom_coa_missing_action",
            "description": "How to compensate batch weight after API qty is adjusted for purity",
        },
        {
            "dt": "Stock Entry",
            "fieldname": "custom_excipient_item",
            "fieldtype": "Link",
            "label": "Excipient Item",
            "options": "Item",
            "insert_after": "custom_excipient_adjustment_mode",
            "depends_on": "eval:doc.custom_excipient_adjustment_mode=='Single Excipient'",
            "description": "Item whose qty will be reduced to absorb the excess API quantity",
        },
        {
            "dt": "Stock Entry",
            "fieldname": "custom_purity_adjustment_log",
            "fieldtype": "Long Text",
            "label": "Purity Adjustment Log",
            "read_only": 1,
            "insert_after": "custom_excipient_item",
            "description": "GMP audit trail — auto-populated on every purity adjustment",
        },

        # ── Stock Entry Detail (items child table) ───────────────────────
        {
            "dt": "Stock Entry Detail",
            "fieldname": "custom_coa_reference",
            "fieldtype": "Link",
            "label": "Batch COA",
            "options": "Batch COA",
            "read_only": 1,
            "insert_after": "batch_no",
            "in_list_view": 0,
        },
        {
            "dt": "Stock Entry Detail",
            "fieldname": "custom_assay_percent",
            "fieldtype": "Float",
            "label": "Assay (%)",
            "read_only": 1,
            "insert_after": "custom_coa_reference",
            "in_list_view": 1,
        },
        {
            "dt": "Stock Entry Detail",
            "fieldname": "custom_lod_percent",
            "fieldtype": "Float",
            "label": "LOD (%)",
            "read_only": 1,
            "insert_after": "custom_assay_percent",
            "in_list_view": 1,
        },
        {
            "dt": "Stock Entry Detail",
            "fieldname": "custom_effective_purity",
            "fieldtype": "Float",
            "label": "Effective Purity (%)",
            "read_only": 1,
            "insert_after": "custom_lod_percent",
            "in_list_view": 1,
            "description": "Assay × (100 − LOD) / 100",
        },
        {
            "dt": "Stock Entry Detail",
            "fieldname": "custom_original_qty",
            "fieldtype": "Float",
            "label": "Original Qty (Before Purity Adj.)",
            "read_only": 1,
            "insert_after": "custom_effective_purity",
        },
        {
            "dt": "Stock Entry Detail",
            "fieldname": "custom_adjusted_qty",
            "fieldtype": "Float",
            "label": "Adjusted Qty (After Purity Adj.)",
            "read_only": 1,
            "insert_after": "custom_original_qty",
            "in_list_view": 1,
        },
    ])


def _upsert_custom_fields(fields: list):
    """Create or update custom fields without duplicating them."""
    for field in fields:
        existing = frappe.db.get_value(
            "Custom Field",
            {"dt": field["dt"], "fieldname": field["fieldname"]},
        )
        if existing:
            cf = frappe.get_doc("Custom Field", existing)
            for k, v in field.items():
                setattr(cf, k, v)
            cf.save(ignore_permissions=True)
        else:
            cf = frappe.get_doc({"doctype": "Custom Field", **field})
            cf.insert(ignore_permissions=True)
