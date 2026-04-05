import frappe
from frappe.utils import (
    flt,
    now_datetime,
    format_datetime,
    get_time,
    getdate,
    nowdate,
    nowtime,
)
import time


def update_control_number_item_qty_with_logs():
    logs = []
    updated = 0
    failed = 0
    start_time = time.time()
    script_start = now_datetime()

    logs.append(f"🔧 Script Start Time: {format_datetime(script_start)}")
    logs.append("------------------------------------------------------")

    # Get all Control Numbers with zero item_quantity
    cn_list = frappe.get_all(
        "Control Number", filters={"item_quantity": 0}, fields=["name", "item_code"]
    )

    logs.append(f"📦 Total CNs to check: {len(cn_list)}")
    logs.append("")

    for cn in cn_list:
        timestamp = format_datetime(now_datetime(), "HH:mm:ss")

        try:
            # Find matching Purchase Receipt Item
            pr_item = frappe.db.get_value(
                "Purchase Receipt Item",
                filters={"custom_control_number": cn.name},
                fieldname=["qty", "name", "parent"],
                as_dict=True,
            )
            if pr_item and flt(pr_item.qty) > 0:  # ignores returned qty
                # Update the item_quantity
                frappe.db.set_value(
                    "Control Number", cn.name, "item_quantity", flt(pr_item.qty)
                )
                updated += 1
                logs.append(
                    f"[{timestamp}]: (Success) CN `{cn.name}` updated to `{pr_item.qty}` from PR `{pr_item.parent}` (Item: `{pr_item.name}`)"
                )
            else:
                failed += 1
                reason = "No matching PR Item found" if not pr_item else "Invalid qty"
                logs.append(
                    f"[{timestamp}]: (Failed) CN `{cn.name}` not updated: {reason}"
                )
        except Exception as e:
            failed += 1
            error_msg = (
                f"[{timestamp}]: (Error) CN `{cn.name}` failed with error: {str(e)}"
            )
            logs.append(error_msg)
            frappe.log_error(frappe.get_traceback(), f"Fix CN Qty Error - {cn.name}")

    frappe.db.commit()

    duration = time.time() - start_time
    logs.append("")
    logs.append("------------------------------------------------------")
    logs.append(f"📈 Total Updated: {updated}")
    logs.append(f"⚠ Total Failed: {failed}")
    logs.append(f"⏱️ Duration: {round(duration, 2)} seconds")

    # Save to custom log doctype
    save_fix_logs_to_custom_doctype("Fix CN Item Qty", logs)

    return {"updated": updated, "failed": failed, "log": logs}


def save_fix_logs_to_custom_doctype(title, log_lines):
    """Save logs to a custom doctype for persistent tracking"""
    try:
        log_doc = frappe.get_doc(
            {
                "doctype": "Custom Script Log",
                "title": title,
                "log": "\n".join(log_lines),
            }
        )

        log_doc.insert(ignore_permissions=True)
        frappe.db.commit()

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Log Save Failure - Fix CN Qty")


def populate_control_number_activity_rows(dry_run=True):
    """This script to be run only once initially to populate the child table as part of migration"""
    logs = []
    updated = 0
    skipped = 0
    failed = 0

    logs.append(f"Script started at {now_datetime()} - Dry Run: {dry_run}")

    cn_list = frappe.get_all(
        "Control Number",
        filters={"child_row_reference_doctype": ["in", ["", None]]},
        fields=[
            "name",
            "item_code",
            "reference_name",
            "reference_doctype",
            "item_quantity",
            "reference_document_status",
            "reference_document_date",
        ],
    )

    logs.append(f"📦 Total CNs to check: {len(cn_list)}")
    logs.append("")

    for cn in cn_list:
        try:
            if not (cn.reference_doctype and cn.reference_name):
                skipped += 1
                logs.append(
                    f"[Skipped] CN `{cn.name}` missing reference_doctype or reference_name"
                )
                continue

            # Fetch PR Item using CN name in custom_control_number
            pr_item = frappe.db.get_value(
                "Purchase Receipt Item",
                filters={"custom_control_number": cn.name},
                fieldname=["name", "qty", "parent", "docstatus"],
                as_dict=True,
            )

            if not pr_item:
                skipped += 1
                logs.append(f"[Skipped] CN `{cn.name}`: No PR Item found")
                continue

            # Get posting date & time
            pr_doc_fields = frappe.db.get_value(
                "Purchase Receipt",
                pr_item.parent,
                ["posting_date", "posting_time", "docstatus", "is_return"],
                as_dict=True,
            )

            if pr_doc_fields.is_return:
                logs.append(
                    f"[SKIPPED] CN `{cn.name}`: PR `{pr_item.parent}` is a return."
                )
                skipped += 1
                continue

            # Check if CN Activity table is empty
            activity_exists = frappe.db.exists(
                "Control Number Activity", {"parent": cn.name}
            )
            if activity_exists:
                logs.append(
                    f"[SKIPPED] CN `{cn.name}`: Activity table already populated."
                )
                skipped += 1
                continue

            # Values to be set in CN
            update_fields = {
                "child_row_reference_doctype": "Purchase Receipt Item",
                "child_row_name": pr_item.name,
                "reference_document_time": get_time(pr_doc_fields.posting_time),
            }

            if not dry_run:
                frappe.db.set_value("Control Number", cn.name, update_fields)

            # Prepare child table row
            child_row = {
                "reference_doctype": cn.reference_doctype,
                "reference_name": cn.reference_name,
                "reference_document_status": cn.reference_document_status,
                "child_row_reference_doctype": "Purchase Receipt Item",
                "child_row_name": pr_item.name,
                "item_code": cn.item_code,
                "in_qty": cn.item_quantity,
                "out_qty": 0,
                "balance_qty": cn.item_quantity,
                "posting_date": getdate(cn.reference_document_date),
                "posting_time": get_time(pr_doc_fields.posting_time),
                "purpose": "Receipt",
                # New fields for tracking
                "activity_created_date": nowdate(),
                "activity_created_time": nowtime(),
                "activity_created_by": frappe.session.user,
            }

            if not dry_run:
                cn_doc = frappe.get_doc("Control Number", cn.name)
                cn_doc.append("control_number_activity", child_row)
                cn_doc.save(ignore_permissions=True)

            logs.append(
                f"[Updated] CN `{cn.name}`: Added row for PR Item `{pr_item.name}` from PR `{pr_item.parent}`"
            )
            updated += 1

        except Exception as e:
            frappe.log_error(
                frappe.get_traceback(), f"CN Activity Migration Error - {cn.name}"
            )
            logs.append(f"[ERROR] CN `{cn.name}`: {str(e)}")
            failed += 1

    if not dry_run:
        frappe.db.commit()

    logs.append(f"Script completed at {now_datetime()}")
    logs.append(f"Summary: Updated: {updated}, Skipped: {skipped}, Failed: {failed}")

    # Save logs
    save_fix_logs_to_custom_doctype(
        "Fix CN Activity Migration" + (" [Dry Run]" if dry_run else ""), logs
    )

    return {"updated": updated, "skipped": skipped, "failed": failed, "log": logs}


def create_old_series_control_numbers():
    """ Creates CN records for old CN series CTRN if exists in Purchase Receipt Items"""
    logs = []
    created = 0
    failed = 0
    script_start = now_datetime()

    logs.append(f"🔧 Script Start Time: {format_datetime(script_start)}")
    logs.append("------------------------------------------------------")

    # Get all Purchase Receipt Items with old ctrn number series
    pri_list = frappe.get_all(
        "Purchase Receipt Item",
        filters={"custom_control_number": ["like", "%CTRN%"]},
        fields=[
            "name",
            "docstatus",
            "item_code",
            "item_name",
            "qty",
            "uom",
            "rejected_qty",
            "quality_inspection",
            "batch_no",
            "manufacturer",
            "custom_control_number",
            "custom__no_of_containers",
            "parent",
        ],
    )
    logs.append(f"📦 Total CNs to create: {len(pri_list)}")
    logs.append("")
    docstatus_map = {0: "Draft", 1: "Submitted", 2: "Cancelled"}
    for pri in pri_list:
        if pri.docstatus == 2:
            continue
        timestamp = format_datetime(now_datetime(), "HH:mm:ss")
        parent = pri.get("parent")
        batch_no = pri.get("batch_no")
        batch_mfg, batch_exp = None, None  # Default values
        if batch_no and frappe.db.exists("Batch", batch_no):
            batch_mfg = frappe.db.get_value("Batch", batch_no, "manufacturing_date")
            batch_exp = frappe.db.get_value("Batch", batch_no, "expiry_date")
        # Validation for Quality Inspection (ARN)
        ar_no = pri.get("quality_inspection")
        arn_date, arn_status, arn_sample_size = None, None, None  # Default values
        if ar_no:
            arn_date = frappe.db.get_value("Quality Inspection", ar_no, "report_date")
            arn_status = frappe.db.get_value("Quality Inspection", ar_no, "status")
            arn_sample_size = frappe.db.get_value(
                "Quality Inspection", ar_no, "sample_size"
            )

        item_qty = flt(
            pri.qty
        )  # balance available accepted qty which will show in balance
        rejected_qty = flt(pri.rejected_qty)
        parent_doc = frappe.db.get_value(
            "Purchase Receipt",
            parent,
            [
                "posting_date",
                "posting_time",
                "docstatus",
                "company",
                "supplier",
                "custom_abbrev",
            ],
            as_dict=True,
        )
        # Fetch abbreviation, fallback to Company abbr if missing
        abbr_value = parent_doc.get("custom_abbrev") or frappe.db.get_value(
            "Company", parent_doc.company, "abbr"
        )
        control_number_data = {
            "company": parent_doc.company,
            "abbr": abbr_value,
            "reference_doctype": "Purchase Receipt",
            "reference_name": parent,
            "reference_document_status": docstatus_map.get(parent_doc.docstatus),
            "reference_document_date": getdate(parent_doc.posting_date),
            "reference_document_time": get_time(parent_doc.posting_time),
            "supplier": parent_doc.get("supplier"),
            "item_code": pri.item_code,
            "item_quantity": item_qty,
            "rejected_quantity": rejected_qty,
            "item_uom": pri.uom,
            "manufacturer": pri.get("manufacturer"),
            "no_of_containers": pri.get("custom__no_of_containers"),
            "arn_number": ar_no,
            "arn_date": arn_date,
            "arn_status": arn_status,
            "sample_quantity": flt(arn_sample_size) if arn_sample_size else 0.0,
            "batch": batch_no,
            "mfg_date": batch_mfg,
            "expiry_date": batch_exp,
            "child_row_reference_doctype": "Purchase Receipt Item",
            "child_row_name": pri.name,
        }
        try:
            # Create a new Control Number
            control_number_data["name"] = pri.custom_control_number
            if not frappe.db.exists("Control Number", control_number_data["name"]):
                control_number_doc = frappe.get_doc(
                    {"doctype": "Control Number", **control_number_data}
                )
                control_number_doc.insert(ignore_permissions=True)

            created += 1
            logs.append(
                f"[{timestamp}]: (Success) CN `{control_number_doc.name}` created for PR `{pri.parent}` (Item: `{pri.item_code}:{pri.name}`)"
            )
            # docstatus 1 then add the cn activity row, 2 already being skipped, 0 not needed as actual submission will add row
            if pri.docstatus == 1:
                control_number_doc.append(
                    "control_number_activity",
                    {
                        "reference_doctype": "Purchase Receipt",
                        "reference_name": parent,
                        "reference_document_status": docstatus_map.get(
                            parent_doc.docstatus
                        ),
                        "child_row_reference_doctype": "Purchase Receipt Item",
                        "child_row_name": pri.name,
                        "item_code": pri.item_code,
                        "in_qty": item_qty,
                        "out_qty": 0,
                        "rejected_qty": rejected_qty,
                        "balance_qty": item_qty,  # same as item qty
                        "posting_date": getdate(parent_doc.posting_date),
                        "posting_time": get_time(parent_doc.posting_time),
                        "purpose": "Receipt",
                        "activity_created_date": nowdate(),
                        "activity_created_time": nowtime(),
                        "activity_created_by": frappe.session.user,
                    },
                )
                control_number_doc.save(ignore_permissions=True)

        except Exception as e:
            frappe.log_error(
                frappe.get_traceback(),
                f"CN Creation for Series CNTR Error - {control_number_doc.name}",
            )
            logs.append(f"[ERROR] CN `{control_number_doc.name}`: {str(e)}")
            failed += 1
    logs.append(f"Script completed at {now_datetime()}")
    logs.append(f"Summary: created: {created}, Failed: {failed}")

    # Save logs
    save_fix_logs_to_custom_doctype("CN Creation for Series CNTR", logs)

    return {
        "created": created,
        "failed": failed,
        "log": logs,
    }

def update_all_uom_references(item_code, new_stock_uom):
    """
    Updates Stock UOM for the given item across all key doctypes.
    WARNING: Run this only after taking a full database backup.
    not handled:
    tabSales Order Item
    tabDelivery Note Item
    tabSales Invoice Item
    tabMaterial Request Item
    tabStock Entry Detail
    """
    logs = []
    # --- Step 1: Update Bin ---
    bins = frappe.get_all("Bin", filters={"item_code": item_code}, pluck="name")
    for bin_name in bins:
        frappe.db.set_value("Bin", bin_name, "stock_uom", new_stock_uom)
    logs.append(f"✅ Updated {len(bins)} Bin records.")

    # --- Step 2: Update Stock Ledger Entry ---
    sle_count = frappe.db.count("Stock Ledger Entry", {"item_code": item_code})
    if sle_count:
        frappe.db.sql("""
            UPDATE `tabStock Ledger Entry`
            SET stock_uom = %s
            WHERE item_code = %s
        """, (new_stock_uom, item_code))
        logs.append(f"✅ Updated {sle_count} Stock Ledger Entries.")

    # --- Step 3: Update Item Price ---
    item_prices = frappe.db.count("Item Price", {"item_code": item_code})
    if item_prices:
        frappe.db.sql("""
            UPDATE `tabItem Price`
            SET uom = %s
            WHERE item_code = %s
        """, (new_stock_uom, item_code))
        logs.append(f"✅ Updated {item_prices} Item Price records.")

    # --- Step 4: Update Purchase Receipts ---
    pr_items = frappe.db.count("Purchase Receipt Item", {"item_code": item_code})
    if pr_items:
        frappe.db.sql("""
            UPDATE `tabPurchase Receipt Item`
            SET uom = %s, stock_uom = %s
            WHERE item_code = %s
        """, (new_stock_uom, new_stock_uom, item_code))
        logs.append(f"✅ Updated {pr_items} Purchase Receipt Items.")

    # --- Step 5: Update Purchase Invoices ---
    pi_items = frappe.db.count("Purchase Invoice Item", {"item_code": item_code})
    if pi_items:
        frappe.db.sql("""
            UPDATE `tabPurchase Invoice Item`
            SET uom = %s, stock_uom = %s
            WHERE item_code = %s
        """, (new_stock_uom, new_stock_uom, item_code))
        logs.append(f"✅ Updated {pi_items} Purchase Invoice Items.")

    # --- Step 6: Update Purchase Orders ---
    po_items = frappe.db.count("Purchase Order Item", {"item_code": item_code})
    if po_items:
        frappe.db.sql("""
            UPDATE `tabPurchase Order Item`
            SET uom = %s, stock_uom = %s
            WHERE item_code = %s
        """, (new_stock_uom, new_stock_uom, item_code))
        logs.append(f"✅ Updated {po_items} Purchase Order Items.")

    cn_items = frappe.db.count("Control Number", {"item_code": item_code})
    if cn_items:
        frappe.db.sql("""
            UPDATE `tabControl Number`
            SET item_uom = %s
            WHERE item_code = %s
        """, (new_stock_uom, item_code))
        logs.append(f"✅ Updated {cn_items} Control Numbers.")

    #! sr not reqd as no uom
    # # --- Step 7: Update Stock Reconciliation ---
    # sr_items = frappe.db.count("Stock Reconciliation Item", {"item_code": item_code})
    # if sr_items:
    #     frappe.db.sql("""
    #         UPDATE `tabStock Reconciliation Item`
    #         SET uom = %s, stock_uom = %s
    #         WHERE item_code = %s
    #     """, (new_stock_uom, new_stock_uom, item_code))
    #      logs.append(f"✅ Updated {sr_items} Stock Reconciliation Items.")

    # --- Step 8: Update Item Master (last, after dependencies) ---
    # frappe.db.sql("""
    #     UPDATE `tabItem`
    #     SET stock_uom = %s, uom = %s
    #     WHERE name = %s
    # """, (new_stock_uom, new_stock_uom, item_code))

    # --- Commit all changes ---
    frappe.db.commit()
    logs.append(f"🎯 All references updated for item {item_code} to UOM '{new_stock_uom}'. You can now safely change Default UOM.")

    save_fix_logs_to_custom_doctype(
        "Item UOM changed in all reference transactions", logs
    )
    return {
        "status": "success",
        "log": logs,
    }


#! Run the below script only once as a migration or fix as it will mess up if run mutiple tries due to replacing logic
# @frappe.whitelist()
# def run_update_cn_qty_script():
#     return update_control_number_item_qty_with_logs()


# @frappe.whitelist()
# def run_cn_activity_migration(dry_run=True):
#     return populate_control_number_activity_rows(frappe.parse_json(dry_run))


# @frappe.whitelist()
# def run_old_series_cn_script():
#     return create_old_series_control_numbers()

@frappe.whitelist()
def fix_item_uom_including_dependancies(item_code, new_stock_uom):
     return update_all_uom_references(item_code, new_stock_uom)