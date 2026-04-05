frappe.ui.form.on("Material Request", {
  custom_cost_center: function (frm) {
    set_cost_center_in_items(frm, frm.doc.custom_cost_center);
  },
  refresh(frm) {
    const common_filter = {
      company: frm.doc.company,
      is_group: 0,
    };
    frm.set_query("custom_cost_center", () => ({
      filters: common_filter,
    }));

    frm.set_query("set_warehouse", () => ({
      filters: {...common_filter, warehouse_type: "Purchase"},
    }));
  },
});

function set_cost_center_in_items(frm, cost_center) {
  if (!cost_center) return;

  frm.doc.items.forEach((row) => {
    row.cost_center = cost_center;
  });

  frm.refresh_field("items");
}
