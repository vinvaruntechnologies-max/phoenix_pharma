import frappe
import json
from frappe.utils import now_datetime
from datetime import timedelta
from phoenix_pharma.phoenix_pharma.utils.utils import (
    get_env_prefix,
    send_notification,
)
from phoenix_pharma.phoenix_pharma.custom.helper import check_returnable_components


def fetch_fields_from_sales_order_item(doc, method):
    if doc.sales_order and doc.production_item:
        # Fetch from Sales Order Item
        sales_order_item = frappe.get_value(
            "Sales Order Item",
            {"parent": doc.sales_order, "item_code": doc.production_item},
            ["uom", "conversion_factor", "custom_mrp", "stock_qty", "qty", "rate"],
            as_dict=True,
        )

        if sales_order_item:
            doc.custom_sale_uom = sales_order_item.uom
            doc.custom_uom_conversion_factor = sales_order_item.conversion_factor
            doc.custom_mrp = sales_order_item.custom_mrp
            doc.custom_stock_qty = sales_order_item.stock_qty
            doc.custom_sale_qty = sales_order_item.qty
            doc.custom_rate = sales_order_item.rate


def before_insert(doc, method=None):
    if doc.amended_from:
        doc.custom_notified_statuses = json.dumps(
            ["Not Started", "In Process", "Completed", "Closed"]
        )

    # Fetch cost center from Sales Order if available
    if doc.sales_order and not doc.custom_cost_center:
        custom_cost_center = frappe.db.get_value(
            "Sales Order", doc.sales_order, "cost_center"
        )
        if custom_cost_center:
            doc.custom_cost_center = custom_cost_center

    # Fallback: Fetch from Production Plan if Sales Order not available
    if not doc.sales_order and not doc.custom_cost_center and doc.production_plan:
        custom_cost_center = frappe.db.get_value(
            "Production Plan", doc.production_plan, "custom_cost_center"
        )
        if custom_cost_center:
            doc.custom_cost_center = custom_cost_center


def on_change(doc, method=None):
    # Load notified statuses from custom field
    notified_statuses = []
    if doc.custom_notified_statuses:
        try:
            notified_statuses = json.loads(doc.custom_notified_statuses)
        except Exception:
            pass  # Ignore malformed JSON

    current_status = doc.status
    if current_status not in notified_statuses:
        return  # Status already notified

    # Notify QA, prod, stores users based on cost center of Work Order
    qa_role_map = {
        "Puducherry - PBPL": "QA Approver Puducherry - PBPL",
        "Assam - PBPL": "QA Approver Assam - PBPL",
        "Assam - PL": "QA Approver Assam - PL",
    }

    production_role_map = {
        "Puducherry - PBPL": "Production Approver Puducherry - PBPL",
        "Assam - PBPL": "Production Approver Assam - PBPL",
        "Assam - PL": "Production Approver Assam - PL",
    }

    stores_role_map = {
        "Puducherry - PBPL": "Stores Approver Puducherry - PBPL",
        "Assam - PBPL": "Stores Approver Assam - PBPL",
        "Assam - PL": "Stores Approver Assam - PL",
    }

    work_order_link = frappe.utils.get_url_to_form("Work Order", doc.name)
    sales_order_link = frappe.utils.get_url_to_form("Sales Order", doc.sales_order)
    cost_center = doc.custom_cost_center
    if doc.docstatus == 1 and doc.status == "Not Started":
        if cost_center:
            # Notify Stores
            stores_role = stores_role_map.get(cost_center)
            if stores_role:
                stores_subject = f"{get_env_prefix()} Stores [Action]: Work Order {doc.name} Submitted for the SO {doc.sales_order}"
                stores_message = (
                    f"Hello Stores Team,<br>"
                    f"Work Order has been submitted by the QA team, Kindly issue materials required for production<br>"
                    f"<b>Work Order:</b> <a href='{work_order_link}' target='_blank'>{doc.name}</a><br>"
                    f"<b>Status:</b> {doc.status}<br>"
                    f"<b>Item To Mfg.:</b> {doc.production_item}: {doc.item_name}<br>"
                    f"<b>Batch:</b> {doc.custom_batch_no}<br>"
                    f"<b>Linked Sales Order:</b> <a href='{sales_order_link}' target='_blank'>{doc.sales_order}</a><br>"
                    f"<b>Type:</b> {doc.custom_domestic__export_order}<br>"
                )
                send_notification(doc, stores_role, stores_subject, stores_message)

            # Notify Production Approver
            prod_role = production_role_map.get(cost_center)
            if prod_role:
                prod_subject = f"{get_env_prefix()} Production [Info]: Work Order {doc.name} Submitted for the SO {doc.sales_order}"
                prod_message = (
                    f"Hello Production Team,<br>"
                    f"Work Order has been submitted by the QA team, Kindly verify the same and prepare the production activities<br>"
                    f"<b>Work Order:</b> <a href='{work_order_link}' target='_blank'>{doc.name}</a><br>"
                    f"<b>Status:</b> {doc.status}<br>"
                    f"<b>Item To Mfg.:</b> {doc.production_item}: {doc.item_name}<br>"
                    f"<b>Batch:</b> {doc.custom_batch_no}<br>"
                    f"<b>Linked Sales Order:</b> <a href='{sales_order_link}' target='_blank'>{doc.sales_order}</a><br>"
                    f"<b>Type:</b> {doc.custom_domestic__export_order}<br>"
                )
                send_notification(doc, prod_role, prod_subject, prod_message)

    if doc.docstatus == 1 and doc.status == "In Process":
        if cost_center:
            # Notify QA
            qa_role = qa_role_map.get(cost_center)
            if qa_role:
                stores_subject = f"{get_env_prefix()} QA [Info]: Required Materials are received for production for the Work Order {doc.name}"
                stores_message = (
                    f"Hello QA Team,<br>"
                    f"Required materials have been received for production, Kindly verify if everything looks good.<br>"
                    f"<b>Work Order:</b> <a href='{work_order_link}' target='_blank'>{doc.name}</a><br>"
                    f"<b>Status:</b> {doc.status}<br>"
                    f"<b>Item To Mfg.:</b> {doc.production_item}: {doc.item_name}<br>"
                    f"<b>Batch:</b> {doc.custom_batch_no}<br>"
                    f"<b>Linked Sales Order:</b> <a href='{sales_order_link}' target='_blank'>{doc.sales_order}</a><br>"
                    f"<b>Type:</b> {doc.custom_domestic__export_order}<br>"
                )
                send_notification(doc, qa_role, stores_subject, stores_message)

            # Notify Production Approver
            prod_role = production_role_map.get(cost_center)
            if prod_role:
                prod_subject = f"{get_env_prefix()} Production [Action]: Required Materials are received for production for the Work Order {doc.name}"
                prod_message = (
                    f"Hello Production Team,<br>"
                    f"Required materials have been received for production, Kindly proceeed with batch production by executing the generated Job cards linked to the Work Order<br>"
                    f"<b>Work Order:</b> <a href='{work_order_link}' target='_blank'>{doc.name}</a><br>"
                    f"<b>Status:</b> {doc.status}<br>"
                    f"<b>Item To Mfg.:</b> {doc.production_item}: {doc.item_name}<br>"
                    f"<b>Batch:</b> {doc.custom_batch_no}<br>"
                    f"<b>Linked Sales Order:</b> <a href='{sales_order_link}' target='_blank'>{doc.sales_order}</a><br>"
                    f"<b>Type:</b> {doc.custom_domestic__export_order}<br>"
                )
                send_notification(doc, prod_role, prod_subject, prod_message)
    # * currently this does not trigger notification as expected, since work order items gets updated later after status is changed
    # * hence notifying the stores users through a scheduled job
    # if doc.docstatus == 1 and doc.status in ["Completed", "Closed"]:
    #     has_return = check_returnable_components(doc)
    #     if cost_center and has_return:
    #         # Notify Stores
    #         stores_role = stores_role_map.get(cost_center)
    #         if stores_role:
    #             stores_subject = f"{get_env_prefix()} Stores [Action]: Work Order {doc.name} has some items to be returned"
    #             stores_message = (
    #                 f"Hello Stores Team,<br>"
    #                 f"Work Order has some items which are to be returned to stores from WIP Warehouse ( Production WH. ),<br>"
    #                 f"Please open the Work Order and click <b>'Return Components'</b> to initiate the return process.<br>"
    #                 f"<b>Work Order with Return Items:</b> <a href='{work_order_link}' target='_blank'>{doc.name}</a><br>"
    #                 f"<b>Status:</b> {doc.status}<br>"
    #             )
    #             send_notification(doc, stores_role, stores_subject, stores_message)

    # After sending notifications
    if current_status in notified_statuses and current_status not in [
        "Completed",
        "Closed",
    ]:  # removal of completed and closed will be done by scheduled job run
        notified_statuses.remove(current_status)
        doc.db_set(
            "custom_notified_statuses",
            json.dumps(notified_statuses),
            update_modified=False,
        )
#* does not seem to run correctly for some reason in local env scheduled time
def notify_returnable_work_orders():
    stores_role_map = {
        "Puducherry - PBPL": "Stores Approver Puducherry - PBPL",
        "Assam - PBPL": "Stores Approver Assam - PBPL",
        "Assam - PL": "Stores Approver Assam - PL",
    }
    try:
        start_time = now_datetime() - timedelta(hours=36)
        work_orders = frappe.get_all(
            "Work Order",
            filters={
                "status": ["in", ["Completed", "Closed"]],
                "docstatus": 1,
                "modified": [">=", start_time],
            },
            fields=["name", "custom_cost_center", "custom_notified_statuses"],
        )
        for wo in work_orders:
            doc = frappe.get_doc("Work Order", wo.name)
            current_status = doc.status
            cost_center = doc.custom_cost_center
            notified_statuses = []
            if doc.custom_notified_statuses:
                try:
                    notified_statuses = json.loads(doc.custom_notified_statuses)
                except Exception:
                    pass
            if not cost_center:
                continue

            if current_status not in notified_statuses:
                continue  # Status already notified

            has_return = check_returnable_components(doc)
            if has_return:
                stores_role = stores_role_map.get(doc.custom_cost_center)
                if stores_role:
                    work_order_link = frappe.utils.get_url_to_form(
                        "Work Order", doc.name
                    )
                    subject = f"{get_env_prefix()} Stores [Action]: Work Order {doc.name} has some items to be returned"
                    message = (
                        f"Hello Stores Team,<br>"
                        f"Work Order has some items which are to be returned to stores from WIP Warehouse ( Production WH. ),<br>"
                        f"Please open the Work Order and click <b>'Return Components'</b> to initiate the return process.<br>"
                        f"<b>Work Order with Return Items:</b> <a href='{work_order_link}' target='_blank'>{doc.name}</a><br>"
                        f"<b>Status:</b> {doc.status}<br>"
                    )
                    send_notification(doc, stores_role, subject, message)

            # After sending notifications
            if current_status in notified_statuses:
                notified_statuses.remove(current_status)
                doc.db_set(
                    "custom_notified_statuses",
                    json.dumps(notified_statuses),
                    update_modified=False,
                )
    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "Failed while processing Work Orders to determine 'Returnable Items'",
        )
