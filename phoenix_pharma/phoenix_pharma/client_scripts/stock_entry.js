const valid_purposes_for_work_order = [
  "Material Transfer for Manufacture",
  "Manufacture",
  "Material Consumption for Manufacture",
  "Disassemble",
];

frappe.ui.form.on("Stock Entry", {
  onload: function (frm) {
    if (
      frm.doc.work_order &&
      valid_purposes_for_work_order.includes(frm.doc.purpose)
    ) {
      frappe.db
        .get_value("Work Order", frm.doc.work_order, [
          "custom_cost_center",
          "custom_batch_no",
          "production_item",
        ])
        .then((r) => {
          const work_order = r.message;

          // Set cost center if not already set
          if (!frm.doc.custom_cost_center && work_order.custom_cost_center) {
            frm.set_value("custom_cost_center", work_order.custom_cost_center);
            set_cost_center_in_items(frm, work_order.custom_cost_center);
          }

          // Set batch from work order
          if (work_order.custom_batch_no) {
            frm.set_value("custom_batch_no", work_order.custom_batch_no);
            set_batch_for_fg_from_work_order(
              frm,
              work_order.custom_batch_no,
              work_order.production_item
            );
          }
        });
    } else if (frm.doc.custom_cost_center) {
      set_cost_center_in_items(frm, frm.doc.custom_cost_center);
    }
  },
  refresh: function (frm) {
    const common_filter = {
      company: frm.doc.company,
      is_group: 0,
    };
    frm.set_query("custom_cost_center", () => ({
      filters: common_filter,
    }));
    toggle_manual_arn_mode(frm);
    if (frm.doc.custom_select_arn_manually) {
      frm.fields_dict["custom_exploded_items"].grid.get_field(
        "control_number"
      ).get_query = function (doc, cdt, cdn) {
        let row = locals[cdt][cdn];

        if (!row.item_code) {
          return { filters: [] };
        }

        let filters = {
          company: frm.doc.company,
          item_code: row.item_code,
          reference_document_status: "Submitted",
          arn_number: ["not in", ["", null]],
          arn_date: ["not in", ["", null]],
          arn_status: "Accepted",
          item_quantity: [">", 0],
        };

        if (row.batch) {
          filters.batch = row.batch;
        }

        return { filters };
      };
    }
  },

  custom_select_arn_manually: function (frm) {
    toggle_manual_arn_mode(frm);
    if (frm.doc.custom_select_arn_manually) {
      frm.fields_dict["custom_exploded_items"].grid.get_field(
        "control_number"
      ).get_query = function (doc, cdt, cdn) {
        let row = locals[cdt][cdn];

        if (!row.item_code) {
          return { filters: [] };
        }

        let filters = {
          company: frm.doc.company,
          item_code: row.item_code,
          reference_document_status: "Submitted",
          arn_number: ["not in", ["", null]],
          arn_date: ["not in", ["", null]],
          arn_status: "Accepted",
          item_quantity: [">", 0],
        };

        if (row.batch) {
          filters.batch = row.batch;
        }

        return { filters };
      };
    }
  },

  custom_cost_center: function (frm) {
    set_cost_center_in_items(frm, frm.doc.custom_cost_center);
  },

  custom_reset: function (frm) {
    const return_to_store_from_production_wip =
      frm.doc.is_return &&
      frm.doc.stock_entry_type === "Material Transfer for Manufacture";
    const method_to_call = return_to_store_from_production_wip
      ? "phoenix_pharma.phoenix_pharma.custom.helper.load_issued_items_from_work_order"
      : "phoenix_pharma.phoenix_pharma.custom.helper.load_exploded_se_items";
    frappe.call({
      method: method_to_call,
      args: { doc: frm.doc },
      freeze: true,
      callback: function (r) {
        if (!r.message) return;
        frm.clear_table("custom_exploded_items");
        (r.message.custom_exploded_items || []).forEach((row) => {
          frm.add_child("custom_exploded_items", row);
        });
        frm.refresh_field("custom_exploded_items");
      },
    });
  },
});

function set_cost_center_in_items(frm, cost_center) {
  if (!cost_center) return;

  frm.doc.items.forEach((row) => {
    row.cost_center = cost_center;
  });

  frm.refresh_field("items");
}

function set_batch_for_fg_from_work_order(frm, batch_no, item) {
  if (!batch_no) return;

  if (
    frm.doc.purpose === "Manufacture" ||
    frm.doc.purpose === "Material Transfer for Manufacture"
  ) {
    frm.doc.items.forEach((row) => {
      if (row.item_code === item) {
        row.batch_no = batch_no;
      }
    });

    frm.refresh_field("items");
  }
}

function toggle_manual_arn_mode(frm) {
  const is_manual = frm.doc.custom_select_arn_manually;

  // Toggle child table editability
  frm.set_df_property("custom_exploded_items", "read_only", !is_manual);

  // Toggle visibility of "control_number" field in the child table
  // frm.fields_dict.custom_exploded_items.grid.update_docfield_property(
  //   "control_number",
  //   "in_list_view",
  //   is_manual ? 1 : 0
  // );
  // Refresh grid to apply visibility changes
  // frm.fields_dict.custom_exploded_items.grid.refresh();
  frm.refresh_field("custom_exploded_items");
}

frappe.ui.form.on("Exploded Stock Entry Items", {
  control_number: function (frm, cdt, cdn) {
    // Clear issued_qty when control_number changes
    frappe.model.set_value(cdt, cdn, "issued_qty", 0);
  },

  issued_qty: function (frm, cdt, cdn) {
    let row = locals[cdt][cdn];

    const row_idx =
      frm.doc.custom_exploded_items.findIndex((r) => r.name === row.name) + 1;

    if (row.issued_qty > row.available_qty) {
      frappe.msgprint(
        __(
          "Row {0} | Item: {1} : {2} — Issued Qty cannot be more than Available Qty in ARN {3}.",
          [row_idx, row.item_code, row.item_name, row.available_qty]
        )
      );
      frappe.model.set_value(cdt, cdn, "issued_qty", 0);
      return;
    }

    // 2️⃣ Check: Sum of issued_qty for same item_code <= total_required_qty
    let total_issued = 0;

    frm.doc.custom_exploded_items.forEach((r) => {
      if (r.item_code === row.item_code) {
        total_issued += flt(r.issued_qty);
      }
    });

    if (total_issued > flt(row.total_required_qty)) {
      frappe.msgprint(
        __(
          "Row {0} | Item: {1} : {2} — Total issued quantity {3} exceeds required quantity {4}.",
          [
            row_idx,
            row.item_code,
            row.item_name,
            total_issued,
            row.total_required_qty,
          ]
        )
      );
      frappe.model.set_value(cdt, cdn, "issued_qty", 0);
    }
  },
});
