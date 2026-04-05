frappe.ui.form.on("Delivery Note", {
  validate: function (frm) {
    if(frm.doc.custom_domestic_or_export && frm.doc.custom_domestic_or_export === "Domestic") {
       frappe.throw({
        title: "Invalid Request",
        message: __(
          "Cannot raise Preshipment Invoice or Delivery Note for order type Domestic, raise Invoice directly by checking update stock option in Sales Invoice"
        ),
      });
    }
  },
  refresh: function (frm) {
    frm.set_query("set_warehouse", () => ({
      filters: [
        ["company", "=", frm.doc.company],
        ["is_group", "=", 0],
        ["warehouse_type", "=", "Billing"],
      ],
    }));
    toggle_preshipment_batch_column(frm);
  },

  // custom_port_country: function (frm) {
  //   frm.set_value("custom_port_of_discharge", null); // Reset selection
  //   set_port_filter(frm);
  // },

  custom_port_type: function (frm) {
    frm.set_value("custom_port_of_discharge", null); // Reset selection
    set_port_filter(frm);
  },

  onload_post_render: function (frm) {
    set_port_filter(frm); // Apply initial filter if values exist
  },

  custom_is_preshipment: toggle_preshipment_batch_column,
  onload: function (frm) {
    toggle_preshipment_batch_column(frm);
    frm.fields_dict["items"].grid.get_field(
      "custom_preshipment_batch_no"
    ).get_query = function (doc, cdt, cdn) {
      const row = locals[cdt][cdn];

      if (!row.item_code) {
        frappe.msgprint(
          "Please select Item Code before choosing Preshipment Batch"
        );
        return false;
      }

      return {
        filters: {
          item: row.item_code,
          // warehouse: row.warehouse, //TODO: use a be method to get batch tagged to correct warehouse and call it here to set warhouse filter
        },
      };
    };
  },
});
function toggle_preshipment_batch_column(frm) {
  frm.fields_dict["items"].grid.toggle_display(
    "custom_preshipment_batch_no",
    frm.doc.custom_is_preshipment
  );
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
