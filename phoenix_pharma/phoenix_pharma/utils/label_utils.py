import frappe
from frappe import _
from frappe.utils import formatdate


def get_label_context(
    control_number_name: str,
    label_type: str,
    no_of_containers: int,
    date: str,
    arn_no: str,
    sample_size: str = "",
    arn_status: str = "",
    analysed_by: str = "",
):
    control = frappe.get_doc("Control Number", control_number_name)
    logo_url = frappe.db.get_value("Company", control.company, "company_logo")
    logo_url = frappe.utils.get_url() + logo_url if logo_url else ""
    mfg_date = None
    expiry_date = None
    formatted_date = None
    retest_date = None
    if control.mfg_date:
        mfg_date = formatdate(control.mfg_date, "dd-MM-yyyy")
    if control.expiry_date:
        expiry_date = formatdate(control.expiry_date, "dd-MM-yyyy")
    if date:
        formatted_date = formatdate(date, "dd-MM-yyyy")
    if control.retest_date:
        retest_date = formatdate(control.retest_date, "dd-MM-yyyy")

    context = {
        "label_type": label_type,
        "control_number": control.name,
        "item_name": control.item_name,
        "batch": control.batch,
        "mfg_date": mfg_date,
        "expiry_date": expiry_date,
        "quantity": control.item_quantity,
        "uom": control.item_uom,
        "no_of_containers": no_of_containers,
        "company": control.company,
        "doc_no": control.reference_name,
        "date": formatted_date,
        "supplier": control.supplier,
        "manufacturer": control.manufacturer,
        "arn_no": arn_no,
        "sample_size": sample_size,
        "arn_status": arn_status,
        "analysed_by": analysed_by,
        "assay": control.assay,
        "lod": control.lod,
        "retest_date": retest_date,
        "logo_url": logo_url,
    }
    return context


@frappe.whitelist()
def print_label(
    control_number_name: str,
    no_of_containers: int,
    label_type: str,
    date: str,
    arn_no: str = "",
    sample_size: str = "",
    arn_status: str = "",
    analysed_by: str = "",
):  # based on label_type change dimensions and context
    html = frappe.render_template(
        f"templates/includes/{label_type}.html",
        get_label_context(
            control_number_name,
            label_type,
            no_of_containers,
            date,
            arn_no,
            sample_size,
            arn_status,
            analysed_by,
        ),
    )
    frappe.local.response.filename = f"{label_type}_label_{control_number_name}.pdf"
    frappe.local.response.filecontent = frappe.utils.pdf.get_pdf(
        html,
        options={
            "margin-top": "0mm",
            "margin-bottom": "0mm",
            "margin-left": "0mm",
            "margin-right": "0mm",
            "page-width": "100mm",  # true 10 cm
            "page-height": "70mm",  # true 5 cm - changing to 70mm
            "encoding": "UTF-8",
        },
    )
    #!fix dimensions - actual print is having lot of whitespaces
    # 100.2 X 50.2 - label page size
    # 97 X 47 - table inside page
    frappe.local.response.type = "pdf"
