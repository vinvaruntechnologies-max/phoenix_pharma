// Copyright (c) 2025, Navin R C and contributors
// For license information, please see license.txt

frappe.query_reports["PR PI Report"] = {
  filters: [
    {
      fieldname: "purchase_receipt",
      label: "Purchase Receipt",
      fieldtype: "Link",
      options: "Purchase Receipt",
      reqd: 0,
    },
    {
      fieldname: "supplier",
      label: "Supplier",
      fieldtype: "Link",
      options: "Supplier",
      reqd: 0,
    },
    {
      fieldname: "from_date",
      label: "From PR Date",
      fieldtype: "Date",
      reqd: 0,
    },
    {
      fieldname: "to_date",
      label: "To PR Date",
      fieldtype: "Date",
      reqd: 0,
    },
    {
      fieldname: "receipt_status",
      label: "Receipt Status",
      fieldtype: "Select",
      options: "\nDraft\nTo Receive\nTo Bill\nCompleted\nCancelled",
      default: "To Bill",
    },
    {
      fieldname: "include_draft_pi",
      label: "Include Draft PIs",
      fieldtype: "Check",
      default: 1,
    },
    {
      fieldname: "only_with_pi",
      label: "Only Rows With PI",
      fieldtype: "Check",
      default: 0,
    },
    {
      fieldname: "only_without_pi",
      label: "Only Rows Without PI",
      fieldtype: "Check",
      default: 0,
    },
  ],
};
