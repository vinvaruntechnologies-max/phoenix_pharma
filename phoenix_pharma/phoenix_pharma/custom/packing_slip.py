import frappe


def on_submit(doc, method):
    update_delivery_note_with_packing(doc.name)


def on_cancel(doc, method):
    if doc.delivery_note:
        dn = frappe.get_doc("Delivery Note", doc.delivery_note)

        # Remove rows from custom_packaged_items linked to this Packing Slip
        dn.custom_packaged_items = [
            row
            for row in dn.custom_packaged_items
            if row.packing_slip_reference != doc.name
        ]

        dn.save(ignore_permissions=True)
        frappe.msgprint(f"Removed packing slip rows from Delivery Note {dn.name}")


@frappe.whitelist()
def update_delivery_note_with_packing(packing_slip_name):
    ps = frappe.get_doc("Packing Slip", packing_slip_name)

    for ps_item in ps.items:
        if not ps_item.dn_detail:
            continue  # skip if no linked DN item

        dn_parent = frappe.db.get_value(
            "Delivery Note Item", ps_item.dn_detail, "parent"
        )
        dn = frappe.get_doc("Delivery Note", dn_parent)

        # Create a new row in Delivery Note's custom_packaged_items
        row = dn.append("custom_packaged_items", {})
        row.packing_slip_reference = ps.name
        row.item_code = ps_item.item_code
        row.item_name = ps_item.item_name
        row.qty = ps_item.qty
        row.stock_uom = ps_item.stock_uom
        row.dn_item = ps_item.dn_detail
        row.batch = ps_item.batch_no
        row.from_package_no = ps.from_case_no
        row.to_package_no = ps.to_case_no
        row.no_of_unit_per_package = ps.custom_no_of_units_per_package
        row.noupp_uom = ps.custom_noupp_uom
        row.no_of_qty_per_package = ps.custom_no_of_qty_per_package_copy
        row.noqpp_uom = ps.custom_noqpp_uom
        row.net_weight = ps.custom_net_weight_pack
        row.net_weight_uom = ps.custom_net_weight_pack_uom
        row.gross_weight = ps.custom_gross_weight_pack
        row.gross_weight_uom = ps.custom_gross_weight_pack_uom

        if ps.from_case_no and ps.to_case_no:
            row.pack_nos_range = f"{ps.from_case_no} - {ps.to_case_no}"
        elif ps.from_case_no:
            row.pack_nos_range = f"{ps.from_case_no} - {ps.from_case_no}"
        else:
            row.pack_nos_range = ""

        dn.save(ignore_permissions=True)


@frappe.whitelist()
def get_batch_for_dn_item(dn_item_name):
    if not dn_item_name:
        return {}

    dn_item = frappe.db.get_value(
        "Delivery Note Item",
        dn_item_name,
        ["parent", "batch_no", "custom_preshipment_batch_no"],
        as_dict=True,
    )

    if not dn_item:
        return {}

    is_preshipment = frappe.db.get_value(
        "Delivery Note", dn_item.parent, "custom_is_preshipment"
    )

    return {
        "batch_no": dn_item.custom_preshipment_batch_no
        if is_preshipment
        else dn_item.batch_no
    }
