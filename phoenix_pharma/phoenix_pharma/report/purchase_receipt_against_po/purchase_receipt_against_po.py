# Copyright (c) 2025, Navin R C and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
    columns = [
        {
            "label": "Company",
            "fieldname": "company",
            "fieldtype": "Link",
            "options": "Company",
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
            "label": "Purchase Order",
            "fieldname": "purchase_order",
            "fieldtype": "Link",
            "options": "Purchase Order",
            "width": 130,
        },
        {"label": "PO Date", "fieldname": "po_date", "fieldtype": "Date", "width": 100},
        {
            "label": "Purchase Receipt",
            "fieldname": "pr_name",
            "fieldtype": "Link",
            "options": "Purchase Receipt",
            "width": 150,
        },
        {"label": "PR Date", "fieldname": "pr_date", "fieldtype": "Date", "width": 100},
        {
            "label": "Approval State",
            "fieldname": "workflow_state",
            "fieldtype": "Data",
            "width": 120,
        },
        {
            "label": "DocStatus",
            "fieldname": "docstatus",
            "fieldtype": "Data",
            "width": 100,
        },
        {
            "label": "Item Code",
            "fieldname": "item_code",
            "fieldtype": "Data",
            "options": "Item",
            "width": 120,
        },
        {
            "label": "Item Name",
            "fieldname": "item_name",
            "fieldtype": "Data",
            "width": 180,
        },
        {"label": "Qty", "fieldname": "qty", "fieldtype": "Float", "width": 80},
        {
            "label": "Received Qty in PO",
            "fieldname": "received_qty",
            "fieldtype": "Float",
            "width": 120,
        },
        {
            "label": "PO Balance Qty",
            "fieldname": "balance_qty",
            "fieldtype": "Float",
            "width": 120,
        },
    ]

    data = []

    if (
        filters.get("purchase_order")
        or filters.get("company")
        or filters.get("supplier")
    ):
        # Build WHERE conditions
        conditions = []
        values = []

        if filters.get("purchase_order"):
            conditions.append("pri.purchase_order = %s")
            values.append(filters["purchase_order"])

        if filters.get("company"):
            conditions.append("pr.company = %s")
            values.append(filters["company"])

        if filters.get("supplier"):
            conditions.append("pr.supplier = %s")
            values.append(filters["supplier"])

        where_clause = " AND ".join(conditions)

        # Get Purchase Receipts with enhanced data
        data = frappe.db.sql(
            f"""
            SELECT
                pr.company,
                pr.supplier,
                pri.purchase_order,
                po.transaction_date as po_date,
                pr.name as pr_name,
                pr.posting_date as pr_date,
                pr.workflow_state,
                CASE pr.docstatus
                    WHEN 0 THEN 'Draft'
                    WHEN 1 THEN 'Submitted'
                    WHEN 2 THEN 'Cancelled'
                END as docstatus,
                pri.item_code,
                pri.item_name,
                pri.qty,
                poi.received_qty,
                (poi.qty - COALESCE(poi.received_qty, 0)) as balance_qty
            FROM `tabPurchase Receipt` pr
            JOIN `tabPurchase Receipt Item` pri ON pri.parent = pr.name
            LEFT JOIN `tabPurchase Order` po ON po.name = pri.purchase_order
            LEFT JOIN `tabPurchase Order Item` poi
                ON poi.parent = pri.purchase_order
                AND poi.item_code = pri.item_code
            WHERE {where_clause}
            ORDER BY pr.creation DESC, pri.item_code
        """,
            values,
            as_dict=True,
        )

    return columns, data
