from erpnext.controllers.taxes_and_totals import calculate_taxes_and_totals
import frappe
from erpnext.controllers.accounts_controller import get_taxes_and_charges
from frappe.model.naming import make_autoname


def purchase_order_set_taxes_and_totals(doc, events):
    try:
        # Prevent infinite recursion
        if getattr(doc, "flags", None) and getattr(doc.flags, "ignore_validate", False):
            return

        taxes_and_charges = get_taxes_and_charges(
            master_doctype="Purchase Taxes and Charges Template",
            master_name=doc.taxes_and_charges,
        )

        if taxes_and_charges:
            for row in taxes_and_charges:
                doc.append("taxes", row)

            # Calculate taxes after adding them
            calculate_taxes_and_totals(doc)
            # Set a flag to avoid infinite loop
            doc.flags.ignore_validate = True
            if not frappe.db.exists("Purchase Order", doc.name):
                frappe.db.commit()
    except Exception as e:
        # Log the error to ERPNext's Error Log
        error_message = f"PO {doc.name} failed: {str(e)}"
        frappe.log_error(error_message, "Purchase Order Processing Error")


# TODO:
# need to extend for Stock Entry type other than manufacture, or Job Card. if reqd.
def set_qi_naming_series(doc, method=None):
    # Fetch company and custom_abbrev in a single DB call
    if doc.reference_name and not doc.company:
        reference_doc = frappe.db.get_value(
            doc.reference_type,
            doc.reference_name,
            ["company", "custom_abbrev"],
            as_dict=True,
        )
        if reference_doc:
            doc.company = reference_doc.get("company")
            doc.custom_abbrev = reference_doc.get("custom_abbrev")

    # Fetch abbreviation from company if not already set
    if doc.company and not doc.custom_abbrev:
        doc.custom_abbrev = frappe.db.get_value("Company", doc.company, "abbr")

    suffix = "QI"  # Default suffix

    # Stock Entry of type 'Manufacture' – check finished item and fetch item_group from Item master
    if doc.reference_type == "Stock Entry" and doc.reference_name:
        stock_entry = frappe.get_doc("Stock Entry", doc.reference_name)
        if stock_entry.stock_entry_type == "Manufacture":
            for se_item in stock_entry.items:
                if se_item.is_finished_item:
                    item_group = (
                        frappe.db.get_value("Item", se_item.item_code, "item_group")
                        or ""
                    )
                    if item_group == "Finished Food Product":
                        suffix = "FFP"
                    elif item_group == "Finished Product":
                        suffix = "FP"
                    elif item_group == "Semi Finished Product":
                        suffix = "SFP"
                    else:
                        suffix = "OFP"
                    break  # Use first finished item only

    # If reference is Purchase Receipt
    elif doc.reference_type == "Purchase Receipt":
        suffix = "ARN"

    # Final naming series assignment
    if doc.custom_abbrev:
        doc.naming_series = f".{doc.custom_abbrev}.{suffix}.MM.YY."


# stock entry naming series
def set_se_naming_series(doc, method=None):
    if doc.company:
        reference_doc = frappe.db.get_value(
            "Company",
            doc.company,
            ["abbr"],
            as_dict=True,
        )
        abbr = ""
        if reference_doc:
            abbr = reference_doc.get("abbr")

    series_map = {
        "Material Issue": f".{abbr}.SEMIS.MM.YY.",
        "Material Receipt": f".{abbr}.SEMRT.MM.YY.",
        "Material Transfer": f".{abbr}.SEMTF.MM.YY.",
        "Manufacture": f".{abbr}.SEMFG.MM.YY.",
        "Repack": f".{abbr}.SERPK.MM.YY.",
        "Disassemble": f".{abbr}.SEDAS.MM.YY.",
        "Send to Subcontractor": f".{abbr}.SESSC.MM.YY.",
        "Material Transfer for Manufacture": f".{abbr}.SEMTM.MM.YY.",
        "Material Consumption for Manufacture": f".{abbr}.SEMCM.MM.YY.",
        "Destruction": f".{abbr}.SEDST.MM.YY.",
        "Preshipment Batch Creation": f".{abbr}.SEPSC.MM.YY.",
        "Preshipment Batch Deletion": f".{abbr}.SEPSD.MM.YY.",
    }

    if doc.stock_entry_type in series_map:
        doc.naming_series = series_map[doc.stock_entry_type]
    else:
        frappe.log_error(
            f"Stock Entry Type '{doc.stock_entry_type}' not mapped",
            "Naming Series Error",
        )
        frappe.throw("Unhandled Stock Entry Type. Please contact support.")


# material request naming series
def set_mr_naming_series(doc, method=None):
    if doc.company:
        reference_doc = frappe.db.get_value(
            "Company",
            doc.company,
            ["abbr"],
            as_dict=True,
        )
        abbr = ""
        if reference_doc:
            abbr = reference_doc.get("abbr")

    series_map = {
        "Purchase": f".{abbr}.MRPRC.MM.YY.",
        "Material Transfer": f".{abbr}.MRMTR.MM.YY.",
        "Material Issue": f".{abbr}.MRMIS.MM.YY.",
        "Manufacture": f".{abbr}.MRMFG.MM.YY.",
        "Customer Provided": f".{abbr}.MRCPR.MM.YY.",
    }

    if doc.material_request_type in series_map:
        doc.naming_series = series_map[doc.material_request_type]
    else:
        frappe.log_error(
            f"Material Request Type '{doc.material_request_type}' not mapped",
            "Naming Series Error",
        )
        frappe.throw("Unhandled Material Request Type. Please contact support.")


# bom naming
def set_bom_naming_series(doc, method=None):
    if doc.company:
        reference_doc = frappe.db.get_value(
            "Company",
            doc.company,
            ["abbr"],
            as_dict=True,
        )
        abbr = ""
        if reference_doc:
            abbr = reference_doc.get("abbr")
        if abbr and doc.item:
            naming_series = f".{abbr}.-BOM-.{doc.item}.-.###"
            doc.name = make_autoname(naming_series)
            doc.flags.name_set = True


# work order naming
def set_wo_naming_series(doc, method=None):
    if doc.company:
        reference_doc = frappe.db.get_value(
            "Company",
            doc.company,
            ["abbr"],
            as_dict=True,
        )
        abbr = ""
        if reference_doc:
            abbr = reference_doc.get("abbr")
        if abbr:
            doc.naming_series = f".{abbr}.-WO-.MM.YY.-.#####"


# job card naming
def set_jc_naming_series(doc, method=None):
    if doc.company:
        reference_doc = frappe.db.get_value(
            "Company",
            doc.company,
            ["abbr"],
            as_dict=True,
        )
        abbr = ""
        if reference_doc:
            abbr = reference_doc.get("abbr")
        if abbr:
            doc.naming_series = f".{abbr}.-JOB-.#####"


# pick list naming
def set_pl_naming_series(doc, method=None):
    if doc.company:
        reference_doc = frappe.db.get_value(
            "Company",
            doc.company,
            ["abbr"],
            as_dict=True,
        )
        abbr = ""
        if reference_doc:
            abbr = reference_doc.get("abbr")
        if abbr:
            doc.naming_series = f".{abbr}.-PICK-.MM.YY.-.#####"


# production plan naming
def set_pp_naming_series(doc, method=None):
    if doc.company:
        reference_doc = frappe.db.get_value(
            "Company",
            doc.company,
            ["abbr"],
            as_dict=True,
        )
        abbr = ""
        if reference_doc:
            abbr = reference_doc.get("abbr")
        if abbr:
            doc.naming_series = f".{abbr}.-PP-.MM.YY.-.#####"


# sales invoice naming
def set_si_naming_series(doc, method=None):
    def get_abbr(company):
        return frappe.db.get_value("Company", company, "abbr")

    def get_warehouse_code(warehouse):
        return frappe.db.get_value("Warehouse", warehouse, "custom_warehouse_code")

    abbr = get_abbr(doc.company) if doc.company else ""
    wh_code = get_warehouse_code(doc.set_warehouse) if doc.set_warehouse else ""

    # Helper to format the naming series
    def format_series(prefix, code):
        return f".{code}.{prefix}.MM.YY.#####"

    # Determine naming series based on conditions
    if doc.is_return:
        if abbr:
            doc.naming_series = format_series("SCN", abbr)  # Credit Note
    elif doc.is_debit_note:
        if abbr:
            doc.naming_series = format_series("SDN", abbr)  # Debit Note
    elif wh_code:
        export_type = doc.get("custom_domestic_or_export", "").strip()
        if export_type == "Domestic":
            doc.naming_series = format_series("SD", wh_code)
        elif export_type == "Export":
            doc.naming_series = format_series("SE", wh_code)
        else:
            doc.naming_series = format_series("SI", wh_code)


# Delivery Note / Preshipment invoice naming
def set_dn_naming_series(doc, method=None):
    def get_warehouse_code(warehouse):
        return frappe.db.get_value("Warehouse", warehouse, "custom_warehouse_code")

    wh_code = get_warehouse_code(doc.set_warehouse) if doc.set_warehouse else ""

    # Helper to format the naming series
    def format_series(prefix, code):
        return f".{code}.{prefix}.MM.YY.#####"

    # Determine naming series based on conditions
    if doc.is_return:
        if wh_code:
            doc.naming_series = format_series("RET", wh_code)  # Return
    else:
        if wh_code:
            doc.naming_series = format_series("PRE", wh_code)  # Preshipment / DN naming

#! revert batch naming by item - batch id as its causing complications in link fields
# batch naming
# def set_batch_naming_series(doc, method=None):
#     if doc.batch_id and doc.item:
#         doc.name = f"{doc.item}-{doc.batch_id}"
#         doc.flags.name_set = True

#         # Optional uniqueness check
#         if frappe.db.exists("Batch", doc.name):
#             frappe.throw(
#                 f"A batch with name {doc.name} already exists for the item {doc.item}. Please use a unique Batch ID. per item"
#             )
