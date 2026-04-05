frappe.ui.form.on("Production Plan", {
  refresh(frm) {
    frm.set_query("sub_assembly_warehouse", () => ({
      filters: [
        ["company", "=", frm.doc.company],
        ["is_group", "=", 0],
        ["warehouse_type", "=", "WIP"],
      ],
    }));

    frm.set_query("for_warehouse", () => ({
      filters: [
        ["company", "=", frm.doc.company],
        ["is_group", "=", 0],
        ["warehouse_type", "=", "Purchase"],
      ],
    }));
  },
  validate(frm) {
    frm.trigger("set_cost_center_from_sales_orders");
    return frm.trigger("check_cost_centers");
  },

  set_cost_center_from_sales_orders(frm) {
    if (!frm.doc.sales_orders || frm.doc.sales_orders.length === 0) {
      frm.set_value("custom_cost_center", null);
      return;
    }

    frappe.call({
      method: "frappe.client.get_value",
      args: {
        doctype: "Sales Order",
        filters: {
          name: frm.doc.sales_orders[0].sales_order,
        },
        fieldname: "cost_center",
      },
      callback(r) {
        if (r.message) {
          frm.set_value("custom_cost_center", r.message.cost_center);
        }
      },
    });
  },

  check_cost_centers(frm) {
    const cost_center_map = {};
    const promises = [];

    frm.doc.sales_orders.forEach((row) => {
      if (row.sales_order) {
        promises.push(
          frappe.db
            .get_value("Sales Order", row.sales_order, "cost_center")
            .then((r) => {
              if (r && r.message) {
                const cc = r.message.cost_center;
                cost_center_map[row.sales_order] = cc;
              }
            })
        );
      }
    });
    return Promise.all(promises).then(() => {
      const unique_cost_centers = [...new Set(Object.values(cost_center_map))];
      if (unique_cost_centers.length > 1) {
        const details = Object.entries(cost_center_map)
          .map(([so, cc]) => `${so}: ${cc}`)
          .join("<br>"); // Use <br> instead of \n
        const cost_center_list = unique_cost_centers.join(", ");
        frappe.throw({
          title: __("Multiple Cost Centers Detected"),
          message: __(
            "All Sales Orders in a Production Plan must have the same Cost Center.<br><br>" +
              "However, the following cost centers were found:<br><b>{0}</b><br><br>" +
              "Details:<br>{1}",
            [cost_center_list, details]
          ),
        });
      }
    });
  },
});
