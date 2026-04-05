import frappe
import json
from phoenix_pharma.phoenix_pharma.custom.helper import (
    handle_preshipment_batch_creation,
    handle_preshipment_batch_deletion,
)
#* not in use anymore as preshipment batch field alone is enough to generate print format
def validate(doc, method=None):
    if doc.custom_is_preshipment and doc.workflow_state in [
        "Draft",
        "Preshipment Generated",
    ]:
        for item in doc.items:
            item.db_set("batch_no", None)      # Clear safely during doc save


def before_insert(doc, method=None):
    if doc.amended_from:
        doc.custom_notified_statuses = json.dumps(
            ["Preshipment In Progress", "Preshipment Generated", "Completed"]
        )


def on_update(doc, method=None):
    notified_statuses = []
    if doc.custom_notified_statuses:
        try:
            notified_statuses = json.loads(doc.custom_notified_statuses)
        except Exception:
            pass

    current_status = doc.workflow_state
    if current_status not in notified_statuses:
        return

    if current_status == "Preshipment In Progress":
        handle_preshipment_batch_creation(doc)

    elif current_status == "Preshipment Generated":
        handle_preshipment_batch_deletion(doc)

    # Update notified statuses to avoid re-triggering
    notified_statuses.remove(current_status)
    doc.db_set(
        "custom_notified_statuses", json.dumps(notified_statuses), update_modified=False
    )
