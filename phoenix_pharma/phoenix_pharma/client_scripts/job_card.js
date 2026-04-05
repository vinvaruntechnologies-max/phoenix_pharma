frappe.ui.form.on("Job Card", {
  refresh: function (frm) {
    frm.set_query("workstation", () => {
      return {
        filters: {
          custom_company: frm.doc.company,
        },
      };
    });
  },
});
