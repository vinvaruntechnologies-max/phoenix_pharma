# Copyright (c) 2025, Navin R C and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
    if not filters:
        filters = {}

    columns = get_columns()
    data = get_data(filters)

    return columns, data


def get_columns():
    return [
        # PR level
        {
            "label": "Purchase Receipt",
            "fieldname": "purchase_receipt",
            "fieldtype": "Link",
            "options": "Purchase Receipt",
            "width": 160,
        },
        {
            "label": "PR Date",
            "fieldname": "pr_date",
            "fieldtype": "Date",
            "width": 120,
        },
        {
            "label": "Supplier",
            "fieldname": "supplier",
            "fieldtype": "Link",
            "options": "Supplier",
            "width": 150,
        },
        {
            "label": "Receipt Status",
            "fieldname": "receipt_status",
            "fieldtype": "Data",
            "width": 110,
        },
        # PR Item level
        {
            "label": "Item",
            "fieldname": "item_code",
            "fieldtype": "Link",
            "options": "Item",
            "width": 140,
        },
        {
            "label": "Item Name",
            "fieldname": "item_name",
            "fieldtype": "Data",
            "width": 160,
        },
        {
            "label": "Received Qty",
            "fieldname": "received_qty",
            "fieldtype": "Float",
            "width": 90,
        },
        {
            "label": "Received Amount",
            "fieldname": "received_amount",
            "fieldtype": "Currency",
            "width": 110,
        },
        # PI level
        {
            "label": "Purchase Invoice",
            "fieldname": "purchase_invoice",
            "fieldtype": "Link",
            "options": "Purchase Invoice",
            "width": 150,
        },
        {
            "label": "PI Date",
            "fieldname": "pi_date",
            "fieldtype": "Date",
            "width": 100,
        },
        {
            "label": "PI Workflow State",
            "fieldname": "pi_workflow_state",
            "fieldtype": "Data",
            "width": 130,
        },
        {
            "label": "PI Docstatus",
            "fieldname": "pi_docstatus",
            "fieldtype": "Data",
            "width": 90,
        },
        {
            "label": "Invoiced Qty",
            "fieldname": "invoiced_qty",
            "fieldtype": "Float",
            "width": 90,
        },
        {
            "label": "Invoiced Amount",
            "fieldname": "invoiced_amount",
            "fieldtype": "Currency",
            "width": 110,
        },
    ]


def get_data(filters):
    conditions = ["pr.docstatus = 1"]  # only submitted PRs
    params = {}

    # Filters

    if filters.get("purchase_receipt"):
        conditions.append("pr.name = %(purchase_receipt)s")
        params["purchase_receipt"] = filters["purchase_receipt"]

    if filters.get("supplier"):
        conditions.append("pr.supplier = %(supplier)s")
        params["supplier"] = filters["supplier"]

    if filters.get("from_date"):
        conditions.append("pr.posting_date >= %(from_date)s")
        params["from_date"] = filters["from_date"]

    if filters.get("to_date"):
        conditions.append("pr.posting_date <= %(to_date)s")
        params["to_date"] = filters["to_date"]

    # Only rows that have at least one PI
    if filters.get("only_with_pi"):
        conditions.append("pi.name IS NOT NULL")

    # Only rows without any PI yet (pending billing)
    if filters.get("only_without_pi"):
        conditions.append("pi.name IS NULL")

    # if filters.get("pi_workflow_state"):
    #     conditions.append("pi.workflow_state = %(pi_workflow_state)s")
    #     params["pi_workflow_state"] = filters["pi_workflow_state"]

    if filters.get("receipt_status"):
        conditions.append("pr.status = %(receipt_status)s")
        params["receipt_status"] = filters["receipt_status"]

    # include_draft_pi: if unchecked, show only submitted/cancelled PIs
    if not filters.get("include_draft_pi"):
        conditions.append("(pi.docstatus IN (1, 2) OR pi.docstatus IS NULL)")
    else:
        conditions.append("(pi.docstatus IN (0, 1, 2) OR pi.docstatus IS NULL)")

    condition_sql = " AND ".join(conditions)

    data = frappe.db.sql(
        f"""
        SELECT
            pr.name AS purchase_receipt,
            pr.posting_date AS pr_date,
            pr.supplier AS supplier,
            pr.status AS receipt_status,

            pri.name AS pr_item_id,
            pri.item_code AS item_code,
            pri.item_name AS item_name,
            pri.qty AS received_qty,
            pri.amount AS received_amount,

            pi.name AS purchase_invoice,
            pi.posting_date AS pi_date,
            pi.workflow_state AS pi_workflow_state,
            CASE
                WHEN pi.docstatus = 0 THEN 'Draft'
                WHEN pi.docstatus = 1 THEN 'Submitted'
                WHEN pi.docstatus = 2 THEN 'Cancelled'
                ELSE NULL
            END AS pi_docstatus,

            pii.qty AS invoiced_qty,
            pii.amount AS invoiced_amount

        FROM `tabPurchase Receipt Item` pri
        INNER JOIN `tabPurchase Receipt` pr
            ON pri.parent = pr.name

        LEFT JOIN `tabPurchase Invoice Item` pii
            ON pii.pr_detail = pri.name

        LEFT JOIN `tabPurchase Invoice` pi
            ON pi.name = pii.parent

        WHERE {condition_sql}
        ORDER BY
            pr.posting_date DESC,
            pr.name,
            pri.idx,
            pi.posting_date,
            pi.name
        """,
        params,
        as_dict=True,
    )

    return data
