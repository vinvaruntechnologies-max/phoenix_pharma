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
                "Pending Purchase Review",
                "Pending Dir. Review",
                "Pending Production Review",
                "Pending QA Review",
                "Pending Stores Review",
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

    role_map = {
        "Pending Purchase Review": "Purchase Approver",
        "Pending Dir. Review": "Final Approver",
        "Pending Production Review": {
            "Puducherry - PBPL": "Production Approver Puducherry - PBPL",
            "Assam - PBPL": "Production Approver Assam - PBPL",
            "Assam - PL": "Production Approver Assam - PL",
        },
        "Pending QA Review": {
            "Puducherry - PBPL": "QA Approver Puducherry - PBPL",
            "Assam - PBPL": "QA Approver Assam - PBPL",
            "Assam - PL": "QA Approver Assam - PL",
        },
        "Pending Stores Review": {
            "Puducherry - PBPL": "Stores Approver Puducherry - PBPL",
            "Assam - PBPL": "Stores Approver Assam - PBPL",
            "Assam - PL": "Stores Approver Assam - PL",
        },
    }

    state = doc.workflow_state
    center = doc.cost_center
    role = None
    sales_order_link = frappe.utils.get_url_to_form("Sales Order", doc.name)
    if state in ["Pending Purchase Review", "Pending Dir. Review"]:
        role = role_map.get(state)
    elif state in role_map:
        center_role_map = role_map[state]
        role = center_role_map.get(center)

    if role:
        subject = f"{get_env_prefix()} Approval [Action]: {doc.custom_domestic_or_export or ''} Sales Order {doc.name} - {state}"
        message = (
            f"Hello,<br>"
            f"Approval Action Needed for the Sales Order<br>"
            f"<b>Company:</b> {doc.company}<br>"
            f"<b>Customer:</b> {doc.customer}<br>"
            f"<b>Cost Center:</b> {doc.cost_center}<br>"
            f"<b>Linked Sales Order:</b> <a href='{sales_order_link}' target='_blank'>{doc.name}</a><br>"
            f"<b>Status:</b> {state}<br>"
        )
        send_notification(doc, role, subject, message)

    # After sending notifications
    if current_status in notified_statuses:
        notified_statuses.remove(current_status)
        doc.db_set(
            "custom_notified_statuses",
            json.dumps(notified_statuses),
            update_modified=False,
        )


def on_submit(doc, method=None):
    production_role_map = {
        "Puducherry - PBPL": "Production Approver Puducherry - PBPL",
        "Assam - PBPL": "Production Approver Assam - PBPL",
        "Assam - PL": "Production Approver Assam - PL",
    }
    center = doc.cost_center
    role = None
    sales_order_link = frappe.utils.get_url_to_form("Sales Order", doc.name)
    role = production_role_map.get(center)
    if role:
        subject = f"{get_env_prefix()} Production [Action]: {doc.custom_domestic_or_export or ''} Sales Order {doc.name} - Submitted"
        message = (
            f"Hello,<br>"
            f"This SO is now submitted, Please create a new production plan for this sales order, Check the required raw materials and wait for the materials to be received before submitting the Production plan<br>"
            f"<b>Company:</b> {doc.company}<br>"
            f"<b>Customer:</b> {doc.customer}<br>"
            f"<b>Cost Center:</b> {doc.cost_center}<br>"
            f"<b>Linked Sales Order:</b> <a href='{sales_order_link}' target='_blank'>{doc.name}</a><br>"
            f"<b>Status:</b> Submitted<br>"
        )
        send_notification(doc, role, subject, message)

@frappe.whitelist()
def notify_role_for_mrp_update(sales_order_name):
    # Only notify in these workflow states
    states_to_notify_on_mrp_update = [
        "Pending Dir. Review",
        "Pending Production Review",
        "Pending QA Review",
        "Pending Stores Review",
        "Approved",
    ]

    # Fetch only necessary fields from Sales Order
    so = frappe.db.get_value(
        "Sales Order",
        sales_order_name,
        [
            "workflow_state",
            "cost_center",
            "company",
            "customer",
            "custom_domestic_or_export",
        ],
        as_dict=True,
    )

    if not so or so.workflow_state not in states_to_notify_on_mrp_update:
        return "No notification: not a notifyable state."

    center = so.cost_center
    roles_to_notify = {"Purchase Approver", "Final Approver"}

    # Role mapping based on workflow state and cost center
    role_map = {
        "Pending Production Review": {
            "Puducherry - PBPL": "Production Approver Puducherry - PBPL",
            "Assam - PBPL": "Production Approver Assam - PBPL",
            "Assam - PL": "Production Approver Assam - PL",
        },
        "Pending QA Review": {
            "Puducherry - PBPL": "QA Approver Puducherry - PBPL",
            "Assam - PBPL": "QA Approver Assam - PBPL",
            "Assam - PL": "QA Approver Assam - PL",
        },
        "Pending Stores Review": {
            "Puducherry - PBPL": "Stores Approver Puducherry - PBPL",
            "Assam - PBPL": "Stores Approver Assam - PBPL",
            "Assam - PL": "Stores Approver Assam - PL",
        },
    }

    # Add all applicable roles based on cost center
    for state_roles in role_map.values():
        if isinstance(state_roles, dict):
            role = state_roles.get(center)
            if role:
                roles_to_notify.add(role)

    # Get MRP table data
    items = frappe.db.get_all(
        "Sales Order Item",
        filters={"parent": sales_order_name},
        fields=["item_code", "item_name"],
    )

    item_rows = "".join(
        [f"<tr><td>{i.item_code}</td><td>{i.item_name}</td></tr>" for i in items]
    )
    item_table = f"""
        <table border='1' cellpadding='5' cellspacing='0'>
            <thead>
                <tr>
                    <th>Item Code</th>
                    <th>Item Name</th>
                </tr>
            </thead>
            <tbody>{item_rows}</tbody>
        </table>
    """

    updated_by = frappe.session.user
    subject = f"{get_env_prefix()} MRP Updated in Sales Order: {sales_order_name}"
    message = f"""
        Hello,<br>
        The MRP in Sales Order <b>{sales_order_name}</b> has been updated. Check the below SO for the updated value.<br><br>
        <b>Updated By:</b> {frappe.utils.get_fullname(updated_by)} ({updated_by})<br>
        <b>Company:</b> {so.company}<br>
        <b>Customer:</b> {so.customer}<br>
        <b>Cost Center:</b> {so.cost_center}<br>
        <b>Sales Order:</b> <a href="{frappe.utils.get_url_to_form("Sales Order", sales_order_name)}">{sales_order_name}</a><br><br>
        <b>MRP Updated for:</b><br>{item_table}
    """

    # Send notification and email for all resolved roles
    for role in roles_to_notify:
        send_notification(
            doc=frappe._dict(name=sales_order_name, doctype="Sales Order"),
            role=role,
            subject=subject,
            message=message,
        )

    return "Notification sent."
