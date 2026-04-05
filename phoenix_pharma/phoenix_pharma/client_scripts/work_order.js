frappe.ui.form.on("Work Order", {
  refresh: function (frm) {
    const common_filter = {
      company: frm.doc.company,
      is_group: 0,
    };

    frm.set_query("source_warehouse", () => ({
      filters: common_filter,
    }));

    frm.set_query("fg_warehouse", () => ({
      filters: common_filter,
    }));

    frm.set_query("wip_warehouse", () => ({
      filters: common_filter,
    }));

    frm.set_query("scrap_warehouse", () => ({
      filters: common_filter,
    }));

    frm.set_query("custom_cost_center", () => ({
      filters: common_filter,
    }));

    frm.set_query("custom_batch_no", () => ({
      filters: {
        item: frm.doc.production_item,
      },
    }));

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
});
