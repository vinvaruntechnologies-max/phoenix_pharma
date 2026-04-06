import frappe
from frappe.model.document import Document


class BatchCOA(Document):
    def validate(self):
        self._validate_assay_lod()
        self._calculate_effective_purity()

    def before_save(self):
        self._calculate_effective_purity()

    def on_update(self):
        if self.status == "Approved" and not self.approved_by:
            self.db_set("approved_by", frappe.session.user, update_modified=False)
        if self.status == "Approved" and not self.approval_date:
            self.db_set("approval_date", frappe.utils.today(), update_modified=False)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _validate_assay_lod(self):
        if self.assay_percent is None or self.assay_percent <= 0:
            frappe.throw("Assay (%) must be greater than 0.")
        if self.assay_percent > 100:
            frappe.throw("Assay (%) cannot exceed 100.")
        if self.lod_percent is None or self.lod_percent < 0:
            frappe.throw("LOD (%) cannot be negative.")
        if self.lod_percent >= 100:
            frappe.throw("LOD (%) must be less than 100.")

        effective_purity = self.assay_percent * (100 - self.lod_percent) / 100
        if effective_purity <= 0:
            frappe.throw(
                f"Effective Purity calculated as {effective_purity:.4f}% — invalid. "
                "Check Assay and LOD values."
            )

    def _calculate_effective_purity(self):
        if self.assay_percent and self.lod_percent is not None:
            self.effective_purity = round(
                self.assay_percent * (100 - self.lod_percent) / 100, 4
            )
