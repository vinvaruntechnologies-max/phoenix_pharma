"""
API Purity Adjustment Utilities
================================
Handles effective purity calculation, adjusted quantity computation,
excipient compensation, and audit trail logging for GMP-compliant
batch-wise API consumption in Stock Entries.

Formula:
    Effective Purity (%) = Assay (%) × (100 − LOD %) / 100
    Adjusted Qty        = Required Qty / (Effective Purity / 100)
"""

import frappe
from frappe.utils import flt, nowdate, nowtime

# Item groups treated as API (purity adjustment applies)
API_ITEM_GROUPS = {"Active"}


# ---------------------------------------------------------------------------
# Core math
# ---------------------------------------------------------------------------

def calculate_effective_purity(assay: float, lod: float) -> float:
    """Return effective purity %. Raises ValueError on bad inputs."""
    if assay is None or lod is None:
        raise ValueError("Assay and LOD values are required.")
    if assay <= 0 or assay > 100:
        raise ValueError(f"Assay ({assay}) must be between 0 and 100 (exclusive).")
    if lod < 0 or lod >= 100:
        raise ValueError(f"LOD ({lod}) must be between 0 (inclusive) and 100 (exclusive).")
    purity = assay * (100 - lod) / 100
    if purity <= 0:
        raise ValueError(
            f"Effective Purity = {purity:.4f}% — invalid combination of Assay={assay}% and LOD={lod}%."
        )
    return round(purity, 6)


def calculate_adjusted_qty(required_qty: float, assay: float, lod: float) -> float:
    """Return qty of API needed to deliver required_qty of pure substance."""
    purity = calculate_effective_purity(assay, lod)
    return round(flt(required_qty) / (purity / 100), 6)


# ---------------------------------------------------------------------------
# COA lookup
# ---------------------------------------------------------------------------

def get_coa_for_batch(batch_no: str, item_code: str = None):
    """
    Return the latest Approved Batch COA for a batch, or None if not found.
    Prefers a COA that matches both batch_no and item_code when item_code is provided.
    """
    filters = {"batch_no": batch_no, "status": "Approved"}
    if item_code:
        filters["item_code"] = item_code

    records = frappe.get_all(
        "Batch COA",
        filters=filters,
        fields=["name", "assay_percent", "lod_percent", "effective_purity", "item_code"],
        order_by="test_date desc, creation desc",
        limit=1,
    )
    return records[0] if records else None


# ---------------------------------------------------------------------------
# Main adjustment entry point
# ---------------------------------------------------------------------------

def apply_purity_adjustment(doc):
    """
    Called from Stock Entry before_validate.
    For each API item (item_group in API_ITEM_GROUPS):
      - Fetch approved COA for the batch
      - Calculate adjusted qty
      - Store original qty, purity data on the item row
      - Optionally adjust an excipient to compensate excess weight
    Logs everything for GMP audit trail.
    """
    if doc.stock_entry_type not in [
        "Material Transfer for Manufacture",
        "Manufacture",
    ]:
        return

    adjustments = []
    total_excess = 0.0

    for item in doc.items:
        if item.get("is_finished_item"):
            continue

        item_group = frappe.db.get_value("Item", item.item_code, "item_group")
        if item_group not in API_ITEM_GROUPS:
            continue

        if not item.batch_no:
            frappe.msgprint(
                f"Item <b>{item.item_code}</b> has no Batch selected — purity adjustment skipped.",
                indicator="orange",
                alert=True,
            )
            continue

        coa = get_coa_for_batch(item.batch_no, item.item_code)
        coa_missing_action = doc.get("custom_coa_missing_action") or "Warn"

        if not coa:
            msg = (
                f"No approved COA found for batch <b>{item.batch_no}</b> "
                f"of item <b>{item.item_code}</b>. Purity adjustment skipped."
            )
            if coa_missing_action == "Block":
                frappe.throw(msg)
            else:
                frappe.msgprint(msg, indicator="orange", alert=True)
            continue

        assay = flt(coa.assay_percent)
        lod = flt(coa.lod_percent)

        try:
            effective_purity = calculate_effective_purity(assay, lod)
            original_qty = flt(item.qty)
            adjusted_qty = calculate_adjusted_qty(original_qty, assay, lod)
            excess = adjusted_qty - original_qty
            total_excess += excess

            # Write back to item row
            item.custom_coa_reference = coa.name
            item.custom_assay_percent = assay
            item.custom_lod_percent = lod
            item.custom_effective_purity = effective_purity
            item.custom_original_qty = original_qty
            item.custom_adjusted_qty = adjusted_qty
            item.qty = adjusted_qty

            adjustments.append({
                "item_code": item.item_code,
                "item_name": item.item_name,
                "batch_no": item.batch_no,
                "coa": coa.name,
                "assay": assay,
                "lod": lod,
                "effective_purity": effective_purity,
                "original_qty": original_qty,
                "adjusted_qty": adjusted_qty,
                "excess_qty": round(excess, 6),
            })

        except ValueError as e:
            frappe.throw(
                f"Purity calculation error for item <b>{item.item_code}</b> "
                f"batch <b>{item.batch_no}</b>: {e}"
            )

    if adjustments:
        _adjust_excipient(doc, total_excess)
        _write_audit_log(doc, adjustments)


# ---------------------------------------------------------------------------
# Excipient compensation
# ---------------------------------------------------------------------------

def _adjust_excipient(doc, total_excess: float):
    """
    Reduce excipient qty by total_excess to maintain batch weight.
    Mode is driven by custom_excipient_adjustment_mode on the Stock Entry:
      - "Single Excipient" : reduce the item set in custom_excipient_item
      - "Proportional"     : distribute reduction across all non-API, non-FG items
      - "None" / blank     : no adjustment (just log)
    """
    if total_excess <= 0:
        return

    mode = doc.get("custom_excipient_adjustment_mode") or "None"

    if mode == "Single Excipient":
        excipient_code = doc.get("custom_excipient_item")
        if not excipient_code:
            frappe.msgprint(
                "Excipient adjustment mode is 'Single Excipient' but no excipient item is set. "
                "Skipping excipient compensation.",
                indicator="orange",
                alert=True,
            )
            return
        for item in doc.items:
            if item.item_code == excipient_code and not item.get("is_finished_item"):
                original = flt(item.qty)
                new_qty = max(0, original - total_excess)
                item.custom_original_qty = item.custom_original_qty or original
                item.qty = round(new_qty, 6)
                frappe.msgprint(
                    f"Excipient <b>{excipient_code}</b> qty adjusted from "
                    f"{original} → {new_qty} (excess API: {total_excess})",
                    indicator="blue",
                    alert=True,
                )
                return
        frappe.msgprint(
            f"Excipient item <b>{excipient_code}</b> not found in items table. "
            "Skipping compensation.",
            indicator="orange",
            alert=True,
        )

    elif mode == "Proportional":
        excipient_items = [
            item for item in doc.items
            if not item.get("is_finished_item")
            and frappe.db.get_value("Item", item.item_code, "item_group") not in API_ITEM_GROUPS
        ]
        total_excipient_qty = sum(flt(i.qty) for i in excipient_items)
        if total_excipient_qty <= 0:
            return
        for item in excipient_items:
            share = flt(item.qty) / total_excipient_qty
            reduction = total_excess * share
            item.custom_original_qty = item.custom_original_qty or flt(item.qty)
            item.qty = round(max(0, flt(item.qty) - reduction), 6)


# ---------------------------------------------------------------------------
# Audit trail
# ---------------------------------------------------------------------------

def _write_audit_log(doc, adjustments: list):
    """Append a structured audit entry to custom_purity_adjustment_log on the SE."""
    lines = [
        f"[{nowdate()} {nowtime()}] Purity adjustment by {frappe.session.user}:"
    ]
    for a in adjustments:
        lines.append(
            f"  • {a['item_code']} | Batch: {a['batch_no']} | COA: {a['coa']} | "
            f"Assay: {a['assay']}% | LOD: {a['lod']}% | "
            f"Eff. Purity: {a['effective_purity']}% | "
            f"Qty: {a['original_qty']} → {a['adjusted_qty']} (Δ {a['excess_qty']})"
        )

    entry = "\n".join(lines)
    existing = doc.get("custom_purity_adjustment_log") or ""
    doc.custom_purity_adjustment_log = (existing + "\n\n" + entry).strip()


# ---------------------------------------------------------------------------
# Whitelisted API for frontend
# ---------------------------------------------------------------------------

@frappe.whitelist()
def get_purity_data_for_batch(batch_no: str, item_code: str = None):
    """
    Called from JS on batch selection.
    Returns COA data + calculated effective purity for real-time display.
    """
    coa = get_coa_for_batch(batch_no, item_code)
    if not coa:
        return {"found": False}

    try:
        purity = calculate_effective_purity(flt(coa.assay_percent), flt(coa.lod_percent))
    except ValueError as e:
        return {"found": True, "error": str(e)}

    return {
        "found": True,
        "coa": coa.name,
        "assay_percent": coa.assay_percent,
        "lod_percent": coa.lod_percent,
        "effective_purity": purity,
    }


@frappe.whitelist()
def calculate_adjusted_qty_api(required_qty: float, assay: float, lod: float):
    """Whitelisted endpoint for frontend real-time adjusted qty calculation."""
    try:
        adjusted = calculate_adjusted_qty(flt(required_qty), flt(assay), flt(lod))
        purity = calculate_effective_purity(flt(assay), flt(lod))
        return {"adjusted_qty": adjusted, "effective_purity": purity}
    except ValueError as e:
        frappe.throw(str(e))
