
frappe.ui.form.on("Sales Order", {
  refresh: function (frm) {
    frm.set_query("set_warehouse", () => ({
      filters: [
        ["company", "=", frm.doc.company],
        ["is_group", "=", 0],
        ["warehouse_type", "=", "Billing"],
      ],
    }));

    // Always hide by default
    frm.set_df_property("custom_update_mrp", "hidden", 1);
    // Show only for specific roles
    if (
      frappe.user.has_role("Purchase Approver") ||
      frappe.user.has_role("Final Approver")
    ) {
      frm.set_df_property("custom_update_mrp", "hidden", 0);
    }
  },
  //* can put the common logic similar to india compliance app and reuse in diff sales transactions for tax recalc if needed
  //* create utils for all sales transactions for item table to have only FG in refresh event type script
  cost_center: async function (frm) {
    await load_taxes(frm);
    apply_cost_center_to_items(frm);
  },
  company: async function (frm) {
    frm.set_value("cost_center", "");
    clear_taxes(frm);
  },
  customer: async function (frm) {
    if (frm.doc.gst_category === "Overseas")
      frm.set_value("custom_domestic_or_export", "Export");
    else frm.set_value("custom_domestic_or_export", "Domestic");
    frm.set_value("cost_center", "");
    clear_taxes(frm);
  },
  customer_address: async function (frm) {
    await load_taxes(frm);
  },
  gst_category: function (frm) {
    if (frm.doc.gst_category === "Overseas")
      frm.set_value("custom_domestic_or_export", "Export");
    else frm.set_value("custom_domestic_or_export", "Domestic");
  },
  is_export_with_gst: async function (frm) {
    if (frm.doc.is_export_with_gst && frm.doc.cost_center)
      await load_taxes(frm);
    else clear_taxes(frm);
  },
  tax_category: function (frm) {
    if (!frm.doc.customer) {
      frappe.msgprint(__("Please select a Customer first."));
      frm.set_value("tax_category", ""); // optional: clear selection
      return;
    }
    if (!frm.doc.cost_center) {
      frappe.msgprint(__("Please select a Cost Center first."));
      frm.set_value("tax_category", ""); // optional: clear selection
      return;
    }
  },
  custom_port_type: function (frm) {
    frm.set_value("custom_port_of_discharge", null); // Reset selection
    set_port_filter(frm);
  },

  onload_post_render: function (frm) {
    set_port_filter(frm); // Apply initial filter if values exist
  },
  //TODO:
  //* update MRP in linked work orders and sales invoices
  //* Mail all the approvers / receipeints about this MRP change (only after sales order document is submitted)
  //* https://docs.frappe.io/framework/user/en/api/utils#frappesendmail
  custom_update_mrp: function (frm) {
    refresh_all_mrp(frm);

    frappe.call({
      method:
        "phoenix_pharma.phoenix_pharma.custom.sales_order.notify_role_for_mrp_update",
      args: {
        sales_order_name: frm.doc.name,
      },
      callback: function (r) {
        if (!r.exc) {
          if (r.message === "Notification sent.")
            frappe.msgprint("Notification sent successfully.");
        }
      },
    });
  },
});

async function load_taxes(frm) {
  const { customer, cost_center, customer_address, gst_category } = frm.doc;
  if (!customer || !cost_center) return;

  clear_taxes(frm);
  frm.set_value("tax_category", "");
  frm.set_value("dispatch_address_name", "");
  frm.set_value("company_address", "");

  const map_result = await frappe.call({
    method: "phoenix_pharma.phoenix_pharma.utils.utils.get_cost_center_billing_map",
  });
  const cost_center_map = map_result.message || {};

  const billing_address_name = cost_center_map[cost_center];
  if (!billing_address_name) return;

  try {
    const company_address = await get_address(billing_address_name);
    frm.set_value("company_address", company_address.name);
    if (!frm.doc.dispatch_address_name) {
      frm.set_value("dispatch_address_name", company_address.name);
    }

    if (!customer_address) {
      frappe.throw({
        title: "Missing Address",
        message: __(
          "Customer address not found. Please add address and try again."
        ),
      });
    }

    if (!frm.doc.shipping_address_name) {
      frm.set_value("shipping_address_name", customer_address);
    }

    const customer_addr = await get_address(customer_address);
    const gst_state_customer = customer_addr.gst_state_number;
    const gst_state_company = company_address.gst_state_number;

    if (gst_category === "Registered Regular") {
      //* Always reverse charge is not applicable in Sales cycle
      select_tax_template(
        frm,
        gst_state_customer,
        gst_state_company,
        cost_center,
        false // isReverseCharge
      );
    } else if (gst_category === "Unregistered") {
      frappe.throw({
        title: "Invalid GST Category",
        message: __(
          "Unregistered customer GST category. Update in address and reselect Cost Center."
        ),
        indicator: "red",
      });
    } else if (gst_category === "Overseas") {
      select_tax_template(
        frm,
        "96-Other Countries",
        gst_state_company,
        cost_center,
        false // isReverseCharge
      );
    } else {
      frappe.msgprint({
        title: "GST Category Not Handled",
        message: __(
          "GST category in customer address is not supported. Contact support."
        ),
        indicator: "blue",
      });
    }
  } catch (err) {
    console.error("GST Template Selection Error:", err);
    frappe.msgprint(
      "Failed to select GST tax template. Please try again / contact support"
    );
  }
}

function select_tax_template(
  frm,
  customer_gst_state,
  company_gst_state,
  cost_center,
  isReverseCharge
) {
  if (!customer_gst_state || !company_gst_state) return;

  let tax_template = "";
  let tax_category = "";

  const isInState = customer_gst_state === company_gst_state;
  const prefix = isInState ? "In-state" : "Out-state";
  const rcm_prefix = isReverseCharge ? "RCM " : "";

  if (cost_center === "Assam - PL") {
    tax_template = `Output GST ${rcm_prefix}${prefix} - PL`;
    tax_category = `${isReverseCharge ? "Reverse Charge " : ""}${prefix} - PL`;
  } else if (cost_center === "Puducherry - PBPL") {
    tax_template = `Output GST ${rcm_prefix}${prefix} Pondy - PBPL`;
    tax_category = `${
      isReverseCharge ? "Reverse Charge " : ""
    }${prefix} Pondy - PBPL`;
  } else {
    tax_template = `Output GST ${rcm_prefix}${prefix} Assam - PBPL`;
    tax_category = `${
      isReverseCharge ? "Reverse Charge " : ""
    }${prefix} Assam - PBPL`;
  }

  // frm.set_value("tax_category", tax_category);
  //! forcing the user to select the filtered tax category to trigger scripts so that
  //! item tax template loads properly
  frm.set_query("tax_category", () => ({
    filters: [["name", "=", tax_category]],
  }));
  frm.set_value("taxes_and_charges", tax_template);
}

function clear_taxes(frm) {
  if (!frm.doc.customer) return;
  // Clear items table
  frm.clear_table("items");
  frm.refresh_field("items");
  frm.set_value("tax_category", "");
  frm.set_value("taxes_and_charges", "");
  frm.set_value("taxes", []);
  frm.set_value("total_taxes_and_charges", "");
}

// Utility to fetch GST state number from address name
async function get_address(address_name) {
  const res = await frappe.call({
    method: "frappe.client.get_list",
    args: {
      doctype: "Address",
      filters: { name: address_name },
      fields: ["name", "state", "gst_state_number"],
    },
  });

  if (res && res.message && res.message.length > 0) {
    return res.message[0];
  } else {
    throw `Address ${address_name} not found or missing GST details.`;
  }
}

//* mrp update
frappe.ui.form.on("Sales Order Item", {
  item_code: function (frm, cdt, cdn) {
    const domesticOrExport = frm.doc.custom_domestic_or_export;
    const isExportWithGST = frm.doc.is_export_with_gst;
    if (
      !frm.doc.tax_category &&
      (domesticOrExport === "Domestic" ||
        (domesticOrExport === "Export" && isExportWithGST))
    ) {
      frappe.msgprint("Please select a Tax Category before adding items.");
      frappe.model.set_value(cdt, cdn, "item_code", ""); // clear item_code
      return;
    }
    //let row = locals[cdt][cdn];
    let row = frappe.get_doc(cdt, cdn);
    if (!row.item_code) return;

    // setTimeout(() => {
    //   fetch_mrp_for_row(frm, row);
    // }, 300); // 300ms wait for ERPNext to finish fetching UOM
    setTimeout(() => {
      if (!row.uom) {
        // Retry once after another 200ms if uom still not loaded
        setTimeout(() => {
          fetch_mrp_for_row(frm, row);
        }, 200);
      } else {
        fetch_mrp_for_row(frm, row);
      }
    }, 300); // Initial 300ms wait
    apply_cost_center_to_items(frm);
  },
  // !observe how rate changes and enable below
  // customer: function(frm) {
  //     refresh_all_mrp(frm);
  // },
  // price_list: function(frm) {
  //     refresh_all_mrp(frm);
  // }
});

function fetch_mrp_for_row(frm, row) {
  if (!row.item_code) return;
  const args = {
    price_list: frm.doc.selling_price_list,
    customer: frm.doc.customer,
    batch_no: row.batch_no,
    uom: row.uom,
    transaction_date: frm.doc.transaction_date,
  };

  frappe.call({
    method: "phoenix_pharma.phoenix_pharma.utils.mrp_utils.fetch_mrp",
    args: { args, item_code: row.item_code },
    freeze: true,
    callback: function (r) {
      if (r.message) {
        frappe.model.set_value(
          row.doctype,
          row.name,
          "custom_mrp",
          r.message.custom_mrp
        );
      }
    },
  });
}

function refresh_all_mrp(frm) {
  frm.doc.items.forEach((row) => {
    fetch_mrp_for_row(frm, row);
  });
}

function apply_cost_center_to_items(frm) {
  if (!frm.doc.cost_center) return;

  (frm.doc.items || []).forEach((item) => {
    item.cost_center = frm.doc.cost_center;
  });
  frm.refresh_field("items");
}

function set_port_filter(frm) {
  frm.set_query("custom_port_of_discharge", () => {
    let filters = {};

    // if (frm.doc.custom_port_country) {
    //   filters["country"] = frm.doc.custom_port_country;
    // }
    if (frm.doc.custom_destination_country) {
      filters["country"] = frm.doc.custom_destination_country;
    }
    if (frm.doc.custom_port_type === "Seaport") {
      filters["seaport"] = 1;
    } else if (frm.doc.custom_port_type === "Airport") {
      filters["airport"] = 1;
    }

    return { filters };
  });
}
