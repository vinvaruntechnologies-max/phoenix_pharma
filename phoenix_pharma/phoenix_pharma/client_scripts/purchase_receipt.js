frappe.ui.form.on("Purchase Receipt", {
  //**Set manufacturer address in Purchase Receipt Item
  refresh: function (frm) {
    // Set query for selecting manufacturer address inside Purchase Order Item
    frm.fields_dict["items"].grid.get_field(
      "custom_select_manufacturer_address"
    ).get_query = function (doc, cdt, cdn) {
      let row = locals[cdt][cdn];

      if (!row.manufacturer) {
        return { filters: [] };
      }

      return {
        filters: [
          ["link_doctype", "=", "Manufacturer"],
          ["link_name", "=", row.manufacturer],
        ],
      };
    };

    frm.set_query("set_warehouse", () => ({
      filters: [
        ["company", "=", frm.doc.company],
        ["is_group", "=", 0],
        ["is_rejected_warehouse", "=", 0],
        ["warehouse_type", "in", ["Purchase", "External"]],
      ],
    }));

    frm.set_query("rejected_warehouse", () => ({
      filters: [
        ["company", "=", frm.doc.company],
        ["is_group", "=", 0],
        ["is_rejected_warehouse", "=", 1],
      ],
    }));
  },
  is_return: function (frm) {
    if (frm.is_new()) update_naming_series(frm);
  },
  before_save: function (frm) {
    if (frm.is_new()) update_naming_series(frm);
  },
});

function update_naming_series(frm) {
  if (!frm.doc.custom_abbrev) return;
  let abbr = frm.doc.custom_abbrev;
  let series = frm.doc.is_return
    ? `.${abbr}.PRT.MM..YY..###`
    : `.${abbr}.PR.MM..YY..####`;

  frm.set_value("naming_series", series);
}

frappe.ui.form.on("Purchase Receipt Item", {
  custom_print_label: function (frm, cdt, cdn) {
    const row = locals[cdt][cdn];
    if (!row.custom_control_number) {
      frappe.msgprint("Unable to print: Control Number not available.");
      return;
    }

    const control_number = row.custom_control_number || "";
    const label_type = "quarantine";
    const no_of_containers = row.custom__no_of_containers || "";
    const receipt_date = frm.doc.posting_date || "";
    if (!no_of_containers || no_of_containers <= 0) {
      frappe.msgprint(
        "Unable to print: No. of containers must be greater than 0."
      );
      return;
    }
    // DB existence check
    frappe.db
      .exists("Control Number", control_number)
      .then((exists) => {
        if (exists) {
          const url =
            `/api/method/phoenix_pharma.phoenix_pharma.utils.label_utils.print_label` +
            `?control_number_name=${encodeURIComponent(control_number)}` +
            `&no_of_containers=${encodeURIComponent(no_of_containers)}` +
            `&label_type=${encodeURIComponent(label_type)}` +
            `&date=${encodeURIComponent(receipt_date)}`;
          window.open(url);
        } else {
          frappe.msgprint("Unable to print: Control Number does not exist.");
        }
      })
      .catch(() => {
        frappe.msgprint("Error checking Control Number in the system.");
      });
  },
  // clear control number if an item row is duplicated in case
  items_add: function (frm, cdt, cdn) {
    const added_row = locals[cdt][cdn];
    const cn_name = added_row.custom_control_number;
    if (cn_name) {
      frappe.model.set_value(cdt, cdn, "custom_control_number", null);
    }
  },
  //**Set manufacturer address in Purchase Receipt Item
  custom_select_manufacturer_address: function (frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    //console.log("test")
    if (row.custom_select_manufacturer_address) {
      //console.log("custom_select_manufacturer_address")
      frappe.call({
        method: "frappe.client.get",
        args: {
          doctype: "Address",
          name: row.custom_select_manufacturer_address,
        },
        callback: function (r) {
          if (r.message) {
            //console.log("callback")
            let address = r.message;

            // Format full address for display
            // let address_html = `
            //               <b>${address.address_title || ""}</b><br>
            //               ${address.address_line1 || ""}<br>
            //               ${
            //                  address.address_line2
            //                   ? address.address_line2 + "<br>"
            //                   : ""
            //               }
            //               ${address.city || ""}, ${address.state || ""}<br>
            //               ${address.country || ""} - ${address.pincode || ""}
            //           `;
            // frm.cur_grid.grid_form.fields_dict.custom_manufacturer_address.html(address_html)
            // Set manufacturer location as State (or City if state is missing)
            let location = address.state ? address.state : address.city;
            frappe.model.set_value(
              cdt,
              cdn,
              "custom_manufacturer_and_location",
              location
            );
          }
        },
      });
    } else {
      frappe.model.set_value(cdt, cdn, "custom_manufacturer_address", "");
      frappe.model.set_value(cdt, cdn, "custom_manufacturer_and_location", "");
    }
  },
});
