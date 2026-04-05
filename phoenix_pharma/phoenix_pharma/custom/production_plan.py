import frappe
import json
from phoenix_pharma.phoenix_pharma.utils.utils import get_env_prefix,send_notification

def before_insert(doc, method=None):
    if doc.amended_from:
        # Only notify once for submitted (1) and cancelled (2)
        doc.custom_notified_statuses = json.dumps([1, 2])

#TODO: handle cancelled code if required
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
    state = "Submitted" if current_status == 1 else "Cancelled"
    # Notify QA, prod, stores users based on cost center of Work Order
    qa_role_map = {
        "Puducherry - PBPL": "QA Approver Puducherry - PBPL",
        "Assam - PBPL": "QA Approver Assam - PBPL",
        "Assam - PL": "QA Approver Assam - PL",
    }
    production_plan_link = frappe.utils.get_url_to_form("Production Plan", doc.name)
    cost_center = doc.custom_cost_center
    if doc.docstatus in [1, 2]:
        # get SO rows
        so = frappe.db.get_all(
            "Production Plan Sales Order",
            filters={"parent": doc.name},
            fields=["sales_order", "customer", "sales_order_date"],
        )

        so_rows = "".join(
            [
                f"<tr><td>{i.sales_order}</td><td>{i.customer}</td><td>{i.sales_order_date}</td></tr>"
                for i in so
            ]
        )
        so_table = f"""
            <table border='1' cellpadding='5' cellspacing='0'>
                <thead>
                    <tr>
                        <th>SO</th>
                        <th>Customer</th>
                        <th>SO Date</th>
                    </tr>
                </thead>
                <tbody>{so_rows}</tbody>
            </table>
        """

        # get FG rows
        fg = frappe.db.get_all(
            "Production Plan Item",
            filters={"parent": doc.name},
            fields=["item_code", "planned_qty", "stock_uom", "bom_no"],
        )

        fg_rows = ""
        for i in fg:
            item_name = frappe.db.get_value("Item", i.item_code, "item_name") or ""
            fg_rows += (
                f"<tr><td>{i.item_code}</td><td>{item_name}</td><td>{i.planned_qty}</td>"
                f"<td>{i.stock_uom}</td><td>{i.bom_no}</td></tr>"
            )

        fg_table = f"""
            <table border='1' cellpadding='5' cellspacing='0'>
                <thead>
                    <tr>
                        <th>FG Item Code</th>
                        <th>FG Item Name</th>
                        <th>Qty to Mfg</th>
                        <th>UOM</th>
                        <th>BOM</th>
                    </tr>
                </thead>
                <tbody>{fg_rows}</tbody>
            </table>
        """

        # get SFG rows
        sfg = frappe.db.get_all(
            "Production Plan Sub Assembly Item",
            filters={"parent": doc.name},
            fields=["production_item", "item_name", "qty", "uom", "bom_no"],
        )

        sfg_rows = "".join(
            [
                f"<tr><td>{i.production_item}</td><td>{i.item_name}</td><td>{i.qty}</td><td>{i.uom}</td><td>{i.bom_no}</td></tr>"
                for i in sfg
            ]
        )
        sfg_table = f"""
            <table border='1' cellpadding='5' cellspacing='0'>
                <thead>
                    <tr>
                        <th>SF Item Code</th>
                        <th>SF Item Name</th>
                        <th>Qty to Mfg</th>
                        <th>UOM</th>
                        <th>BOM</th>
                    </tr>
                </thead>
                <tbody>{sfg_rows}</tbody>
            </table>
        """

        if cost_center:
            # Notify QA
            qa_role = qa_role_map.get(cost_center)
            if qa_role:
                subject = (
                    f"{get_env_prefix()} QA [Action]: A Production plan {doc.name} has been {state}"
                )
                message = (
                    f"Hello QA Team,<br>"
                    f"A Production Plan has been {state}, please create batch names for the items, configure and submit work order/s after verifying all the details ASAP or ignore if cancelled<br>"
                    f"<b>Status:</b> {state}<br>"
                    f"<b>Cost Center:</b> {cost_center}<br>"
                    f"<b>Linked Production Plan:</b> <a href='{production_plan_link}' target='_blank'>{doc.name}</a><br><br>"
                    f"<b>SO Details:</b> {so_table}<br><br>"
                    f"<b>Finished Product Items To Mfg.:</b><br> {fg_table}<br><br>"
                    f"<b>Semi Finished Items To Mfg.:</b><br> {sfg_table}"
                )
                send_notification(doc, qa_role, subject, message)

    # After sending notifications
    if current_status in notified_statuses:
        notified_statuses.remove(current_status)
        doc.db_set(
            "custom_notified_statuses",
            json.dumps(notified_statuses),
            update_modified=False,
        )
