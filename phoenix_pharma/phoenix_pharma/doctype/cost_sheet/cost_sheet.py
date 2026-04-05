# Copyright (c) 2024, Navin R C and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class CostSheet(Document):
    pass


@frappe.whitelist()
def calculate_cost(data):
    data = frappe.parse_json(data)
    rm_cost = float(data.get("rm_cost", 0))
    pm_cost = float(data.get("pm_cost", 0))
    total_material_cost = float(data.get("total_material_cost", 0))
    process_loss_rm = float(data.get("process_loss_rm", 0))
    process_loss_pm = float(data.get("process_loss_pm", 0))
    testing_charges_rm = float(data.get("testing_charges_rm", 0))
    testing_charges_pm = float(data.get("testing_charges_pm", 0))
    testing_charges_finished_goods = float(
        data.get("testing_charges_finished_goods", 0)
    )
    rubber_stereos = float(data.get("rubber_stereos", 0))
    foil_printing_artwork_block_and_film_making = float(
        data.get("foil_printing_artwork_block_and_film_making", 0)
    )
    development_charges = float(data.get("development_charges", 0))
    dpco_conversion_cost = float(data.get("dpco_conversion_cost", 0))
    apply_profit_margin = data.get("apply_profit_margin", 0)
    profit_margin_ = float(data.get("profit_margin_", 0))
    batch_size = float(data.get("batch_size", 0))
    unit = float(data.get("unit", 0))

    net_total = 0
    # Calculate process loss = process loss % on rm + process loss % on pm
    process_loss_cost = calculate_percentage_on_total(
        rm_cost, process_loss_rm
    ) + calculate_percentage_on_total(pm_cost, process_loss_pm)
    total_cost_after_process_loss = total_material_cost + process_loss_cost
    total_before_profit_margin = total_cost_after_process_loss + (
        +testing_charges_rm
        + testing_charges_pm
        + testing_charges_finished_goods
        + rubber_stereos
        + foil_printing_artwork_block_and_film_making
        + development_charges
        + dpco_conversion_cost
    )
    profit_margin_rs = 0
    if apply_profit_margin:
        profit_margin_rs = calculate_percentage_on_total(
            total_cost_after_process_loss, profit_margin_
        )
    else:
        profit_margin_rs = calculate_percentage_on_total(
            total_before_profit_margin, profit_margin_
        )

    net_total = total_before_profit_margin + profit_margin_rs
    if batch_size != 0:
        cost_per_unit = net_total / batch_size
    else:
        cost_per_unit = 0
    cost_per = net_total / batch_size * unit
    cash_inflow = (
        testing_charges_rm
        + testing_charges_pm
        + testing_charges_finished_goods
        + rubber_stereos
        + foil_printing_artwork_block_and_film_making
        + development_charges
        + dpco_conversion_cost
        + profit_margin_rs
    )
    # ? dependency check later - dpco_conversion_cost
    return {
        "process_loss_cost": process_loss_cost,
        "total_cost_after_process_loss": total_cost_after_process_loss,
        "total_before_profit_margin": total_before_profit_margin,
        "profit_margin_rs": profit_margin_rs,
        "net_total": net_total,
        "cost_per_unit": cost_per_unit,
        "cost_per": cost_per,
        "cash_inflow": cash_inflow
    }


def calculate_percentage_on_total(total, percentage):
    percentage_on_total = total * (percentage / 100)
    return percentage_on_total
