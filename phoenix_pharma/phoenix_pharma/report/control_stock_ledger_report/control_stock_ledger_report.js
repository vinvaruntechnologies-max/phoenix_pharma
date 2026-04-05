// Copyright (c) 2025, Navin R C and contributors
// For license information, please see license.txt

frappe.query_reports["Control Stock Ledger Report"] = {
  filters: [
    {
      fieldname: "company",
      label: "Company",
      fieldtype: "Link",
      options: "Company",
    },
    {
      fieldname: "name",
      label: "Control Number",
      fieldtype: "Link",
      options: "Control Number",
    },
    {
      fieldname: "item_code",
      label: "Item",
      fieldtype: "Link",
      options: "Item",
    },
    {
      label: "Batch",
      fieldname: "batch",
      fieldtype: "Link",
      options: "Batch",
    },
  ],
};
