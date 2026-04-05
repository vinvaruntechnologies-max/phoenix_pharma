# Copyright (c) 2025, Navin R C and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
    filters = filters or {}
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {
            "label": _("Company"),
            "fieldname": "company",
            "fieldtype": "Link",
            "options": "Company",
            "width": 120,
        },
        {
            "label": _("Item Code"),
            "fieldname": "item_code",
            "fieldtype": "Link",
            "options": "Item",
            "width": 130,
        },
        {
            "label": _("Item Name"),
            "fieldname": "item_name",
            "fieldtype": "Data",
            "width": 170,
        },
        {
            "label": _("Control Number"),
            "fieldname": "control_number",
            "fieldtype": "Data",
            "width": 180,
        },
        {
            "label": _("ARN No"),
            "fieldname": "arn_number",
            "fieldtype": "Data",
            "width": 180,
        },
        {
            "label": _("Batch"),
            "fieldname": "batch",
            "fieldtype": "Link",
            "options": "Batch",
            "width": 110,
        },
        {
            "label": _("In Qty"),
            "fieldname": "in_qty",
            "fieldtype": "Float",
            "width": 80,
        },
        {
            "label": _("Out Qty"),
            "fieldname": "out_qty",
            "fieldtype": "Float",
            "width": 80,
        },
        {
            "label": _("Rejected Qty"),
            "fieldname": "rejected_qty",
            "fieldtype": "Float",
            "width": 90,
        },
        {
            "label": _("Balance Qty"),
            "fieldname": "balance_qty",
            "fieldtype": "Float",
            "width": 90,
        },
        {
            "label": _("Reference Doctype"),
            "fieldname": "reference_doctype",
            "fieldtype": "Data",
            "width": 120,
        },
        {
            "label": _("Reference Name"),
            "fieldname": "reference_name",
            "fieldtype": "Data",
            "width": 130,
        },
        {
            "label": _("Purpose"),
            "fieldname": "purpose",
            "fieldtype": "Data",
            "width": 130,
        },
        {
            "label": _("Posting Date"),
            "fieldname": "posting_date",
            "fieldtype": "Date",
            "width": 110,
        },
        {
            "label": _("Posting Time"),
            "fieldname": "posting_time",
            "fieldtype": "Time",
            "width": 110,
        },
        {
            "label": _("Created Date"),
            "fieldname": "activity_created_date",
            "fieldtype": "Date",
            "width": 110,
        },
        {
            "label": _("Created Time"),
            "fieldname": "activity_created_time",
            "fieldtype": "Time",
            "width": 110,
        },
        {
            "label": _("Created By"),
            "fieldname": "activity_created_by",
            "fieldtype": "Data",
            "width": 120,
        },
    ]


def get_data(filters):
    conditions = []
    values = {}

    for field in ["company", "item_code", "name", "batch"]:
        if filters.get(field):
            if field == "name":
                conditions.append("cn.name = %(control_number)s")
                values["control_number"] = filters["name"]
            else:
                conditions.append(f"cn.{field} = %({field})s")
                values[field] = filters[field]

    if filters.get("from_date"):
        conditions.append("cna.posting_date >= %(from_date)s")
        values["from_date"] = filters["from_date"]

    if filters.get("to_date"):
        conditions.append("cna.posting_date <= %(to_date)s")
        values["to_date"] = filters["to_date"]

    condition_str = " AND ".join(conditions) if conditions else "1=1"

    return frappe.db.sql(
        f"""
        SELECT
            cn.name AS control_number,
            cn.company,
            cn.item_name,
            cn.item_code,
            cn.arn_number,
            cn.batch,
            cna.reference_doctype,
            cna.reference_name,
            cna.purpose,
            cna.in_qty,
            cna.out_qty,
            cna.rejected_qty,
            cna.balance_qty,
            cna.posting_date,
            cna.posting_time,
            cna.activity_created_date,
            cna.activity_created_time,
            cna.activity_created_by
        FROM `tabControl Number` cn
        LEFT JOIN `tabControl Number Activity` cna ON cn.name = cna.parent
        WHERE {condition_str}
        ORDER BY cn.name, cna.posting_date, cna.posting_time
        """,
        values,
        as_dict=True,
    )
