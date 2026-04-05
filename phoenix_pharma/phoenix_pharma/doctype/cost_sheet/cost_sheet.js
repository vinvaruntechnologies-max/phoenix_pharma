// Copyright (c) 2024, Navin R C and contributors
// For license information, please see license.txt
let total_cash_inflow = -1;
let cost_per_unit = 0;
let cost_per_ = 0;
frappe.ui.form.on("Cost Sheet", {
  refresh: function (frm) {
    frm.set_query("item_code", "raw_materials", function (doc, cdt, cdn) {
      return {
        filters: {
          //TODO: add colors, flavours, in active, excipients, solvents
          item_group: ["in", ["RM", "Active"]],
        },
      };
    });
    frm.set_query("item_code", "packing_materials", function (doc, cdt, cdn) {
      return {
        filters: {
          item_group: "PM",
        },
      };
    });
  },
  validate: function (frm) {
    if (frm.save_disabled) {
      frappe.msgprint({
        message: __("Save is disabled. Please calculate the cost first."),
        indicator: "red",
      });
      frappe.validated = false; // Abort save operation
    }
  },
  item(frm) {
    clear_bom_list_defaults(frm);
  },
  select_raw_material_bom(frm) {
    clear_bom_list_required_defaults(frm);
  },
  select_packing_bom(frm) {
    clear_bom_list_required_defaults(frm);
  },
  costing_batch_size(frm) {
    clear_bom_list_required_defaults(frm);
  },
  costing_alternate_batch_size(frm) {
    clear_bom_list_required_defaults(frm);
  },
  unit(frm) {
    disable_save_button_with_tooltip(frm);
  },
  costing_with_custom_batch_size(frm) {
    frm.set_value("raw_materials", []);
    frm.set_value("packing_materials", []);
    // frm.set_value("raw_material_qty", 0);
    // frm.set_value("packing_material_qty", 0);
    // frm.set_value("total_material_qty", 0);
    frm.set_value("raw_material_cost", 0);
    frm.set_value("packing_material_cost", 0);
    frm.set_value("total_material_cost", 0);
    frm.set_value("average_weight", -1);
    frm.set_value("costing_batch_size", 0);
    frm.set_value("costing_alternate_batch_size", 0);
    disable_save_button_with_tooltip(frm);
  },
  type_of_formulation(frm) {
    if (
      frm.doc.type_of_formulation === "Tablets" ||
      frm.doc.type_of_formulation === "Capsules"
    ) {
      frm.set_df_property("average_weight", "label", "Average Weight");
    } else {
      frm.set_df_property(
        "average_weight",
        "label",
        "Fill Volume / Fill Weight"
      );
      frm.set_df_property(
        "average_weight_uom",
        "label",
        "Fill Volume / Fill Weight UOM"
      );
    }
    if (
      frm.doc.type_of_formulation === "Tablets" ||
      frm.doc.type_of_formulation === "Capsules"
    ) {
      //!Assuming input only KG converting to mg - hard coded
      frm.set_value("average_weight_uom", "mg");
    } else if (
      frm.doc.type_of_formulation === "Ointments" ||
      frm.doc.type_of_formulation === "Creams" ||
      frm.doc.type_of_formulation === "Gel"
    ) {
      frm.set_value("average_weight_uom", "KG");
    } else {
      frm.set_value("average_weight_uom", "Litre");
    }
    frm.refresh_field(" frm.doc.type_of_formulation");
  },
  process_loss_rm_(frm) {
    disable_save_button_with_tooltip(frm);
  },
  process_loss_pm_(frm) {
    disable_save_button_with_tooltip(frm);
  },
  testing_charges_rm(frm) {
    disable_save_button_with_tooltip(frm);
  },
  testing_charges_pm(frm) {
    disable_save_button_with_tooltip(frm);
  },
  testing_charges_finished_goods(frm) {
    disable_save_button_with_tooltip(frm);
  },
  rubber_stereos(frm) {
    disable_save_button_with_tooltip(frm);
  },
  foil_printing_artwork_block_and_film_making(frm) {
    disable_save_button_with_tooltip(frm);
  },
  development_charges(frm) {
    disable_save_button_with_tooltip(frm);
  },
  dpco_conversion_cost(frm) {
    disable_save_button_with_tooltip(frm);
  },
  profit_margin_(frm) {
    disable_save_button_with_tooltip(frm);
  },
  apply_profit_margin(frm) {
    disable_save_button_with_tooltip(frm);
  },

  retrieve_bom_for(frm) {
    if (!frm.doc.item) {
      frappe.msgprint({
        message: __("Select an item first"),
        indicator: "red",
      });
      return;
    }
    if (!frm.doc.retrieve_bom_for) {
      frappe.msgprint({
        message: __("Choose 'Retrieve BOM For' first"),
        indicator: "red",
      });
      return;
    }

    const filter_condition =
      frm.doc.retrieve_bom_for?.trim() === "Costing BOM"
        ? {
            custom_for_costing_only: "Yes",
            item: frm.doc.item,
            docstatus: ["!=", 2],
          }
        : {
            custom_for_costing_only: "No",
            item: frm.doc.item,
            docstatus: ["!=", 2],
          };

    frm.set_query("select_raw_material_bom", () => {
      return {
        filters: { custom_is_packing_bom: "No", ...filter_condition },
      };
    });
    frm.set_query("select_packing_bom", () => {
      return {
        filters: { custom_is_packing_bom: "Yes", ...filter_condition },
      };
    });
    frm.set_value("select_raw_material_bom", 0);
    frm.set_value("select_packing_bom", 0);
    clear_bom_list_defaults(frm);
  },

  retrieve_bom(frm) {
    disable_save_button_with_tooltip(frm);
    if (!frm.doc.item) {
      frappe.msgprint({
        message: __("Select an item first"),
        indicator: "red",
      });
      return;
    }

    if (!frm.doc.select_raw_material_bom) {
      frappe.msgprint({
        message: __("Choose Raw Material BOM first"),
        indicator: "red",
      });
      return;
    }

    if (!frm.doc.type_of_formulation) {
      frappe.msgprint({
        message: __("Choose Type Of Formulation first"),
        indicator: "red",
      });
      return;
    }

    if (!frm.doc.select_packing_bom) {
      frappe.msgprint({
        message: __("Choose Raw Material BOM first"),
        indicator: "red",
      });
      return;
    }
    frm.set_value("raw_materials", []);
    frm.set_value("packing_materials", []);

    const field_list = [
      "batch_size",
      "alternate_batch_size",
      "costing_batch_size",
      "costing_alternate_batch_size",
    ];

    validate_fields(frm, field_list,  frm.doc.costing_with_custom_batch_size === 1);

    let raw_material_cost = 0;
    let packing_material_cost = 0;
    let total_material_cost = 0;

    // let raw_material_qty = 0;
    // let packing_material_qty = 0;
    // let total_material_qty = 0;

    // Fetch and populate child items from each BOM
    const fetch_bom_details = (frm, bom_name, is_packing) => {
      let average_weight = 0;
      let pm_bom_qty = frm.doc.alternate_batch_size;
      let rm_bom_qty = frm.doc.batch_size;
      let costing_rm_qty = frm.doc.costing_batch_size;
      let costing_pm_qty = frm.doc.costing_alternate_batch_size;

      let batch_size_rm_conversion_factor =
        costing_rm_qty && costing_rm_qty > 0 ? costing_rm_qty / rm_bom_qty : 1;
      let batch_size_pm_conversion_factor =
        costing_pm_qty && costing_pm_qty > 0 ? costing_pm_qty / pm_bom_qty : 1;

      frappe.call({
        method: "frappe.client.get",
        args: {
          doctype: "BOM",
          name: bom_name,
        },
        callback: function (res) {
          const bom_data = res.message;
          if (bom_data && bom_data.items) {
            bom_data.items.forEach((item) => {
              let entry = frm.add_child(
                is_packing ? "packing_materials" : "raw_materials"
              );
              entry.item_code = item.item_code;
              entry.item_name = item.item_name;
              entry.qty =
                item.qty *
                (is_packing
                  ? batch_size_pm_conversion_factor
                  : batch_size_rm_conversion_factor);
              entry.uom = item.uom;
              entry.rate = item.rate;
              entry.custom_freight = item.custom_freight;
              entry.amount = (item.rate + item.custom_freight) * entry.qty;
              entry.conversion_factor = item.conversion_factor;
              entry.stock_qty = item.stock_qty;
              entry.stock_uom = item.stock_uom;
              entry.operation = item.operation;
              entry.bom_no = item.bom_no;
              entry.source_warehouse = item.source_warehouse;
              entry.do_not_explode = item.do_not_explode;
              entry.custom_include_in_avg_wt_ = item.custom_include_in_avg_wt_;
              // calculation for materials summary on retrieval
              if (is_packing) {
                packing_material_cost += entry.amount;
                //packing_material_qty += entry.qty;
              } else {
                raw_material_cost += entry.amount;
                //raw_material_qty += entry.qty;
                // average weight / fill wt calculation
                if (item.custom_include_in_avg_wt_ === 1)
                  average_weight += entry.qty;
              }
            });

            total_material_cost = raw_material_cost + packing_material_cost;
            //total_material_qty = raw_material_qty + packing_material_qty;

            //Average wt calculation
            let actual_batch_size =
              frm.doc.costing_with_custom_batch_size === 1
                ? frm.doc.costing_batch_size
                : bom_data.quantity;
            let actual_average_weight =
              frm.doc.costing_with_custom_batch_size === 1
                ? frm.doc.costing_batch_size /
                  frm.doc.costing_alternate_batch_size
                : bom_data.quantity / frm.doc.alternate_batch_size;
            if (
              frm.doc.type_of_formulation === "Tablets" ||
              frm.doc.type_of_formulation === "Capsules"
            ) {
              //!Assuming input only KG converting to mg
              average_weight = (average_weight / actual_batch_size) * 1000000;
              //!Assuming input only KG converting to mg - hard coded
              frm.set_value("average_weight_uom", "mg");
            } else if (
              frm.doc.type_of_formulation === "Ointments" ||
              frm.doc.type_of_formulation === "Creams" ||
              frm.doc.type_of_formulation === "Gel"
            ) {
              average_weight = actual_average_weight * 1000;
              frm.set_value("average_weight_uom", "KG");
            } else {
              average_weight = actual_average_weight * 1000;
              frm.set_value("average_weight_uom", "Litre");
            }
            frm.set_value("average_weight", average_weight);
            frm.refresh_field("average_weight");
            frm.refresh_field(
              is_packing ? "packing_materials" : "raw_materials"
            );
            // frm.set_value("raw_material_qty", raw_material_qty);
            // frm.set_value("packing_material_qty", packing_material_qty);
            // frm.set_value("total_material_qty", total_material_qty);
            frm.set_value("raw_material_cost", raw_material_cost);
            frm.set_value("packing_material_cost", packing_material_cost);
            frm.set_value("total_material_cost", total_material_cost);
            // frm.refresh_field("raw_material_qty");
            // frm.refresh_field("packing_material_qty");
            // frm.refresh_field("total_material_qty");
            frm.refresh_field("raw_material_cost");
            frm.refresh_field("packing_material_cost");
            frm.refresh_field("total_material_cost");
          }
          if (!is_packing) {
            frm.set_value("label_claim_type", bom_data.custom_claim_type);
            frm.set_value("label_claim", []);
            if (
              bom_data &&
              bom_data.custom_claim_items &&
              bom_data.custom_claim_items.length > 0
            ) {
              bom_data.custom_claim_items.forEach((item) => {
                let label_claim_entry = frm.add_child("label_claim");
                label_claim_entry.item = item.item;
                label_claim_entry.description = item.description;
                label_claim_entry.strength = item.strength;
                label_claim_entry.uom = item.uom;
              });
              frm.refresh_field("label_claim");
            } else {
              frappe.msgprint(
                __(
                  "There is no label claim details added for this product's raw material BOM"
                )
              );
            }
          }
        },
      });
    };
    fetch_bom_details(frm, frm.doc.select_packing_bom, true);
    fetch_bom_details(frm, frm.doc.select_raw_material_bom, false);
  },
  calculate_cost(frm) {
    cash_inflow = 0; // to indicate calculate cost button is clicked
    if (!frm.doc.unit) {
      frappe.msgprint({
        message: __("Enter 'unit' first under Product Details section"),
        indicator: "red",
      });
      return;
    }
    if (!frm.doc.alternate_batch_size_uom) {
      frappe.msgprint({
        message: __("Enter 'Alternate Batch Size UOM' first"),
        indicator: "red",
      });
      return;
    }
    if (
      !(frm.doc.raw_materials && frm.doc.packing_materials) ||
      (frm.doc.raw_materials.length === 0 &&
        frm.doc.packing_materials.length === 0)
    ) {
      frappe.msgprint({
        message: __(
          "BOM Items under Materials section are empty click 'Retrieve From BOM' again"
        ),
        indicator: "red",
      });
      return;
    }

    const field_list = [
      "process_loss_rm_",
      "process_loss_pm_",
      "process_loss_cost",
      "testing_charges_rm",
      "testing_charges_pm",
      "testing_charges_finished_goods",
      "rubber_stereos",
      "foil_printing_artwork_block_and_film_making",
      "development_charges",
      "dpco_conversion_cost",
      "profit_margin_",
      //"unit",
      "batch_size",
      "alternate_batch_size",
      "costing_batch_size",
      "costing_alternate_batch_size",
    ];
    validate_fields(frm, field_list);
    // Call calculate method from BE
    frappe.call({
      method:
        "phoenix_pharma.phoenix_pharma.doctype.cost_sheet.cost_sheet.calculate_cost",
      args: {
        data: {
          rm_cost: frm.doc.raw_material_cost,
          pm_cost: frm.doc.packing_material_cost,
          total_material_cost: frm.doc.total_material_cost,
          process_loss_rm: frm.doc.process_loss_rm_,
          process_loss_pm: frm.doc.process_loss_pm_,
          testing_charges_rm: frm.doc.testing_charges_rm,
          testing_charges_pm: frm.doc.testing_charges_pm,
          testing_charges_finished_goods:
            frm.doc.testing_charges_finished_goods,
          rubber_stereos: frm.doc.rubber_stereos,
          foil_printing_artwork_block_and_film_making:
            frm.doc.foil_printing_artwork_block_and_film_making,
          development_charges: frm.doc.development_charges,
          dpco_conversion_cost: frm.doc.dpco_conversion_cost,
          apply_profit_margin: frm.doc.apply_profit_margin,
          profit_margin_: frm.doc.profit_margin_,
          batch_size: frm.doc.batch_size,
          unit: frm.doc.unit,
        },
      },
      callback: (res) => {
        response = res.message;

        if (response) {
          total_cash_inflow = response.cash_inflow;
          const fieldsToUpdate = {
            process_loss_cost: response.process_loss_cost,
            total_cost_after_process_loss:
              response.total_cost_after_process_loss,
            total_before_profit_margin: response.total_before_profit_margin,
            total_before_profit_margin: response.total_before_profit_margin,
            profit_margin_rs: response.profit_margin_rs,
            net_total: response.net_total,
            cost_per_unit: response.cost_per_unit,
            cost_per: response.cost_per,
          };
          cost_per_unit = response.cost_per_unit;
          cost_per_ = response.cost_per;
          for (let field in fieldsToUpdate) {
            if (fieldsToUpdate.hasOwnProperty(field)) {
              frm.set_value(field, fieldsToUpdate[field]);
              frm.refresh_field(field); // Refresh to reflect the change immediately
            }
          }
        }
        frappe.msgprint("Cost Calculated 🤑🎉");
        frm.refresh(); // Refresh the form to fetch updated values
        enable_save_button(frm); // Re-enable the save button
      },
    });
  },
  cash_inflow(frm) {
    if (total_cash_inflow !== -1) {
      frappe.msgprint(
        __(`
        Total Cash Margin for the batch size of <b>${
          frm.doc.batch_size
        }</b> is: <b>${total_cash_inflow?.toFixed(
          2
        )} ₹</b> derived from Testing Charges, DPCO, Profit Margin, and Miscellaneous Charges.💰
        `)
      );
    } else {
      frappe.msgprint(
        __(`
          Please recalculate the cost
        `)
      );
    }
  },
  clear(frm) {
    clear_button(frm);
    frappe.msgprint("Cleared! 🤙");
    disable_save_button_with_tooltip(frm);
  },
});

// Function to disable the save button and add a tooltip
function disable_save_button_with_tooltip(frm) {
  const saveButton = document.querySelector('.btn-primary[data-label="Save"]');
  if (saveButton) {
    saveButton.disabled = true; // Disable the button
    saveButton.style.opacity = "0.6"; // Visual indication of being disabled
    saveButton.title = 'Save is disabled, "Calculate Cost" to enable it.'; // Tooltip message
  }
  // Prevent Save programmatically
  frm.save_disabled = true; // Custom flag to track disable state
}

// Function to enable the save button and remove the tooltip
function enable_save_button(frm) {
  const saveButton = document.querySelector('.btn-primary[data-label="Save"]');
  if (saveButton) {
    saveButton.disabled = false; // Re-enable the button
    saveButton.style.opacity = "1"; // Restore original style
    saveButton.title = ""; // Remove the tooltip
  }
  // Allow Save programmatically
  frm.save_disabled = false; // Clear the custom flag
}

function validate_fields(frm, field_list, zero_check = false) {
  let invalidFields = [];
  field_list.forEach((value) => {
    let value_to_check = frm.doc[value];

    // Check if the value is not a number or is less than 0
    if (
      typeof value_to_check !== "number" ||
      !isFinite(value_to_check) ||
      (!zero_check ? value_to_check < 0 : value_to_check <= 0)
    ) {
      invalidFields.push(value);
    }
  });

  if (invalidFields.length > 0) {
    // Prepare the error message with a list of invalid fields
    let errorMessage = "The following fields contain invalid values:<br>";
    invalidFields.forEach((field) => {
      errorMessage += `- ${field}<br>`;
    });

    // Show the error message in a single popup
    frappe.msgprint({ message: __(errorMessage), indicator: "red" });
    return;
  }
}

function clear_bom_list_defaults(frm) {
  frm.set_value("raw_materials", []);
  frm.set_value("packing_materials", []);
  // frm.set_value("raw_material_qty", 0);
  // frm.set_value("packing_material_qty", 0);
  // frm.set_value("total_material_qty", 0);
  frm.set_value("raw_material_cost", 0);
  frm.set_value("packing_material_cost", 0);
  frm.set_value("total_material_cost", 0);
  frm.set_value("batch_size", 0); //!fetch from field
  frm.set_value("uom", ""); //!fetch from field
  frm.set_value("alternate_batch_size", 0); //!fetch from field
  frm.set_value("alternate_batch_size_uom", ""); //!fetch from field
  frm.set_value("costing_batch_size", 0);
  frm.set_value("costing_alternate_batch_size", 0);
  //frm.set_value("average_weight", 0);
  frm.set_value("average_weight_uom", "");
  disable_save_button_with_tooltip(frm);
}

function clear_bom_list_required_defaults(frm) {
  frm.set_value("raw_materials", []);
  frm.set_value("packing_materials", []);
  // frm.set_value("raw_material_qty", 0);
  // frm.set_value("packing_material_qty", 0);
  // frm.set_value("total_material_qty", 0);
  frm.set_value("raw_material_cost", 0);
  frm.set_value("packing_material_cost", 0);
  frm.set_value("total_material_cost", 0);
  //frm.set_value("average_weight", 0);
  frm.set_value("average_weight_uom", "");
  disable_save_button_with_tooltip(frm);
}

function clear_button(frm) {
  frm.set_value("process_loss_rm_", 0);
  frm.set_value("process_loss_pm_", 0);
  frm.set_value("process_loss_cost", 0);
  frm.set_value("testing_charges_rm", 0);
  frm.set_value("testing_charges_pm", 0);
  frm.set_value("testing_charges_finished_goods", 0);
  frm.set_value("rubber_stereos", 0);
  frm.set_value("foil_printing_artwork_block_and_film_making", 0);
  frm.set_value("development_charges", 0);
  frm.set_value("dpco_conversion_cost", 0);
  frm.set_value("profit_margin_", 0);
  frm.set_value("profit_margin_rs", 0);
  frm.set_value("apply_profit_margin", 0);
  frm.set_value("total_cost_after_process_loss", 0);
  frm.set_value("total_before_profit_margin", 0);
  frm.set_value("net_total", 0);
  frm.set_value("cost_per_unit", 0);
  frm.set_value("cost_per", 0);
}

//TODO: make dpco a data field - done
//TODO: change unit label dynamically and move it below materials summary - done
//TODO: label claim dt new, should be a child table in cost sheet pulled from BOM - done
//TODO: for label claim - done
/**
 * Each tablets contains
 * and table below with item, strength, uom
 */
//TODO: make all rows read only except check box in pm and rm table, calculate avg weight - done
//TODO: average weight if type of forumlation is tablets or capsules else fill weight / fill volume will be selected - done
//TODO: create link fields for others in product details - done
//TODO: add checkbox to allow production BOM in cost sheet also and retrieve it, have to change the get query condition based on this in main frappe call - done
//TODO: actual earnings to company calculation shown with fields and values - can we show it in a table as key values and total? - done
//TODO: good to have is a clear button which clears the cost section fields, subtract the values in Toatal fields and reset entry fields to 0 - done
//TODO: form validation client side to be added for manual entry fields - done
//TODO: recalculate cost counter which increases if dependant fields are changed and clears on each button click to get latest cost - on_save - done
//-------------------
//TODO: Add pack style in BOM and fetch it in Cost sheet - done
//TODO: Keep 2 dropdowns, Select packing BOM and RM BOM for the item ( filter it based on dropdown on ui ), values are filtered based on Costing and Production dropdown value - done
//TODO: on clicking retrieve from BOM button, Batch size and uom from RM BOM selected and alt batch size and uom from packing BOM selected should be fetched and loaded - done
//TODO: retrieve the selected BOMs with calculations set with default batch sizes and post change in batch sizes should be retrieved again and recalculated, (button logic on change to be handled) - done
//TODO: FIX save button getting clickable on clicking retrieve from BOM - done
//--------------------
//TODO: BOM client scripts - done
//TODO: test full flow thorough - done
//TODO: Export as fixtures verify all fixtures and test locally on another bench site setup - done
//TODO: deploy to test and verify all - done
//TODO: load few BOMs and check - done
//TODO: fix issues priliminary
//---------------------------------------------------

//TODOs: for future enhancements v2
//TODO: CCPC list and group dt to be created for DPCO conversion factor calculation
//TODO: future DPCO - rm and pm separate
//TODO: Add on - client script to BOM doctype with set_query filters
// if custom_packing_material_bom = "Yes" then only Items with PM should come in dropdown
// if custom_packing_material_bom = "No" then only Items with RM, "Active"  should come in dropdown
// else by default only RM, PM, Active should come if custom_packing_material_bom is not selected ( initial form load )
//TODO: need script to add freight cost to amount in BOM dt row-wise
//TODO: highlight the missing mandatory field in the form for better ux
//TODO: Average wt conversion factor to change based on item level uom to mg
