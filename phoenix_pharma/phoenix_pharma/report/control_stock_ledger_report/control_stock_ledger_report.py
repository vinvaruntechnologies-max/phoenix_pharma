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
            "label": _("Control Number"),
            "fieldname": "name",
            "fieldtype": "Data",
            "width": 140,
        },
        {
            "label": _("Item Code"),
            "fieldname": "item_code",
            "fieldtype": "Data",
            "width": 130,
        },
        {
            "label": _("Item Name"),
            "fieldname": "item_name",
            "fieldtype": "Data",
            "width": 160,
        },
        {
            "label": _("Batch"),
            "fieldname": "batch",
            "fieldtype": "Link",
            "options": "Batch",
            "width": 110,
        },
        {
            "label": _("Qty"),
            "fieldname": "item_quantity",
            "fieldtype": "Float",
            "width": 80,
        },
        {
            "label": _("Returned Qty"),
            "fieldname": "returned_quantity",
            "fieldtype": "Float",
            "width": 90,
        },
        {"label": _("UOM"), "fieldname": "item_uom", "fieldtype": "Data", "width": 70},
        {
            "label": _("Containers"),
            "fieldname": "no_of_containers",
            "fieldtype": "Int",
            "width": 80,
        },
        {
            "label": _("Supplier"),
            "fieldname": "supplier",
            "fieldtype": "Link",
            "options": "Supplier",
            "width": 120,
        },
        {
            "label": _("Manufacturer"),
            "fieldname": "manufacturer",
            "fieldtype": "Link",
            "options": "Manufacturer",
            "width": 120,
        },
        {
            "label": _("MFG Date"),
            "fieldname": "mfg_date",
            "fieldtype": "Date",
            "width": 90,
        },
        {
            "label": _("EXP Date"),
            "fieldname": "expiry_date",
            "fieldtype": "Date",
            "width": 90,
        },
        {
            "label": _("Retest Date"),
            "fieldname": "retest_date",
            "fieldtype": "Date",
            "width": 90,
        },
        {
            "label": _("ARN No"),
            "fieldname": "arn_number",
            "fieldtype": "data",
            "width": 110,
        },
        {
            "label": _("ARN Date"),
            "fieldname": "arn_date",
            "fieldtype": "Date",
            "width": 100,
        },
        {
            "label": _("ARN Status"),
            "fieldname": "arn_status",
            "fieldtype": "Data",
            "width": 100,
        },
        {"label": _("Assay"), "fieldname": "assay", "fieldtype": "Data", "width": 80},
        {"label": _("LOD"), "fieldname": "lod", "fieldtype": "Data", "width": 80},
        # {
        #     "label": _("Warehouse"),
        #     "fieldname": "warehouse",
        #     "fieldtype": "Link",
        #     "options": "Warehouse",
        #     "width": 120,
        # },
        {
            "label": _("Reference Document"),
            "fieldname": "reference_doctype",
            "fieldtype": "Data",
            "width": 130,
        },
        {
            "label": _("Reference Id"),
            "fieldname": "reference_name",
            "fieldtype": "Dynamic Link",
            "options": "reference_doctype",
            "width": 150,
        },
        {
            "label": _("Ref Date"),
            "fieldname": "reference_document_date",
            "fieldtype": "Data",
            "width": 100,
        },
        {
            "label": _("Ref Status"),
            "fieldname": "reference_document_status",
            "fieldtype": "Data",
            "width": 100,
        },
    ]


def get_data(filters):
    conditions = []
    values = {}

    for field in [
        "company",
        "item_code",
        "name",
        "batch"
    ]:
        if filters.get(field):
            conditions.append(f"cn.{field} = %({field})s")
            values[field] = filters[field]

    condition_str = " AND ".join(conditions) if conditions else "1=1"

    data = frappe.db.sql(
        f"""
        SELECT
            cn.name, cn.company, cn.item_code, cn.item_name, cn.batch,
            cn.item_quantity, cn.returned_quantity, cn.item_uom,
            cn.no_of_containers,
            cn.supplier, cn.manufacturer, cn.mfg_date, cn.expiry_date,
            cn.retest_date, cn.arn_number, cn.arn_date, cn.arn_status,
            cn.assay, cn.lod, cn.reference_doctype, cn.reference_name,
            cn.reference_document_date, cn.reference_document_status
        FROM `tabControl Number` cn
        WHERE {condition_str}
        ORDER BY cn.modified DESC
    """,
        values,
        as_dict=True,
    )

    # Pull warehouse from reference doc if available
    # for row in data:
    #     row["warehouse"] = ""
    #     if row.get("reference_doctype") and row.get("reference_name"):
    #         try:
    #             ref_doc = frappe.get_doc(
    #                 row["reference_doctype"], row["reference_name"]
    #             )
    #             if hasattr(ref_doc, "set_warehouse"):
    #                 row["warehouse"] = ref_doc.set_warehouse
    #             elif hasattr(ref_doc, "items") and ref_doc.items:
    #                 row["warehouse"] = ref_doc.items[0].warehouse
    #         except:
    #             pass

    return data
