frappe.ui.form.on("Quality Inspection", {
  //** client script: Update supplier, control number and manufacturer in QI from ref dt
  before_save: async function (frm) {
    if (!frm.doc.reference_type || !frm.doc.reference_name) {
      frappe.msgprint({
        title: __("Missing Reference"),
        message: __("Reference Type or Reference Name is missing."),
        indicator: "red",
      });
      return;
    }

    let allowed_reference_types = [
      "Purchase Receipt",
      "Delivery Note",
      "Stock Entry",
    ];
    if (!allowed_reference_types.includes(frm.doc.reference_type)) {
      console.warn(
        `Reference Type ${frm.doc.reference_type} is not yet handled.`
      );
      return;
    }

    try {
      let reference_doc = await frappe.db.get_doc(
        frm.doc.reference_type,
        frm.doc.reference_name
      );
      if (
        !reference_doc ||
        !reference_doc.items ||
        reference_doc.items.length === 0
      ) {
        frappe.msgprint({
          title: __("No Items Found"),
          message: __(
            `No items found in the referenced ${frm.doc.reference_type}.`
          ),
          indicator: "red",
        });
        return;
      }

      let updated_fields = {};

      // Set custom_supplier from reference document (form level)
      if (!frm.doc.custom_supplier && reference_doc.supplier) {
        updated_fields.custom_supplier = reference_doc.supplier;
      }

      // Find the matching item in the reference document
      let matching_item = reference_doc.items.find(
        (item) => item.item_code === frm.doc.item_code
      );

      if (matching_item) {
        // Set custom_control_number only if not already set
        if (
          !frm.doc.custom_control_number &&
          matching_item.custom_control_number
        ) {
          updated_fields.custom_control_number =
            matching_item.custom_control_number;
        }

        if (
          !frm.doc.custom_number_of_containers &&
          matching_item.custom__no_of_containers
        ) {
          updated_fields.custom_number_of_containers =
            matching_item.custom__no_of_containers;
        }

        // Set custom_manufacturer from item level
        if (!frm.doc.custom_manufacturer && matching_item.manufacturer) {
          updated_fields.custom_manufacturer = matching_item.manufacturer;
        }

        if (!frm.doc.custom_batch_qty && matching_item.qty) {
          updated_fields.custom_batch_qty = matching_item.qty;
        }
      }

      // Update only if there are changes
      if (Object.keys(updated_fields).length > 0) {
        Object.keys(updated_fields).forEach((field) => {
          frappe.model.set_value(
            frm.doctype,
            frm.doc.name,
            field,
            updated_fields[field]
          );
          frm.refresh_field(field); // Refresh only updated fields
        });
      }
    } catch (err) {
      console.error(`Error fetching data from ${frm.doc.reference_type}:`, err);
    }
  },
  custom_print_label: function (frm) {
    if (!frm.doc.custom_control_number) {
      frappe.msgprint(
        "Unable to print: Control Number not available, please save once and retry."
      );
      return;
    }

    const control_number = frm.doc.custom_control_number || "";
    const label_type = frm.doc.custom_label_to_print || "";
    const no_of_containers = frm.doc.custom_number_of_containers || "";
    const sample_size = frm.doc.sample_size || "";
    const arn_status = frm.doc.status || "";
    const arn_date = frm.doc.report_date || "";
    const arn_no = frm.doc.name || "";
    const analysed_by = frm.doc.custom_analysed_by || "";

    if (!no_of_containers || no_of_containers <= 0) {
      frappe.msgprint(
        "Unable to print: No. of containers must be greater than 0."
      );
      return;
    }

    if (label_type === "Approved" && frm.doc.docstatus !== 1) {
      frappe.msgprint(
        "The Quality Inspection must be submitted before printing 'Approved' label"
      );
      return;
    }

    if (label_type === "Approved" && arn_status !== "Accepted") {
      frappe.msgprint(
        "The Quality Inspection status must be 'Accepted' before printing 'Approved' label"
      );
      return;
    }

    // DB existence check
    frappe.db
      .exists("Control Number", control_number)
      .then((exists) => {
        if (exists) {
          const url =
            `/api/method/phoenix_pharma.phoenix_pharma.utils.label_utils.print_label?` +
            `control_number_name=${encodeURIComponent(control_number)}` +
            `&no_of_containers=${encodeURIComponent(no_of_containers)}` +
            `&label_type=${encodeURIComponent(label_type)}` +
            `&date=${encodeURIComponent(arn_date)}` +
            `&sample_size=${encodeURIComponent(sample_size)}` +
            `&arn_status=${encodeURIComponent(arn_status)}` +
            `&analysed_by=${encodeURIComponent(analysed_by)}` +
            `&arn_no=${encodeURIComponent(arn_no)}`;
          window.open(url);
        } else {
          frappe.msgprint("Unable to print: Control Number does not exist.");
        }
      })
      .catch(() => {
        frappe.msgprint("Error checking Control Number in the system.");
      });
  },
  setup: function (frm) {
    get_claim_items(frm);
  },
  item_code: function (frm) {
    get_claim_items(frm);
  },
  custom_reset: function (frm) {
    if (frm.doc.docstatus === 0) {
      get_claim_items(frm, true);
    } else {
      frappe.msgprint("You cannot reset claim items on a submitted document.");
    }
  },
});

frappe.ui.form.on("Assay Reading", {
  claim_obtained: function (frm, cdt, cdn) {
    update_result_percentage(cdt, cdn);
    frm.refresh_field("custom_label_claim_items");
  },
  label_claim: function (frm, cdt, cdn) {
    update_result_percentage(cdt, cdn);
    frm.refresh_field("custom_label_claim_items");
  },
});

function update_result_percentage(cdt, cdn) {
  let row = locals[cdt][cdn];
  if (row.label_claim && row.claim_obtained && row.label_claim !== 0) {
    row.result__in__ = (row.claim_obtained / row.label_claim) * 100;
  } else {
    row.result__in__ = null;
  }
}

function get_claim_items(frm, force = false) {
  if (
    frm.doc.item_code &&
    [
      "Finished Product",
      "Finished Food Product",
      "Semi Finished Product",
    ].includes(frm.doc.custom_item_group)
  ) {
    // Only fetch/populate if table is empty or if reset
    if (
      force ||
      !frm.doc.custom_label_claim_items ||
      frm.doc.custom_label_claim_items.length === 0
    ) {
      frappe.call({
        method: "frappe.client.get",
        args: {
          doctype: "Item",
          name: frm.doc.item_code,
        },
        callback: function (r) {
          const item_doc = r.message;
          const claim_items = item_doc.custom_claim_items || [];

          if (claim_items.length) {
            frm.clear_table("custom_label_claim_items");

            claim_items.forEach((row) => {
              let child = frm.add_child("custom_label_claim_items");
              child.contains = row.contains_heading;
              child.label_claim = row.strength;
              child.label_claim_uom = row.uom;
              child.claim_obtained_uom = row.uom;
            });

            frm.refresh_field("custom_label_claim_items");
          }
        },
      });
    }
  }
}
