import frappe
import json
from phoenix_pharma.phoenix_pharma.utils.utils import (
    get_env_prefix,
    send_notification,
)


def before_insert(doc, method=None):
    if doc.amended_from:
        doc.custom_notified_statuses = json.dumps(
            ["Pending QA Review", "Pending Dir. Review"]
        )


def on_update(doc, method=None):
    # Load notified statuses from custom field
    notified_statuses = []
    if doc.custom_notified_statuses:
        try:
            notified_statuses = json.loads(doc.custom_notified_statuses)
        except Exception:
            pass  # Ignore malformed JSON

    current_status = doc.workflow_state
    if current_status not in notified_statuses:
        return  # Status already notified

    if not doc.company:
        frappe.throw(
            "Company is mandatory to send notifications. Please set the Company before proceeding, else contact support"
        )
    company = doc.company

    role_map = {
        "Pending Dir. Review": "Final Approver",
        "Pending QA Review": {
            "Phoenix Biologicals Private Limited": [
                "QA Approver Puducherry - PBPL",
                "QA Approver Assam - PBPL",
            ],
            "Phoenix Laboratories": ["QA Approver Assam - PL"],
        },
    }
    bom_link = frappe.utils.get_url_to_form("BOM", doc.name)
    role_dict = role_map.get(current_status)
    if current_status == "Pending QA Review":
        roles_list = role_dict.get(company)
        for role in roles_list:
            qa_subject = f"{get_env_prefix()} QA [Action]: QA approval needed for BOM : {doc.name} with status {current_status}"
            qa_message = (
                f"Hello QA Team,<br>"
                f"Please review the BOM created, verify everything and approve it for final approval<br>"
                f"<b>BOM:</b> <a href='{bom_link}' target='_blank'>{doc.name}</a><br>"
                f"<b>BOM Name:</b> {doc.custom_bom_no}<br>"
                f"<b>Status:</b> {current_status}<br>"
                f"<b>Company:</b> {company}<br>"
                f"<b>Item:</b> {doc.item}<br>"
                f"<b>Item Group:</b> {doc.custom_item_group}<br>"
            )
            send_notification(doc, role, qa_subject, qa_message)
    elif current_status == "Pending Dir. Review":
        subject = f"{get_env_prefix()} Dir. [Action]: Dir. approval needed for BOM : {doc.name} with status {current_status}"
        message = (
            f"Hello,<br>"
            f"Please review the BOM created, verify everything and approve it<br>"
            f"<b>BOM:</b> <a href='{bom_link}' target='_blank'>{doc.name}</a><br>"
            f"<b>BOM Name:</b> {doc.custom_bom_no}<br>"
            f"<b>Status:</b> {current_status}<br>"
            f"<b>Company:</b> {company}<br>"
            f"<b>Item:</b> {doc.item}<br>"
            f"<b>Item Group:</b> {doc.custom_item_group}<br>"
        )
        send_notification(doc, role_dict, subject, message)

    # After sending notifications
    if current_status in notified_statuses:
        notified_statuses.remove(current_status)
        doc.db_set(
            "custom_notified_statuses",
            json.dumps(notified_statuses),
            update_modified=False,
        )
