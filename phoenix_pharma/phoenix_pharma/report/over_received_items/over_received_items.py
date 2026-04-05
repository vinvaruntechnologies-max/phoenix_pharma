# Copyright (c) 2025, Navin R C and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
    columns, data = get_columns(filters=filters), get_datas(filters=filters)
    return columns, data


def get_columns(filters=None):
    return [
        {
            "label": "Company",
            "fieldname": "company",
            "fieldtype": "Link",
            "options": "Company",
            "width": 200,
        },
        {
            "label": "Purchase Order",
            "fieldname": "purchase_order",
            "fieldtype": "Link",
            "options": "Purchase Order",
            "width": 200,
        },
        {
            "label": "PO Date",
            "fieldname": "transaction_date",
            "fieldtype": "Date",
            "width": 120,
        },
        {
            "label": "Supplier",
            "fieldname": "supplier",
            "fieldtype": "Data",
            "width": 150,
        },
        {
            "label": "Item Code",
            "fieldname": "item_code",
            "fieldtype": "Link",
            "options": "Item",
            "width": 250,
        },
        {
            "label": "Item Name",
            "fieldname": "item_name",
            "fieldtype": "Data",
            "width": 250,
        },
        {
            "label": "Ordered Qty",
            "fieldname": "ordered_qty",
            "fieldtype": "Float",
            "width": 120,
        },
        {
            "label": "Received Qty",
            "fieldname": "received_qty",
            "fieldtype": "Float",
            "width": 120,
        },
        {
            "label": "Excess Qty",
            "fieldname": "excess_qty",
            "fieldtype": "Float",
            "width": 120,
        },
        {
            "label": "Control Number",
            "fieldname": "control_number",
            "fieldtype": "Data",
            "width": 200,
        },
        {
            "label": "Quality Inspection",
            "fieldname": "quality_inspection",
            "fieldtype": "Data",
            "width": 200,
        },
        {
            "label": "Purchase Receipt",
            "fieldname": "purchase_receipt",
            "fieldtype": "Link",
            "options": "Purchase Receipt",
            "width": 200,
        },
        {
            "label": "PR Date",
            "fieldname": "posting_date",
            "fieldtype": "Date",
            "width": 120,
        },
    ]


def get_datas(filters=None):
    filters = filters or {}

    conditions = []
    values = {}

    if filters.get("supplier"):
        conditions.append("po.supplier = %(supplier)s")
        values["supplier"] = filters["supplier"]

    if filters.get("item_code"):
        conditions.append("poi.item_code = %(item_code)s")
        values["item_code"] = filters["item_code"]

    if filters.get("po_from_date"):
        conditions.append("po.transaction_date >= %(po_from_date)s")
        values["po_from_date"] = filters["po_from_date"]

    if filters.get("po_to_date"):
        conditions.append("po.transaction_date <= %(po_to_date)s")
        values["po_to_date"] = filters["po_to_date"]

    if filters.get("pr_from_date"):
        conditions.append("pr.posting_date >= %(pr_from_date)s")
        values["pr_from_date"] = filters["pr_from_date"]

    if filters.get("pr_to_date"):
        conditions.append("pr.posting_date <= %(pr_to_date)s")
        values["pr_to_date"] = filters["pr_to_date"]

    if filters.get("company"):
        conditions.append("po.company = %(company)s")
        values["company"] = filters["company"]

    # Ignore returns
    conditions.append("pr.is_return = 0")

    condition_sql = " AND " + " AND ".join(conditions) if conditions else ""

    return frappe.db.sql(
        f"""
        SELECT
            po.company,
            poi.parent AS purchase_order,
            po.transaction_date,
            po.supplier,
            poi.item_code,
            poi.item_name,
            poi.qty AS ordered_qty,
            pri.received_qty AS received_qty,
            (pri.received_qty - poi.qty) AS excess_qty,
            pri.custom_control_number AS control_number,
            pri.quality_inspection AS quality_inspection,
            pri.parent AS purchase_receipt,
            pr.posting_date
        FROM
            `tabPurchase Order` po
        JOIN
            `tabPurchase Order Item` poi ON poi.parent = po.name
        JOIN
            `tabPurchase Receipt Item` pri ON pri.purchase_order = poi.parent AND pri.item_code = poi.item_code
        JOIN
            `tabPurchase Receipt` pr ON pr.name = pri.parent
        WHERE
            po.docstatus IN (0, 1)
            AND pri.docstatus IN (0, 1)
            AND pri.received_qty > poi.qty
            {condition_sql}
        ORDER BY
            po.company, poi.parent, poi.item_code, pri.parent
        """,
        values,
        as_dict=True,
    )
