import frappe
from frappe.utils import nowdate, nowtime, flt, get_time, getdate


def upsert_control_number(item, parent_doc, control_number_name=None):
    """
    Create or update a Control Number document based on a line item and its parent document.

    This function is used during Purchase Receipt or Purchase Invoice workflows to:
      - Create a new Control Number for each item if it's the first save.
      - Update the existing Control Number on subsequent saves with any new/edited data.
      - Automatically link the Control Number back to the item row.

    Parameters:
        item (dict or Document): The child row (item) from the parent document.
        parent_doc (Document): The parent document, e.g., Purchase Receipt or Purchase Invoice.
        control_number_name (str, optional): If provided, updates the existing Control Number with this name.

    Returns:
        str: The name of the created or updated Control Number document.

    Example:
        upsert_control_number(item=row, parent_doc=doc)

    Notes:
        - For Purchase Receipts, it expects `custom_abbrev` field.
        - For Purchase Invoices, it expects `custom_abbr` field.
        - If custom abbreviations are not found, falls back to `Company.abbr`.
    """
    # Test - full accepted, full rejection, cancelled, partial return, full return
    # Determine correct abbreviation field based on document type
    if parent_doc.doctype == "Purchase Receipt":
        abbr_field = "custom_abbrev"
    elif parent_doc.doctype == "Purchase Invoice":
        abbr_field = "custom_abbr"
    else:
        abbr_field = "abbr"  # Default to standard abbreviation field

    # Fetch abbreviation, fallback to Company abbr if missing
    abbr_value = getattr(parent_doc, abbr_field, None) or frappe.db.get_value(
        "Company", parent_doc.company, "abbr"
    )
    # Validation for Quality Inspection (ARN)
    arn_no = item.get("quality_inspection")
    arn_date, arn_status, arn_sample_size = None, None, None  # Default values
    if arn_no:
        arn_date = frappe.db.get_value("Quality Inspection", arn_no, "report_date")
        arn_status = frappe.db.get_value("Quality Inspection", arn_no, "status")
        arn_sample_size = frappe.db.get_value(
            "Quality Inspection", arn_no, "sample_size"
        )
    # Validation for Batch
    batch_no = item.get("batch_no")
    batch_mfg, batch_exp = None, None  # Default values
    if batch_no and frappe.db.exists("Batch", batch_no):
        batch_mfg = frappe.db.get_value("Batch", batch_no, "manufacturing_date")
        batch_exp = frappe.db.get_value("Batch", batch_no, "expiry_date")
    docstatus_map = {0: "Draft", 1: "Submitted", 2: "Cancelled"}
    item_qty = flt(
        item.qty
    )  # balance available accepted qty which will show in balance
    rejected_qty = flt(item.rejected_qty)
    if parent_doc.docstatus == 2:
        item_qty = 0
        rejected_qty = 0
    control_number_data = {
        "company": parent_doc.company,
        "abbr": abbr_value,
        "reference_doctype": parent_doc.doctype,
        "reference_name": parent_doc.name,
        "reference_document_status": docstatus_map.get(parent_doc.docstatus),
        "reference_document_date": getdate(parent_doc.posting_date),
        "reference_document_time": get_time(parent_doc.posting_time),
        "supplier": getattr(parent_doc, "supplier", None),
        "item_code": item.item_code,
        "item_quantity": item_qty,
        "rejected_quantity": rejected_qty,
        "item_uom": item.uom,
        "manufacturer": item.get("manufacturer"),
        "no_of_containers": item.get("custom__no_of_containers"),
        "arn_number": arn_no,
        "arn_date": arn_date,
        "arn_status": arn_status,
        # TODO: add total sampled qty - Query the QI sampled qty for each PR item / CN and add as total_sampled qty, this has to be reduced in CN DT and auto se type mat issue
        "sample_quantity": flt(arn_sample_size) if arn_sample_size else 0.0,
        "batch": batch_no,
        "mfg_date": batch_mfg,
        "expiry_date": batch_exp,
        "child_row_reference_doctype": "Purchase Receipt Item",  # change this dynamically if needed if PI receival is introduced
        "child_row_name": item.name,
    }

    if not control_number_name:
        # Create a new Control Number
        control_number_doc = frappe.get_doc(
            {"doctype": "Control Number", **control_number_data}
        )
        control_number_doc.insert(ignore_permissions=True)
        return control_number_doc.name
    else:
        # Update the existing Control Number
        control_doc = frappe.get_doc("Control Number", control_number_name)
        for key, value in control_number_data.items():
            setattr(control_doc, key, value)
        control_doc.save(ignore_permissions=True)
        return control_number_name


def update_return_qty(item, parent_doc, control_number_name=None):
    """backup without handling partial rejections"""
    # Test - full accepted, full rejection, cancelled, partial return, full return
    # Determine correct abbreviation field based on document type
    docstatus_map = {0: "Draft", 1: "Submitted", 2: "Cancelled"}
    if control_number_name:
        # Update the existing Control Number
        control_doc = frappe.get_doc("Control Number", control_number_name)

        existing_returned_qty = control_doc.get("returned_quantity")
        current_returned_qty = flt(item.qty)
        current_balance_qty = control_doc.get("item_quantity")
        if parent_doc.docstatus == 1:
            if item.return_qty_from_rejected_warehouse:
                control_doc.rejected_quantity += current_returned_qty
                control_doc.returned_quantity += current_returned_qty
            else:
                control_doc.returned_quantity = (
                    existing_returned_qty + current_returned_qty
                )  # (-ve + -ve)
                current_balance_qty = (
                    current_balance_qty + current_returned_qty
                )  # (+ve + -ve)
                control_doc.item_quantity = current_balance_qty
            control_doc.append(
                "control_number_activity",
                {
                    "reference_doctype": parent_doc.doctype,
                    "reference_name": parent_doc.name,
                    "reference_document_status": docstatus_map.get(
                        parent_doc.docstatus
                    ),
                    "child_row_reference_doctype": "Purchase Receipt Item",
                    "child_row_name": item.name,
                    "item_code": item.item_code,
                    "in_qty": 0,
                    "out_qty": current_returned_qty,
                    "balance_qty": current_balance_qty,
                    "posting_date": getdate(parent_doc.posting_date),
                    "posting_time": get_time(parent_doc.posting_time),
                    "purpose": "Return",
                    "activity_created_date": nowdate(),
                    "activity_created_time": nowtime(),
                    "activity_created_by": frappe.session.user,
                },
            )
        elif parent_doc.docstatus == 2:
            # reverse on cancel
            if item.return_qty_from_rejected_warehouse:
                control_doc.rejected_quantity -= current_returned_qty
                control_doc.returned_quantity -= current_returned_qty
            else:
                control_doc.returned_quantity = (
                    existing_returned_qty - current_returned_qty
                )
                current_balance_qty = current_balance_qty - current_returned_qty
                control_doc.item_quantity = current_balance_qty
            # delete the Return row
            control_doc.set(
                "control_number_activity",
                [
                    row
                    for row in control_doc.control_number_activity
                    if not (
                        row.reference_doctype == parent_doc.doctype
                        and row.reference_name == parent_doc.name
                        and row.child_row_name == item.name
                        and row.purpose == "Return"
                    )
                ],
            )
        control_doc.save(ignore_permissions=True)
        return control_number_name


def log_control_number_activity(item, parent_doc, cn_name):
    docstatus_map = {0: "Draft", 1: "Submitted", 2: "Cancelled"}
    item_qty = flt(item.qty)
    balance_qty = flt(item.qty)
    rejected_qty = flt(
        item.rejected_qty,
    )
    if parent_doc.docstatus == 2:
        item_qty = 0
        balance_qty = 0
        rejected_qty = 0

    cn_doc = frappe.get_doc("Control Number", cn_name)

    existing_row = None
    for row in cn_doc.control_number_activity:
        if row.reference_name == parent_doc.name and row.child_row_name == item.name:
            existing_row = row
            break

    if existing_row:
        # Modify the existing row instead of appending a new one
        existing_row.reference_document_status = docstatus_map.get(parent_doc.docstatus)
        existing_row.in_qty = item_qty
        existing_row.out_qty = 0
        existing_row.balance_qty = balance_qty
        existing_row.rejected_qty = rejected_qty
        existing_row.posting_date = getdate(parent_doc.posting_date)
        existing_row.posting_time = get_time(parent_doc.posting_time)
        existing_row.purpose = "Receipt"
        existing_row.activity_created_date = nowdate()
        existing_row.activity_created_time = nowtime()
        existing_row.activity_created_by = frappe.session.user
    else:
        # Only append if not already present
        cn_doc.append(
            "control_number_activity",
            {
                "reference_doctype": parent_doc.doctype,
                "reference_name": parent_doc.name,
                "reference_document_status": docstatus_map.get(parent_doc.docstatus),
                "child_row_reference_doctype": "Purchase Receipt Item",
                "child_row_name": item.name,
                "item_code": item.item_code,
                "in_qty": item_qty,
                "out_qty": 0,
                "rejected_qty": rejected_qty,
                "balance_qty": balance_qty,
                "posting_date": getdate(parent_doc.posting_date),
                "posting_time": get_time(parent_doc.posting_time),
                "purpose": "Receipt",
                "activity_created_date": nowdate(),
                "activity_created_time": nowtime(),
                "activity_created_by": frappe.session.user,
            },
        )

    cn_doc.save(ignore_permissions=True)


def get_status_label(docstatus):
    return {0: "Draft", 1: "Submitted", 2: "Cancelled"}.get(docstatus, "Unknown")


def update_control_number_from_exploded_items(doc, reverse=False):
    return_to_store_from_production_wip = (
        doc.is_return and doc.stock_entry_type == "Material Transfer for Manufacture"
    )
    if doc.stock_entry_type not in [
        "Material Issue",
        "Material Transfer for Manufacture",
        "Destruction",
    ]:
        return
    for row in doc.get("custom_exploded_items") or []:
        cn_name = row.get("control_number")
        arn = row.get("arn")
        if not cn_name:
            continue

        qty = flt(row.get("issued_qty"))
        if qty == 0:
            continue

        try:
            cn_doc = frappe.get_doc("Control Number", cn_name)
            current_balance = flt(cn_doc.item_quantity)
            # * handle return_to_store_from_production_wip + reverse condition
            if return_to_store_from_production_wip:
                new_balance = current_balance - qty if reverse else current_balance + qty
                in_qty = qty
                out_qty = 0
                purpose = "Return From WIP WH"
            else:
                new_balance = current_balance + qty if reverse else current_balance - qty
                in_qty = 0
                out_qty = -qty
                purpose = doc.stock_entry_type
            if new_balance < 0 and not reverse:
                frappe.throw(
                    f"[Error] Not enough balance for ARN {arn} and Control Number {cn_name}. "
                    f"Available: {current_balance}, Required: {qty}"
                )

            # Update balance
            cn_doc.item_quantity = new_balance
            if not reverse:
            # Log activity
                cn_doc.append(
                    "control_number_activity",
                    {
                        "reference_doctype": doc.doctype,
                        "reference_name": doc.name,
                        "reference_document_status": get_status_label(doc.docstatus),
                        "child_row_reference_doctype": "Stock Entry Detail",
                        "child_row_name": row.name,
                        "item_code": row.item_code,
                        "in_qty": in_qty,
                        "out_qty": out_qty,
                        "balance_qty": new_balance,
                        "posting_date": doc.posting_date,
                        "posting_time": doc.posting_time,
                        "purpose": purpose,
                        "activity_created_date": nowdate(),
                        "activity_created_time": nowtime(),
                        "activity_created_by": frappe.session.user,
                    },
                )
            else:
                # remove the row if cancelled
                cn_doc.set(
                "control_number_activity",
                [
                    cn_row
                    for cn_row in cn_doc.control_number_activity
                    if not (
                        cn_row.child_row_name == row.name
                        and cn_row.purpose == purpose
                    )
                ],
            )
            cn_doc.save(ignore_permissions=True)

        except Exception as e:
            frappe.log_error(
                frappe.get_traceback(), f"Control Number update failed for {cn_name}"
            )
