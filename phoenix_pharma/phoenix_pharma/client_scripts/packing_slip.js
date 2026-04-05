frappe.ui.form.on("Packing Slip", {
  onload: function (frm) {
    // Set batch_no filter
    frm.fields_dict["items"].grid.get_field("batch_no").get_query = function (
      doc,
      cdt,
      cdn
    ) {
      const row = locals[cdt][cdn];
      return {
        filters: {
          item: row.item_code || "",
        },
      };
    };

    frm.trigger("prepopulate_batch_nos");
  },

  prepopulate_batch_nos: async function (frm) {
    for (let row of frm.doc.items || []) {
      if (!row.batch_no && row.dn_detail) {
        try {
          const r = await frappe.call({
            method: "phoenix_pharma.phoenix_pharma.custom.packing_slip.get_batch_for_dn_item",
            args: { dn_item_name: row.dn_detail },
          });

          if (r.message && r.message.batch_no) {
            row.batch_no = r.message.batch_no;
          }
        } catch (err) {
          console.error("Error fetching batch from server:", err);
        }
      }
    }
    frm.refresh_field("items");
  },
});
