import frappe
import json
from phoenix_pharma.phoenix_pharma.utils.utils import get_env_prefix,send_notification

def before_insert(doc, method=None):
    if doc.amended_from:
        # Only notify once for submitted (1) and cancelled (2)
        doc.custom_notified_statuses = json.dumps([1, 2])


def on_update(doc, method=None):
    # Load notified statuses from custom field
    notified_statuses = []
    if doc.custom_notified_statuses:
        try:
            notified_statuses = json.loads(doc.custom_notified_statuses)
        except Exception:
            pass  # Ignore malformed JSON

    current_status = doc.docstatus
    if current_status not in notified_statuses:
        return  # Status already notified

    sales_invoice_link = frappe.utils.get_url_to_form("Sales Invoice", doc.name)
    state = "Submitted" if current_status == 1 else "Cancelled"
    # Item list formatting
    item_lines = ""
    for item in doc.items:
        item_lines += f"{item.item_code}: {item.item_name}<br>"
    subject = f"{get_env_prefix()} {doc.cost_center} Billing [Info]: {doc.custom_domestic_or_export or ''} Sales Invoice {doc.name} - {state.lower()}"
    message = (
        f"Hello,<br>"
        f"Sales Invoice has been {state.lower()} successfully with the below details:<br>"
        f"<b>Company:</b> {doc.company}<br>"
        f"<b>Customer:</b> {doc.customer}<br>"
        f"<b>Cost Center:</b> {doc.cost_center}<br>"
        f"<b>Linked Sales Invoice:</b> <a href='{sales_invoice_link}' target='_blank'>{doc.name}</a><br>"
        f"<b>Status:</b> {state}<br>"
        f"<b>Items:</b><br>{item_lines}"
    )

    send_notification(doc, "Billing Recipients", subject, message)

    # After sending notifications
    if current_status in notified_statuses:
        notified_statuses.remove(current_status)
        doc.db_set(
            "custom_notified_statuses",
            json.dumps(notified_statuses),
            update_modified=False,
        )
