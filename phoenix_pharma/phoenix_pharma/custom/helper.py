import frappe
from frappe.utils import flt
from collections import defaultdict

ALLOWED_ITEM_GROUPS = {"RM", "PM", "Active"}


def handle_preshipment_batch_creation(doc):
    """Create Stock Entry for Preshipment Batch Creation per DN item"""
    for item in doc.items:
        batch = item.get("custom_preshipment_batch_no")
        if not batch:
            frappe.throw(f"Preshipment Batch not specified for item {item.item_code}")

        # 🧹 Clear any auto-selected batch if different
        if item.batch_no and item.batch_no != batch:
            item.db_set("batch_no", "")

        se = frappe.get_doc(
            {
                "doctype": "Stock Entry",
                "stock_entry_type": "Preshipment Batch Creation",
                "company": doc.company,
                "items": [
                    {
                        "item_code": item.item_code,
                        "t_warehouse": item.warehouse,
                        "qty": item.qty,
                        "uom": item.uom,
                        "batch_no": batch,
                    }
                ],
            }
        )

        se.insert()
        se.submit()
        se.add_tag("System Generated")

        # ✅ Set this batch into DN item for users to generate
        item.db_set("batch_no", batch)


def handle_preshipment_batch_deletion(doc):
    """Delete previously created Preshipment Batch (discard logic)"""
    for item in doc.items:
        batch = item.get("custom_preshipment_batch_no")
        if not batch:
            continue  # Nothing to delete
        item.db_set("batch_no", None)
        se = frappe.get_doc(
            {
                "doctype": "Stock Entry",
                "stock_entry_type": "Preshipment Batch Deletion",
                "company": doc.company,
                "items": [
                    {
                        "item_code": item.item_code,
                        "s_warehouse": item.warehouse,
                        "qty": item.qty,
                        "uom": item.uom,
                        "batch_no": batch,
                        "is_scrap_item": 1,
                    }
                ],
            }
        )

        se.insert()
        se.submit()
        se.add_tag("System Generated")


@frappe.whitelist()
def load_exploded_se_items(doc):
    """
    Populates the `custom_exploded_items` child table in Stock Entry
    using FIFO from Control Numbers (sorted by reference_document_date, arn_date).
    Avoids duplicate CN allocation by tracking used quantity globally.
    """
    # not showing the ARN in mfg stock entry as ARN is reduced in material transfer to manufacture itself
    if isinstance(doc, str):
        doc = frappe.parse_json(doc)
    if isinstance(doc, dict):
        doc = frappe.get_doc(doc)
    if doc.stock_entry_type not in [
        "Material Issue",
        "Material Transfer for Manufacture",
        "Destruction",
    ]:
        return
    doc.set("custom_exploded_items", [])  # Clear existing data

    # Track how much quantity has already been allocated per CN
    cn_allocated_qty = defaultdict(float)

    for item in doc.items:
        item_group = frappe.db.get_value("Item", item.item_code, "item_group")
        if item_group not in ALLOWED_ITEM_GROUPS:
            continue
        remaining_qty = flt(item.qty)
        if remaining_qty <= 0:
            continue

        # Filters for Control Numbers
        filters = {
            "company": doc.company,
            "item_code": item.item_code,
            "reference_document_status": "Submitted",
            "arn_number": ["not in", ["", None]],
            "arn_date": ["not in", ["", None]],
            "arn_status": "Accepted",
            "item_quantity": [">", 0],
        }

        if item.batch_no:
            filters["batch"] = item.batch_no

        # Fetch eligible Control Numbers
        cn_records = frappe.get_all(
            "Control Number",
            filters=filters,
            fields=[
                "name",
                "item_name",
                "item_quantity",
                "item_uom",
                "batch",
                "assay",
                "lod",
                "arn_number",
                "retest_date",
                "arn_date",
                "reference_document_date",
            ],
            order_by="reference_document_date asc, arn_date asc",
        )

        for cn in cn_records:
            cn_name = cn.name
            total_qty = flt(cn.item_quantity)
            already_allocated = cn_allocated_qty[cn_name]
            available_qty = total_qty - already_allocated

            if available_qty <= 0 or remaining_qty <= 0:
                continue

            allocated_qty = min(remaining_qty, available_qty)

            doc.append(
                "custom_exploded_items",
                {
                    "item_code": item.item_code,
                    "item_name": cn.item_name,
                    "available_qty": total_qty,
                    "issued_qty": allocated_qty,
                    "uom": cn.item_uom,
                    "batch": cn.batch,
                    "assay": cn.assay,
                    "lod": cn.lod,
                    "arn": cn.arn_number,
                    "retest_date": cn.retest_date,
                    "control_number": cn.name,
                    "total_required_qty": flt(item.qty),
                },
            )

            cn_allocated_qty[cn_name] += allocated_qty
            remaining_qty -= allocated_qty

        # Optional: You can log or track shortfall if remaining_qty > 0
        if remaining_qty > 0:
            frappe.msgprint(
                f"Insufficient ARN-issued qty for the item {item.item_code}: {item.item_name or ''} with Shortfall: {remaining_qty}"
            )
        # * NOTE: if there is a difference in control number avl qty and physical stock, stock reconcilliation

    return doc


def update_exploded_items_in_work_order(doc):
    """copies exploded items (custom_exploded_items) to issued ARN Reference child table in work order - custom_issued_arn_reference
    This reference is needed in case return from WIP to stores request is initiated for CN / ARN reconcilliation"""
    if (
        doc.stock_entry_type == "Material Transfer for Manufacture"
        and not doc.is_return
    ):
        if not doc.get("custom_exploded_items") or not doc.get("work_order"):
            return  # Nothing to copy or no target Work Order

        try:
            work_order = frappe.get_doc("Work Order", doc.work_order)
        except frappe.DoesNotExistError:
            frappe.throw(f"Work Order {doc.work_order} does not exist")

        needs_update = False  # avoid unnecessary save()
        if doc.docstatus == 1:
            # * Clear existing entries assuming only 1 indent be raised in current design
            work_order.set("custom_issued_arn_reference", [])
            for row in doc.custom_exploded_items:
                work_order.append(
                    "custom_issued_arn_reference",
                    {
                        "item_code": row.item_code,
                        "item_name": row.item_name,
                        "batch": row.batch,
                        "control_number": row.control_number,
                        "arn": row.arn,
                        "available_qty": row.available_qty,
                        "issued_qty": row.issued_qty,
                        "uom": row.uom,
                        "total_required_qty": row.total_required_qty,
                        "assay": row.assay,
                        "lod": row.lod,
                        "retest_date": row.retest_date,
                    },
                )
            needs_update = True

        elif doc.docstatus == 2:
            # * Clear existing entries assuming only 1 indent be raised in current design if cancelled
            if work_order.get("custom_issued_arn_reference"):
                work_order.set("custom_issued_arn_reference", [])
                needs_update = True

        if needs_update:
            work_order.save(ignore_permissions=True)


@frappe.whitelist()
def load_issued_items_from_work_order(doc):
    """
    Populate `custom_exploded_items` in Stock Entry (return type)
    based on ARN-wise issued items stored in Work Order (custom_issued_arn_reference).
    This reverses previously issued items proportionally to returned quantity.
    """
    if isinstance(doc, str):
        doc = frappe.parse_json(doc)
    if isinstance(doc, dict):
        doc = frappe.get_doc(doc)

    if not (
        doc.is_return
        and doc.stock_entry_type == "Material Transfer for Manufacture"
        and doc.work_order
    ):
        return doc

    doc.set("custom_exploded_items", [])  # Clear current exploded items

    # Track how much qty has been allocated per control number
    cn_allocated_qty = defaultdict(float)

    # Fetch Work Order and its issued ARN reference table
    wo = frappe.get_doc("Work Order", doc.work_order)
    issued_items = wo.get("custom_issued_arn_reference") or []

    for item in doc.items:
        item_qty_to_return = flt(item.qty)
        if item_qty_to_return <= 0:
            continue

        for cn in issued_items:
            if cn.item_code != item.item_code:
                continue
            if item.batch_no and cn.batch != item.batch_no:
                continue

            cn_name = cn.control_number
            total_issued = flt(cn.issued_qty)
            already_allocated = cn_allocated_qty[cn_name]
            available_to_return = total_issued - already_allocated

            if available_to_return <= 0 or item_qty_to_return <= 0:
                continue

            allocated_qty = min(item_qty_to_return, available_to_return)

            doc.append(
                "custom_exploded_items",
                {
                    "item_code": cn.item_code,
                    "item_name": cn.item_name,
                    "available_qty": total_issued,
                    "issued_qty": allocated_qty,
                    "uom": cn.uom,
                    "batch": cn.batch,
                    "assay": cn.assay,
                    "lod": cn.lod,
                    "arn": cn.arn,
                    "retest_date": cn.retest_date,
                    "control_number": cn_name,
                    "total_required_qty": flt(item.qty),
                },
            )

            cn_allocated_qty[cn_name] += allocated_qty
            item_qty_to_return -= allocated_qty

        # Optional: Handle shortfall
        if item_qty_to_return > 0:
            frappe.msgprint(
                f"Insufficient ARN qty to return for item {item.item_code}: {item.item_name or ''} with Shortfall: {item_qty_to_return}"
            )

    return doc


def check_returnable_components(doc, method=None):
    has_returnables = False
    for item in doc.required_items:
        transferred = flt(item.transferred_qty)
        returned = flt(item.returned_qty)
        consumed = flt(item.consumed_qty)

        if consumed < (transferred - returned):
            has_returnables = True
            break

    return has_returnables
