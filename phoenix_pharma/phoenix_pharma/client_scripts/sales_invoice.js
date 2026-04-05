frappe.ui.form.on("Sales Invoice", {
  refresh: function (frm) {
    frm.set_query("set_warehouse", () => ({
      filters: [
        ["company", "=", frm.doc.company],
        ["is_group", "=", 0],
        ["warehouse_type", "=", "Billing"],
      ],
    }));
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
  setup: function (frm) {
    if (frm.doc.custom_domestic_or_export === "Domestic") {
      frm.set_value("update_stock", 1);
    }
  },
});

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
