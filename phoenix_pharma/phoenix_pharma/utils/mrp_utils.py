# your_app/your_module/utils/price_utils.py
import frappe
from frappe import _

from frappe.query_builder.functions import IfNull

@frappe.whitelist()
def fetch_mrp(args=None, item_code=None):
    """
    Fetch MRP based on customer, price_list, uom, batch_no and date.
    Called via frontend JS.
    """

    if isinstance(args, str):
        args = frappe.parse_json(args)

    if not item_code:
        frappe.throw(_("Item Code is required"))

    today = args.get("transaction_date") or frappe.utils.nowdate()

    ip = frappe.qb.DocType("Item Price")
    query = (
        frappe.qb.from_(ip)
        .select(ip.custom_mrp)
        .where(
            (ip.item_code == item_code)
            & (ip.price_list == args.get("price_list"))
            & (IfNull(ip.uom, "").isin(["", args.get("uom")]))
        )
        .orderby(ip.valid_from, order=frappe.qb.desc)
        .orderby(IfNull(ip.batch_no, ""), order=frappe.qb.desc)
        .limit(1)
    )

    if args.get("customer"):
        query = query.where(ip.customer == args.get("customer"))
    else:
        query = query.where(IfNull(ip.customer, "") == "")

    if args.get("batch_no"):
        query = query.where(IfNull(ip.batch_no, "") == args.get("batch_no"))

    query = query.where(
        (IfNull(ip.valid_from, "2000-01-01") <= today)
        & (IfNull(ip.valid_upto, "2500-12-31") >= today)
    )
    result = query.run(as_dict=True)

    if result and result[0].get("custom_mrp"):
        return frappe._dict({
            "custom_mrp": result[0]["custom_mrp"]
        })
    else:
        return frappe._dict({
            "custom_mrp": None
        })
