import frappe

def get_env_prefix():
    env = (frappe.conf.get("env") or "").strip().upper()
    if env == "TEST":
        return "[TESTING]"
    return ""  # default: no prefix


def get_users_by_role(role):
    return frappe.get_all(
        "Has Role", filters={"role": role}, fields=["parent as user"], distinct=True
    )


def get_active_users_by_role(role):
    users = get_users_by_role(role)
    return [
        user["user"]
        for user in users
        if frappe.db.get_value("User", user["user"], "enabled") == 1
    ]


def send_notification(doc, role, subject, message):
    if role == "Billing Recipients":
        users = frappe.conf.get("billing_recipients") or []
    else:
        users = get_active_users_by_role(role)
    # TODO:comment below and uncomment above if testing is done
    # users = ["navinrc98@icloud.com", "navintheboss1998@gmail.com"]
    for user_id in users:
        # * for email enable the below lines
        email = frappe.db.get_value("User", user_id, "email")
        # Email
        if email:
            frappe.sendmail(
                recipients=[email],
                subject=subject,
                message=message,
            )

        # Avoid duplicate system notifications
        if not frappe.db.exists(
            "Notification Log",
            {"subject": subject, "document_name": doc.name, "for_user": user_id},
        ):
            frappe.get_doc(
                {
                    "doctype": "Notification Log",
                    "subject": subject,
                    "email_content": message,
                    "type": "Alert",
                    "document_type": doc.doctype,
                    "document_name": doc.name,
                    "for_user": user_id,
                }
            ).insert(ignore_permissions=True)

@frappe.whitelist()
def get_warehouse_address(warehouse):
    try:
        # Get address linked to warehouse
        address_links = frappe.get_all("Dynamic Link",
            filters={
                "link_doctype": "Warehouse",
                "link_name": warehouse,
                "parenttype": "Address"
            },
            fields=["parent"]
        )
        
        if address_links:
            # Get active addresses only
            for link in address_links:
                address_doc = frappe.get_doc("Address", link.parent)
                if not address_doc.disabled:  # Check address is active
                    return address_doc.get_display()
            
            return "No active address found for this warehouse"
        else:
            return "No address found for this warehouse"
            
    except Exception as e:
        frappe.log_error(f"Error getting warehouse address: {str(e)}")
        return "Error fetching address"