app_name = "phoenix_pharma"
app_title = "Phoenix Pharma"
app_publisher = "Navin R C"
app_description = "ERPNext customizations for Phoenix pharmaceutical manufacturing"
app_email = "navinrc98@gmail.com"
app_license = "MIT"
app_version = "0.1.0"

required_apps = ["frappe/erpnext"]

# ---------------------------------------------------------------------------
# Install / Uninstall
# ---------------------------------------------------------------------------

after_install = "phoenix_pharma.install.after_install"
before_uninstall = "phoenix_pharma.uninstall.before_uninstall"

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

fixtures = [
    {
        "doctype": "Custom Field",
        "filters": [
            [
                "dt",
                "in",
                [
                    "BOM",
                    "BOM Item",
                    "BOM Operation",
                    "Item",
                    "Item Group",
                    "Manufacturer",
                    "Supplier",
                    "Address",
                    "Item Manufacturer",
                    "Purchase Order",
                    "Purchase Order Item",
                    "Purchase Receipt",
                    "Purchase Receipt Item",
                    "Purchase Invoice",
                    "Quality Inspection",
                    "Item Quality Inspection Parameter",
                    "Quality Inspection Reading",
                    "Quality Inspection Parameter",
                    "Quality Inspection Parameter Group",
                    "Control Number",
                    "Sales Order",
                    "Sales Order Item",
                    "Sales Invoice",
                    "Sales Invoice Item",
                    "Work Order",
                    "Work Order Item",
                    "Stock Entry",
                    "Stock Entry Detail",
                    "Delivery Note ",
                    "Pick List",
                    "Delivery Note Item",
                    "Packing Slip Item",
                    "Packing Slip",
                    "Company",
                    "Job Card",
                    "Warehouse",
                    "Material Request",
                    "Workstation",
                    "Production Plan",
                    "Item Price",
                    "Batch",
                ],
            ]
        ],
    },
    {
        "doctype": "Client Script",
        "filters": [
            [
                "dt",
                "in",
                [
                    "BOM",
                    "Item",
                    "Item Manufacturer",
                    "Purchase Order",
                    "Quality Inspection",
                    "Purchase Receipt",
                    "Item Group",
                ],
            ]
        ],
    },
    {
        "doctype": "Property Setter",
        "filters": [
            [
                "doc_type",
                "in",
                [
                    "BOM",
                    "BOM Item",
                    "BOM Operation",
                    "Cost Sheet",
                    "Item",
                    "Item Group Counter",
                    "Item Group",
                    "Manufacturer",
                    "Item Manufacturer",
                    "Purchase Order",
                    "Purchase Order Item",
                    "Address",
                    "Supplier",
                    "Quality Inspection",
                    "Item Quality Inspection Parameter",
                    "Quality Inspection Reading",
                    "Quality Inspection Parameter",
                    "Quality Inspection Parameter Group",
                    "Purchase Invoice",
                    "Purchase Receipt",
                    "Purchase Receipt Item",
                    "Control Number",
                    "Sales Order",
                    "Sales Order Item",
                    "Sales Invoice",
                    "Sales Invoice Item",
                    "Work Order",
                    "Work Order Item",
                    "Stock Entry",
                    "Stock Entry Detail",
                    "Delivery Note ",
                    "Pick List",
                    "Delivery Note Item",
                    "Packing Slip Item",
                    "Packing Slip",
                    "Company",
                    "Job Card",
                    "Warehouse",
                    "Material Request",
                    "Workstation",
                    "Production Plan",
                    "Item Price",
                    "Batch",
                ],
            ]
        ],
    },
    {
        "doctype": "Server Script",
        "filters": [
            ["reference_doctype", "in", ["BOM", "Manufacturer", "Quality Inspection"]]
        ],
    },
    {"doctype": "Label Contains"},
    {"doctype": "Type Of Pack"},
    {"doctype": "Type Of Formulation"},
    {"doctype": "Pack Style"},
    {"doctype": "Port"},
    {"doctype": "Batch COA"},
    {
        "doctype": "Notification",
        "filters": [
            [
                "document_type",
                "in",
                [
                    "Purchase Receipt",
                    "Purchase Invoice",
                    "Purchase Order",
                    "Sales order",
                ],
            ]
        ],
    },
    {
        "doctype": "Workflow",
        "filters": [
            [
                "name",
                "in",
                [
                    "PO Approval V1",
                    "Purchase Receipt Approval V6",
                    "Purchase invoice Approval V3",
                    "SO Approval V1",
                    "Stock Entry V2",
                    "BOM Approval V1",
                ],
            ]
        ],
    },
    {
        "doctype": "Workflow Action Master",
    },
    {
        "doctype": "Print Format",
        "filters": [
            [
                "name",
                "in",
                ["PO Print Format V3", "RM/PM COA V2", "Debit Note V2"],
            ]
        ],
    },
    {
        "doctype": "Workflow State",
    },
    {
        "doctype": "Role",
    },
    {"doctype": "Address Template"},
    {"doctype": "Stock Entry Type"},
]

# ---------------------------------------------------------------------------
# DocType JS (client-side scripts bundled from this app)
# ---------------------------------------------------------------------------

doctype_js = {
    "Sales Order": "phoenix_pharma/client_scripts/sales_order.js",
    "Work Order": "phoenix_pharma/client_scripts/work_order.js",
    "Stock Entry": "phoenix_pharma/client_scripts/stock_entry.js",
    "Delivery Note": "phoenix_pharma/client_scripts/delivery_note.js",
    "Sales Invoice": "phoenix_pharma/client_scripts/sales_invoice.js",
    "BOM": "phoenix_pharma/client_scripts/bom.js",
    "Job Card": "phoenix_pharma/client_scripts/job_card.js",
    "Packing Slip": "phoenix_pharma/client_scripts/packing_slip.js",
    "Production Plan": "phoenix_pharma/client_scripts/production_plan.js",
    "Quality Inspection": "phoenix_pharma/client_scripts/quality_inspection.js",
    "Purchase Receipt": "phoenix_pharma/client_scripts/purchase_receipt.js",
    "Purchase Order": "phoenix_pharma/client_scripts/purchase_order.js",
    "Purchase Invoice": "phoenix_pharma/client_scripts/purchase_invoice.js",
    "Material Request": "phoenix_pharma/client_scripts/material_request.js",
}

# ---------------------------------------------------------------------------
# DocType Class Overrides
# ---------------------------------------------------------------------------

override_doctype_class = {
    "Purchase Receipt": "phoenix_pharma.phoenix_pharma.overrides.purchase_receipt.CustomPurchaseReceipt"
}

# ---------------------------------------------------------------------------
# Document Events
# ---------------------------------------------------------------------------

doc_events = {
    # --- Naming series ---
    "Quality Inspection": {
        "autoname": "phoenix_pharma.phoenix_pharma.custom.naming.set_qi_naming_series",
    },
    "Stock Entry": {
        "autoname": "phoenix_pharma.phoenix_pharma.custom.naming.set_se_naming_series",
        "before_insert": "phoenix_pharma.phoenix_pharma.custom.stock_entry.before_insert",
        "before_validate": "phoenix_pharma.phoenix_pharma.custom.stock_entry.before_validate",
        "on_update": "phoenix_pharma.phoenix_pharma.custom.stock_entry.on_update",
        "on_submit": "phoenix_pharma.phoenix_pharma.custom.stock_entry.on_submit",
        "on_cancel": "phoenix_pharma.phoenix_pharma.custom.stock_entry.on_cancel",
    },
    "Material Request": {
        "autoname": "phoenix_pharma.phoenix_pharma.custom.naming.set_mr_naming_series",
        "before_insert": "phoenix_pharma.phoenix_pharma.custom.material_request.before_insert",
        "on_change": "phoenix_pharma.phoenix_pharma.custom.material_request.on_change",
    },
    "BOM": {
        "autoname": "phoenix_pharma.phoenix_pharma.custom.naming.set_bom_naming_series",
        "before_insert": "phoenix_pharma.phoenix_pharma.custom.bom.before_insert",
        "on_update": "phoenix_pharma.phoenix_pharma.custom.bom.on_update",
    },
    "Work Order": {
        "autoname": "phoenix_pharma.phoenix_pharma.custom.naming.set_wo_naming_series",
        "before_save": "phoenix_pharma.phoenix_pharma.custom.work_order.fetch_fields_from_sales_order_item",
        "before_insert": "phoenix_pharma.phoenix_pharma.custom.work_order.before_insert",
        "on_change": "phoenix_pharma.phoenix_pharma.custom.work_order.on_change",
    },
    "Job Card": {
        "autoname": "phoenix_pharma.phoenix_pharma.custom.naming.set_jc_naming_series",
    },
    "Pick List": {
        "autoname": "phoenix_pharma.phoenix_pharma.custom.naming.set_pl_naming_series",
    },
    "Production Plan": {
        "autoname": "phoenix_pharma.phoenix_pharma.custom.naming.set_pp_naming_series",
        "before_insert": "phoenix_pharma.phoenix_pharma.custom.production_plan.before_insert",
        "on_update": "phoenix_pharma.phoenix_pharma.custom.production_plan.on_update",
    },
    "Sales Order": {
        "before_insert": "phoenix_pharma.phoenix_pharma.custom.sales_order.before_insert",
        "on_update": "phoenix_pharma.phoenix_pharma.custom.sales_order.on_update",
        "on_submit": "phoenix_pharma.phoenix_pharma.custom.sales_order.on_submit",
    },
    "Sales Invoice": {
        "autoname": "phoenix_pharma.phoenix_pharma.custom.naming.set_si_naming_series",
        "before_insert": "phoenix_pharma.phoenix_pharma.custom.sales_invoice.before_insert",
        "on_update": "phoenix_pharma.phoenix_pharma.custom.sales_invoice.on_update",
    },
    "Delivery Note": {
        "autoname": "phoenix_pharma.phoenix_pharma.custom.naming.set_dn_naming_series",
        "before_insert": "phoenix_pharma.phoenix_pharma.custom.delivery_note.before_insert",
        "on_update": "phoenix_pharma.phoenix_pharma.custom.delivery_note.on_update",
    },
    "Packing Slip": {
        "on_submit": "phoenix_pharma.phoenix_pharma.custom.packing_slip.on_submit",
        "on_cancel": "phoenix_pharma.phoenix_pharma.custom.packing_slip.on_cancel",
    },
    "Purchase Receipt": {
        "before_insert": "phoenix_pharma.phoenix_pharma.custom.purchase_receipt.before_insert",
        "on_update": "phoenix_pharma.phoenix_pharma.custom.purchase_receipt.on_update",
    },
}

# ---------------------------------------------------------------------------
# Scheduled Tasks
# ---------------------------------------------------------------------------

scheduler_events = {
    "daily_long": [
        "phoenix_pharma.phoenix_pharma.custom.work_order.notify_returnable_work_orders"
    ],
}
