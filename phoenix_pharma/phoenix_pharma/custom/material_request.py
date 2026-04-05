import frappe
import json
from phoenix_pharma.phoenix_pharma.utils.utils import get_env_prefix,send_notification

def before_insert(doc, method=None):
    if doc.amended_from:
        doc.custom_notified_statuses = json.dumps(["Pending", "Received"])


def on_change(doc, method=None):
    if doc.material_request_type != "Purchase":
        return  # Only trigger for Purchase type

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

    material_request_link = frappe.utils.get_url_to_form("Material Request", doc.name)
    if doc.docstatus == 1 and doc.status == "Pending":
        # Notify Purchase Users on submission
        subject = f"{get_env_prefix()} Purchase [Action]: Material Request {doc.name} Submitted"
        message = (
            f"Hello Purchase Team,<br>"
            f"please process the Material Request and kindly procure the items requested.<br>"
            f"<b>Material Request:</b> <a href='{material_request_link}' target='_blank'>{doc.name}</a><br>"
            f"<b>Title:</b> {doc.title}<br>"
            f"<b>Status:</b> Pending"
        )
        send_notification(doc, "Purchase Approver", subject, message)

    elif doc.docstatus == 1 and doc.status == "Received":
        # Notify QA users based on cost center of Material Request
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

        for item in doc.items:
            if item.sales_order:
                cost_center = frappe.db.get_value(
                    "Sales Order", item.sales_order, "cost_center"
                )
                if cost_center:
                    sales_order_link = frappe.utils.get_url_to_form(
                        "Sales Order", item.sales_order
                    )
                    qa_role = qa_role_map.get(cost_center)
                    if qa_role:
                        subject = f"{get_env_prefix()} QA [Info]: Material Request {doc.name} Received for the SO {item.sales_order}"
                        message = (
                            f"Hello QA Team,<br>"
                            f"Materials have been procured. Verify if everything looks good and wait for the production plan to be submitted by prod. team,<br>"
                            f"<b>Material Request:</b> <a href='{material_request_link}' target='_blank'>{doc.name}</a><br>"
                            f"<b>Title:</b> {doc.title}<br>"
                            f"<b>Status:</b> Received<br>"
                            f"<b>Linked Sales Order:</b> <a href='{sales_order_link}' target='_blank'>{item.sales_order}</a>"
                        )
                        send_notification(doc, qa_role, subject, message)
                    # Notify Production Approver
                    prod_role = production_role_map.get(cost_center)
                    if prod_role:
                        prod_subject = f"{get_env_prefix()} Production [Action]: Material Request {doc.name} Received for the SO {item.sales_order}"
                        prod_message = (
                            f"Hello Production Team,<br>"
                            f"Materials have been procured. Please verify the raw materials stock and submit the production plan for the sales order<br>"
                            f"<b>Material Request:</b> <a href='{material_request_link}' target='_blank'>{doc.name}</a><br>"
                            f"<b>Title:</b> {doc.title}<br>"
                            f"<b>Status:</b> Received<br>"
                            f"<b>Linked Sales Order:</b> <a href='{sales_order_link}' target='_blank'>{item.sales_order}</a>"
                        )
                        send_notification(doc, prod_role, prod_subject, prod_message)
                break  # Notify only once for first valid sales order

    # After sending notifications
    if current_status in notified_statuses:
        notified_statuses.remove(current_status)
        doc.db_set(
            "custom_notified_statuses",
            json.dumps(notified_statuses),
            update_modified=False,
        )
