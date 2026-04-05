from erpnext.stock.doctype.purchase_receipt.purchase_receipt import PurchaseReceipt
from phoenix_pharma.phoenix_pharma.utils.control_number import (
    upsert_control_number,
    log_control_number_activity,
    update_return_qty,
)
import frappe

ALLOWED_ITEM_GROUPS = {"RM", "PM", "Active"}


class CustomPurchaseReceipt(PurchaseReceipt):
    def before_save(self):
        # Set QC flag based on return status and item requirements
        if self.is_return:
            self.custom_requires_quality_inspection = 0
            return
        else:
            self.custom_requires_quality_inspection = any(
                frappe.db.get_value(
                    "Item", item.item_code, "inspection_required_before_purchase"
                )
                for item in self.items
            )

        for item in self.items:
            item_group = frappe.db.get_value("Item", item.item_code, "item_group")
            if item_group in ALLOWED_ITEM_GROUPS:
                try:
                    item.custom_control_number = upsert_control_number(
                        item, self, item.get("custom_control_number")
                    )
                except Exception as e:
                    frappe.log_error(
                        f"Control Number Error on save for {item.item_code}, PR: {self.name}, PR Item: {item.name}",
                        str(e),
                    )

    # to save ARN to the control number doing on_submit
    # * Note: From QI server script "Update Assay, LOD, retest date in CN" to update assay and lod to control number
    def on_submit(self):
        super().on_submit()
        if not self.is_return:
            for item in self.items:
                item_group = frappe.db.get_value("Item", item.item_code, "item_group")
                if item_group in ALLOWED_ITEM_GROUPS:
                    try:
                        control_number_name = item.custom_control_number or None
                        upsert_control_number(item, self, control_number_name)
                        log_control_number_activity(item, self, control_number_name)
                    except Exception as e:
                        frappe.log_error(
                            f"Control Number Error on submission for {item.item_code}, PR: {self.name}, PR Item: {item.name}",
                            str(e),
                        )
        elif self.is_return:
            for item in self.items:
                item_group = frappe.db.get_value("Item", item.item_code, "item_group")
                if item_group in ALLOWED_ITEM_GROUPS:
                    try:
                        # new function for is_return only during submission
                        # it should add in returned qty and reduce in item_qty
                        # append row in the child table for each return request against the CN and handle cancel
                        control_number_name = item.custom_control_number or None
                        update_return_qty(item, self, control_number_name)
                    except Exception as e:
                        frappe.log_error(
                            f"Control Number Error on submission for {item.item_code}, Return PR: {self.name}, Return PR: {item.name}",
                            str(e),
                        )

    def on_cancel(self):
        # call super so that all pre existing logic of the parent class runs first since we are overriding
        super().on_cancel()
        if not self.is_return:
            for item in self.items:
                item_group = frappe.db.get_value("Item", item.item_code, "item_group")
                if item_group in ALLOWED_ITEM_GROUPS:
                    try:
                        control_number_name = item.custom_control_number or None
                        upsert_control_number(item, self, control_number_name)
                        log_control_number_activity(item, self, control_number_name)
                    except Exception as e:
                        frappe.log_error(
                            f"Control Number Error on cancellation for {item.item_code}, PR: {self.name}, PR Item: {item.name}",
                            str(e),
                        )
        elif self.is_return:
            for item in self.items:
                item_group = frappe.db.get_value("Item", item.item_code, "item_group")
                if item_group in ALLOWED_ITEM_GROUPS:
                    try:
                        control_number_name = item.custom_control_number or None
                        update_return_qty(item, self, control_number_name)
                    except Exception as e:
                        frappe.log_error(
                            f"Control Number Error on cancellation for {item.item_code}, Return PR: {self.name}, Return PR: {item.name}",
                            str(e),
                        )

    def validate(self):
        super().validate()
        if self.is_return and self.amended_from:
            frappe.throw(
                "Do not Amend a Purchase Return. Please Cancel the incorrect Purchase Return and create another one against the original receipt.",
                title="Invalid Return",
            )

    def before_insert(self):
        # clear control number for PR items except for Purchase Return
        if not self.is_return:
            for item in self.items:
                item_group = frappe.db.get_value("Item", item.item_code, "item_group")
                if item_group in ALLOWED_ITEM_GROUPS:
                    if item.custom_control_number:
                        item.custom_control_number = None

    def after_delete(self):
        if (
            not self.is_return
        ):  # CN will not be deleted when a Purchase return is deleted
            for item in self.get("items", []):
                cn_name = item.get("custom_control_number")
                if not cn_name:
                    continue

                try:
                    # Fetch Control Number doc
                    cn_doc = frappe.get_doc("Control Number", cn_name)
                    if len(cn_doc.control_number_activity) == 0 or (
                        len(cn_doc.control_number_activity) == 1
                        and cn_doc.control_number_activity[0].child_row_name
                        == item.name
                    ):
                        # Only this item is using the CN → delete CN
                        frappe.delete_doc(
                            "Control Number", cn_name, ignore_permissions=True
                        )
                        frappe.msgprint(f"Control Number {cn_name} deleted.")
                    else:
                        # Other rows still reference the CN → raise error, prevent deletion
                        frappe.throw(
                            f"Cannot delete this Purchase Receipt because Control Number <b>{cn_name}</b> "
                            f"is still linked to other documents or entries."
                        )

                except frappe.DoesNotExistError:
                    pass  # CN already deleted
                except Exception as e:
                    frappe.log_error(
                        f"Error in after_delete cleanup for {cn_name} and item {item.item_code}",
                        str(e),
                    )

        # handle is_return after handling double save issue due to notifications
