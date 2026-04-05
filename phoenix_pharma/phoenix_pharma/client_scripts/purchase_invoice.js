frappe.ui.form.on("Purchase Invoice", {
    is_return: function (frm) {
      if (frm.is_new()) update_naming_series(frm);
    },
    before_save: function (frm) {
      if (frm.is_new()) update_naming_series(frm);
    },
  });
  
  function update_naming_series(frm) {
    if (!frm.doc.custom_abbr) return;
    let abbr = frm.doc.custom_abbr;
    let series = frm.doc.is_return
      ? `.${abbr}.DRN.MM..YY..###`
      : `.${abbr}.PI.MM..YY..####`;
  
    frm.set_value("naming_series", series);
  }