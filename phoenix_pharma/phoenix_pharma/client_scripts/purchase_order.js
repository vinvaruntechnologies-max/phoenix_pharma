frappe.ui.form.on("Purchase Order", {
  refresh: function (frm) {
    // Set query for selecting manufacturer address inside Purchase Order Item
    //**client script: Set manufacturer address in PO Item
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
    warehouse_type = frm.doc.custom_send_to_external_warehouse
      ? "External"
      : "Purchase";
    frm.set_query("set_warehouse", () => ({
      filters: [
        ["company", "=", frm.doc.company],
        ["is_group", "=", 0],
        ["warehouse_type", "=", warehouse_type],
      ],
    }));
  },
  custom_send_to_external_warehouse: function (frm) {
    frm.set_value("set_warehouse", "");
    warehouse_type = frm.doc.custom_send_to_external_warehouse
      ? "External"
      : "Purchase";
    frm.set_query("set_warehouse", () => ({
      filters: [
        ["company", "=", frm.doc.company],
        ["is_group", "=", 0],
        ["warehouse_type", "=", warehouse_type],
      ],
    }));
  },
  set_warehouse: function (frm) {
    if (frm.doc.set_warehouse && frm.doc.custom_send_to_external_warehouse) {
      frappe.call({
        method:
          "phoenix_pharma.phoenix_pharma.utils.utils.get_warehouse_address",
        args: {
          warehouse: frm.doc.set_warehouse,
        },
        callback: function (r) {
          if (r.message) {
            frm.set_value(
              "custom_external_warehouse_address_display",
              html2text(r.message)
            );
          }
        },
      });
    } else {
      frm.set_value("custom_external_warehouse_address_display", "");
    }
  },
  //**client script: PO tax template selection based on cost center
  cost_center: function (frm) {
    frm.set_value("tax_category", "");
    frm.set_value("shipping_address", "");
    frm.set_value("billing_address", "");
    frm.set_value("place_of_supply", "");
    clear_taxes(frm);
    if (frm.doc.cost_center) {
      // Define Cost Center to Address mapping
      let cost_center_map = {
        "Assam - PBPL": "PBPL - Assam-Billing",
        "Puducherry - PBPL": "PBPL - Pondy-Billing",
        "Assam - PL": "PHOENIX LABORATORIES - Assam-Billing",
        // Add more mappings as needed
      };

      let billing_address_name = cost_center_map[frm.doc.cost_center];

      if (billing_address_name) {
        //console.log("billing address");
        // Fetch the Billing Address details
        frappe.call({
          method: "frappe.client.get_list",
          args: {
            doctype: "Address",
            filters: { name: billing_address_name },
            fields: ["name", "state", "gst_state_number"],
          },
          callback: function (res) {
            //console.log("res", res);
            if (res && Array.isArray(res.message) && res.message.length > 0) {
              //console.log(res.message);
              let address = res.message[0];
              frm.set_value("billing_address", address.name);
              frm.set_value("shipping_address", address.name); // Set Shipping Address same as Billing
              //console.log("supplier", frm.doc.supplier_address);
              const supplierAddress = frm.doc.supplier_address;
              const gst_state_company = address.gst_state_number;
              if (supplierAddress) {
                //console.log("inside supplier call");
                frappe.call({
                  method: "frappe.client.get_list",
                  args: {
                    doctype: "Address",
                    filters: { name: supplierAddress },
                    fields: ["name", "state", "gst_state_number"],
                  },
                  callback: function (res) {
                    if (
                      res &&
                      Array.isArray(res.message) &&
                      res.message.length > 0
                    ) {
                      //console.log("res from supplier");
                      // call select_tax_template
                      let gst_state_supplier = res.message[0].gst_state_number;
                      if (frm.doc.gst_category === "Registered Regular") {
                        select_tax_template(
                          frm,
                          gst_state_supplier,
                          gst_state_company,
                          frm.doc.cost_center,
                          false // isReverseCharge
                        );
                      } else if (frm.doc.gst_category === "Unregistered") {
                        frappe.msgprint({
                          message: __(
                            "Supplier is unregistered, Reverse charge tax template will be selected now. If you wish to change it, go to address list and for the supplier create or update their GST category and then reselect cost center again"
                          ),
                          indicator: "blue",
                        });
                        select_tax_template(
                          frm,
                          gst_state_supplier,
                          gst_state_company,
                          frm.doc.cost_center,
                          true // isReverseCharge
                        );
                      } else {
                        // currently overseas are unhandled
                        //console.log("here overseas")
                        frappe.msgprint({
                          message: __(
                            "Supplier is not unregistered / Registered, please choose the tax template or contact support if needed."
                          ),
                          indicator: "blue",
                        });
                      }
                    }
                  },
                });
              } else {
                frappe.msgprint({
                  message: __(
                    "Supplier address / GST state not found, create and reselect the cost center for auto fetching of tax template"
                  ),
                  indicator: "red",
                });
              }
            }
          },
        });
      }
    }
  },
  company: function (frm) {
    frm.set_value("cost_center", "");
    clear_taxes(frm);
    //console.log("cleared defaults");
  },
  supplier: function (frm) {
    frm.set_value("cost_center", "");
    //clear_taxes(frm);
    //console.log("cleared defaults");
  },
  supplier_address: function (frm) {
    clear_taxes(frm);
    //console.log("cleared defaults");
  },
  //**client script: set contact POC in PO form
  custom_company_poc_contact: function (frm) {
    fetch_contact_details(
      frm,
      "custom_company_poc_contact",
      "custom_poc_name__phone"
    );
  },
  contact_person: function (frm) {
    fetch_contact_details(frm, "contact_person", "custom_supplier_name__phone");
  },
  //items_add - validation if cost center is selected to fetch the tax rates
  //if company or address is changed make user to re choose cost center for triggereing fn
});

//**client script: Set manufacturer address in PO Item
frappe.ui.form.on("Purchase Order Item", {
  custom_select_manufacturer_address: function (frm, cdt, cdn) {
    let row = locals[cdt][cdn];

    if (row.custom_select_manufacturer_address) {
      frappe.call({
        method: "frappe.client.get",
        args: {
          doctype: "Address",
          name: row.custom_select_manufacturer_address,
        },
        callback: function (r) {
          if (r.message) {
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

function select_tax_template(
  frm,
  supplier_gst_state,
  company_gst_state,
  cost_center,
  isReverseCharge
) {
  if (supplier_gst_state && company_gst_state) {
    let tax_template = "";
    let tax_category = "";
    if (supplier_gst_state === company_gst_state) {
      // in-state
      if (cost_center === "Assam - PL") {
        tax_template = isReverseCharge
          ? "Input GST RCM In-state - PL"
          : "Input GST In-state - PL";
        tax_category = isReverseCharge
          ? "Reverse Charge In-State - PL"
          : "In-State - PL";
      } else if (cost_center === "Puducherry - PBPL") {
        tax_template = isReverseCharge
          ? "Input GST RCM In-state Pondy - PBPL"
          : "Input GST In-state Pondy - PBPL";
        tax_category = isReverseCharge
          ? "Reverse Charge In-State Pondy - PBPL"
          : "In-State Pondy - PBPL";
      } else {
        //cost_center === "Assam - PBPL"
        tax_template = isReverseCharge
          ? "Input GST RCM In-state Assam - PBPL"
          : "Input GST In-state Assam - PBPL";
        tax_category = isReverseCharge
          ? "Reverse Charge In-State Assam - PBPL"
          : "In-State Assam - PBPL";
      }
    } else {
      //out-state
      if (cost_center === "Assam - PL") {
        tax_template = isReverseCharge
          ? "Input GST RCM Out-state - PL"
          : "Input GST Out-state - PL";
        tax_category = isReverseCharge
          ? "Reverse Charge Out-State - PL"
          : "Out-State - PL";
      } else if (cost_center === "Puducherry - PBPL") {
        tax_template = isReverseCharge
          ? "Input GST RCM Out-state Pondy - PBPL"
          : "Input GST Out-state Pondy - PBPL";
        tax_category = isReverseCharge
          ? "Reverse Charge Out-State Pondy - PBPL "
          : "Out-State Pondy - PBPL";
      } else {
        //cost_center === "Assam - PBPL"
        tax_template = isReverseCharge
          ? "Input GST RCM Out-state Assam - PBPL"
          : "Input GST Out-state Assam - PBPL";
        tax_category = isReverseCharge
          ? "Reverse Charge Out-State Assam - PBPL"
          : "Out-State Assam - PBPL";
      }
    }
    //console.log(
    //   "inside fn",
    //   supplier_gst_state,
    //   company_gst_state,
    //   cost_center,
    //   tax_template
    // );
    frm.set_value("tax_category", tax_category);
    frm.set_value("taxes_and_charges", tax_template);
  }
}

function clear_taxes(frm) {
  frm.set_value("tax_category", "");
  frm.set_value("taxes_and_charges", "");
  frm.set_value("taxes", []);
  frm.set_value("total_taxes_and_charges", "");
}

function fetch_contact_details(frm, contact_field, target_field) {
  if (frm.doc[contact_field]) {
    frappe.call({
      method: "frappe.client.get",
      args: {
        doctype: "Contact",
        name: frm.doc[contact_field],
      },
      callback: function (data) {
        if (data.message) {
          let contact = data.message;
          // Get Primary Mobile
          let primary_mobile = (contact.phone_nos || []).find(
            (phone) => phone.is_primary_mobile_no
          );
          const primary_mobile_no_string = primary_mobile
            ? primary_mobile.phone
            : "";
          // Get Primary Email
          let primary_email = (contact.email_ids || []).find(
            (email) => email.is_primary
          );
          const primary_email_string = primary_email
            ? primary_email.email_id
            : "";
          // Get Contact Display Name
          let contact_display =
            contact.contact_display || contact.first_name || "";

          // Combine Details: "Name, Phone, Email"
          let details_array = [
            contact_display,
            primary_mobile_no_string,
            primary_email_string,
          ].filter(Boolean);
          let formatted_details = details_array.join(", ");

          // Set Value
          frm.set_value(target_field, formatted_details);
        }
      },
    });
  } else {
    frm.set_value(target_field, "");
  }
}

function html2text(html) {
    if (!html) return '';
    
    // Convert HTML to text and preserve whitespace
    html = html
        .replace(/<\/div>/gi, "<br></div>")     // replace end of blocks (case insensitive)
        .replace(/<\/p>/gi, "<br></p>")         // replace end of paragraphs
        .replace(/<br\s*\/?>/gi, "\n")          // handle <br>, <br/>, <br />
        .replace(/<\/li>/gi, "<br></li>");      // handle list items if any
    
    const text = frappe.utils.html2text(html);
    return text
        .replace(/\n{3,}/g, "\n")             // remove excess newlines
        .trim();                                // remove leading/trailing whitespace
}