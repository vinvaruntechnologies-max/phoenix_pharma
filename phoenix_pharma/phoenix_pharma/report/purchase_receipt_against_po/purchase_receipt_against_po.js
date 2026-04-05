// Copyright (c) 2025, Navin R C and contributors
// For license information, please see license.txt

frappe.query_reports["Purchase Receipt Against PO"] = {
  filters: [
    {
      fieldname: "company",
      label: __("Company"),
      fieldtype: "Link",
      options: "Company",
      default: frappe.defaults.get_user_default("Company"),
      reqd: 1,
      width: "150px",
    },
    {
      fieldname: "supplier",
      label: __("Supplier"),
      fieldtype: "Link",
      options: "Supplier",
      width: "150px",
    },
    {
      fieldname: "purchase_order",
      label: __("Purchase Order"),
      fieldtype: "Link",
      options: "Purchase Order",
      width: "150px",
    },
  ],

  formatter: function (value, row, column, data, default_formatter) {
    value = default_formatter(value, row, column, data);

    // Color code workflow state
    if (column.fieldname == "workflow_state") {
      if (value && value.includes("Draft")) {
        value = `<span style="color: #c82712ff; font-weight: bold;">${value}</span>`;
      } else if (value && value.includes("Approved")) {
        value = `<span style="color: #28a745; font-weight: bold;">${value}</span>`;
      } else if (value && value.includes("Quality Review")) {
        value = `<span style="color: #17a2b8; font-weight: bold;">${value}</span>`;
      } else if (value && value.includes("Pending Stores Review")) {
        value = `<span style="color: #d45f11ff; font-weight: bold;">${value}</span>`;
      } else if (value && value.includes("AR Submitted")) {
        value = `<span style="color: #3f4343ff; font-weight: bold;">${value}</span>`;
      }
    }

    // Color code docstatus
    if (column.fieldname == "docstatus") {
      if (value == "Draft") {
        value = `<span class="indicator blue">${value}</span>`;
      } else if (value == "Submitted") {
        value = `<span class="indicator green">${value}</span>`;
      } else if (value == "Cancelled") {
        value = `<span class="indicator red">${value}</span>`;
      }
    }

    // Highlight balance quantities
    if (column.fieldname == "balance_qty") {
      if (data.balance_qty > 0) {
        value = `<span style="color: #de293bff; font-weight: bold;">${value}</span>`;
      } else if (data.balance_qty == 0) {
        value = `<span style="color: #11b638ff;">${value}</span>`;
      }
    }

    // Format dates
    if (column.fieldname == "po_date" || column.fieldname == "pr_date") {
      if (value && value !== "None") {
        value = frappe.datetime.str_to_user(value);
      }
    }

    return value;
  },
};
