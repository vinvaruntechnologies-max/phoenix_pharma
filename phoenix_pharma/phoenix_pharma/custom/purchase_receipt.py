import frappe
import json
from phoenix_pharma.phoenix_pharma.utils.utils import (
    get_env_prefix,
    send_notification,
)


def before_insert(doc, method=None):
    if doc.amended_from:
        doc.custom_notified_statuses = json.dumps(
            [
                "Pending Quality Review",
                "Pending Stores Review",
                "Pending Purchase Review",
            ]
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

    if not doc.cost_center:
        frappe.throw(
            "Cost Center is mandatory to send notifications. Please set the Cost Center before proceeding, else contact support"
        )
    cost_center = doc.cost_center

    qc_role_map = {
        "Puducherry - PBPL": "QC Approver Puducherry - PBPL",
        "Assam - PBPL": "QC Approver Assam - PBPL",
        "Assam - PL": "QC Approver Assam - PL",
    }
    stores_role_map = {
        "Puducherry - PBPL": "Stores Approver Puducherry - PBPL",
        "Assam - PBPL": "Stores Approver Assam - PBPL",
        "Assam - PL": "Stores Approver Assam - PL",
    }
    qa_role_map = {
        "Puducherry - PBPL": "QA Approver Puducherry - PBPL",
        "Assam - PBPL": "QA Approver Assam - PBPL",
        "Assam - PL": "QA Approver Assam - PL",
    }
    pr_link = frappe.utils.get_url_to_form("Purchase Receipt", doc.name)
    if doc.workflow_state == "Pending Quality Review":
        qc_role = qc_role_map.get(cost_center)
        qa_role = qa_role_map.get(cost_center)
        # Notify QC
        if qc_role:
            qc_subject = f"{get_env_prefix()} QC [Action]: QC Tests needed for Purchase Receipt: {doc.name} with status {doc.workflow_state}"
            qc_message = (
                f"Hello QC Team,<br>"
                f"Please raise Quality Inspection and generate RM/PM COA for Purchase Receipt. Once generated kindly approve the request / contact purchase in case of over receipt.<br>"
                f"<b>Purchase Receipt:</b> <a href='{pr_link}' target='_blank'>{doc.name}</a><br>"
                f"<b>Status:</b> {doc.workflow_state}<br>"
                f"<b>Company:</b> {doc.company}<br>"
                f"<b>Supplier:</b> {doc.supplier}<br>"
            )
            send_notification(doc, qc_role, qc_subject, qc_message)

        if qa_role:
            qa_subject = f"{get_env_prefix()} QA [Info]: A Purchase Receipt is sent for QC tests {doc.name} with status {doc.workflow_state}"
            qa_message = (
                f"Hello QA Team,<br>"
                f"FYI, QC team should raise the RM / PM COA for the required items W.R.T. this receipt and approve this to load the items balance into the stock ledger<br>"
                f"<b>Purchase Receipt:</b> <a href='{pr_link}' target='_blank'>{doc.name}</a><br>"
                f"<b>Status:</b> {doc.workflow_state}<br>"
                f"<b>Company:</b> {doc.company}<br>"
                f"<b>Supplier:</b> {doc.supplier}<br>"
            )
            send_notification(doc, qa_role, qa_subject, qa_message)

    if doc.workflow_state == "Pending Stores Review":
        stores_role = stores_role_map.get(cost_center)
        # Notify Stores Incharge
        if stores_role:
            stores_subject = f"{get_env_prefix()} Stores [Action]: Stores Review needed for Purchase Receipt: {doc.name} with status {doc.workflow_state}"
            stores_message = (
                f"Hello Stores Incharge,<br>"
                f"Stores user has raised the Purchase Receipt and its in Draft stage, kindly review and take action to move it to next stage.<br>"
                f"<b>Purchase Receipt:</b> <a href='{pr_link}' target='_blank'>{doc.name}</a><br>"
                f"<b>Status:</b> {doc.workflow_state}<br>"
                f"<b>Company:</b> {doc.company}<br>"
                f"<b>Supplier:</b> {doc.supplier}<br>"
            )
            send_notification(doc, stores_role, stores_subject, stores_message)

    if doc.workflow_state == "Pending Purchase Review":
        # Notify Stores Incharge
        purchase_subject = f"{get_env_prefix()} Purchase [Action]: Purchase Review needed for Purchase Receipt: {doc.name} with status {doc.workflow_state}"
        purchase_message = (
            f"Hello,<br>"
            f"Purchase user has raised the Purchase Receipt most likely for <b>cylinder</b> and its in Draft stage, kindly review and take action to approve.<br>"
            f"<b>Purchase Receipt:</b> <a href='{pr_link}' target='_blank'>{doc.name}</a><br>"
            f"<b>Status:</b> {doc.workflow_state}<br>"
            f"<b>Company:</b> {doc.company}<br>"
            f"<b>Supplier:</b> {doc.supplier}<br>"
        )
        send_notification(doc, "Purchase Approver", purchase_subject, purchase_message)

    # After sending notifications
    if current_status in notified_statuses:
        notified_statuses.remove(current_status)
        doc.db_set(
            "custom_notified_statuses",
            json.dumps(notified_statuses),
            update_modified=False,
        )
