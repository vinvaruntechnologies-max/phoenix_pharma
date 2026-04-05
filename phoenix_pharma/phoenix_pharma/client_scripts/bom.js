frappe.ui.form.on("BOM", {
  refresh(frm) {
    //for items table
    frm.set_query("item_code", "items", function (doc, cdt, cdn) {
      // Define item filter based on 'custom_is_packing_bom' value
      let item_filter = {
        item_group: [
          "in",
          [
            "RM",
            "Active",
            "PM",
            "Semi Finished Product",
            "Finished Product",
            "Finished Food Product",
          ],
        ],
      };

      return {
        filters: item_filter,
      };
    });

    //for item selection
    frm.set_query("item", () => {
      return {
        filters: {
          item_group: [
            "in",
            [
              "Finished Product",
              "Semi Finished Product",
              "Finished Food Product",
            ],
          ],
        },
      };
    });
    frm.fields_dict["operations"].grid.get_field("workstation").get_query =
      function (doc, cdt, cdn) {
        let row = locals[cdt][cdn];
        return {
          filters: {
            custom_company: doc.company,
          },
        };
      };
  },
  setup(frm) {
    frm.fields_dict["operations"].grid.get_field("workstation").get_query =
      function (doc, cdt, cdn) {
        let row = locals[cdt][cdn];
        return {
          filters: {
            custom_company: doc.company,
          },
        };
      };
  },
  item: function (frm) {
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

function get_claim_items(frm, force = false) {
  if (
    frm.doc.item &&
    [
      "Finished Product",
      "Finished Food Product",
      "Semi Finished Product",
    ].includes(frm.doc.custom_item_group)
  ) {
    // Only fetch/populate if table is empty or if reset
    if (
      force ||
      !frm.doc.custom_claim_items ||
      frm.doc.custom_claim_items.length === 0
    ) {
      frappe.call({
        method: "frappe.client.get",
        args: {
          doctype: "Item",
          name: frm.doc.item,
        },
        callback: function (r) {
          const item_doc = r.message;
          const claim_items = item_doc.custom_claim_items || [];
          if (claim_items.length) {
            frm.clear_table("custom_claim_items");

            claim_items.forEach((row) => {
              let child = frm.add_child("custom_claim_items");
              child.contains_heading = row.contains_heading;
              child.strength = row.strength;
              child.uom = row.uom;
              child.description = row.description;
            });
            frm.refresh_field("custom_claim_items");
          }
        },
      });
    }
  }
}

frappe.ui.form.on("BOM Item", {
  custom_qty_wo_overage: function (frm, cdt, cdn) {
    calculate_qty(cdt, cdn);
  },
  custom_overage: function (frm, cdt, cdn) {
    calculate_qty(cdt, cdn);
  },
});

function calculate_qty(cdt, cdn) {
  let row = locals[cdt][cdn];
  if (row.custom_qty_wo_overage && row.custom_overage >= 0) {
    let overage_qty = (row.custom_qty_wo_overage * row.custom_overage) / 100;

    row.qty = row.custom_qty_wo_overage + overage_qty;

    frappe.model.set_value(cdt, cdn, "qty", row.qty);
  }
}
