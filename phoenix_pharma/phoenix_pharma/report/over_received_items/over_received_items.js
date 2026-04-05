// Copyright (c) 2025, Navin R C and contributors
// For license information, please see license.txt

frappe.query_reports["Over Received Items"] = {
	filters: [
	  {
		fieldname: "supplier",
		label: "Supplier",
		fieldtype: "Link",
		options: "Supplier",
	  },
	  {
		fieldname: "item_code",
		label: "Item Code",
		fieldtype: "Link",
		options: "Item",
	  },
	  {
		fieldname: "po_from_date",
		label: "PO From Date",
		fieldtype: "Date",
	  },
	  {
		fieldname: "po_to_date",
		label: "PO To Date",
		fieldtype: "Date",
	  },
	  {
		fieldname: "pr_from_date",
		label: "PR From Date",
		fieldtype: "Date",
	  },
	  {
		fieldname: "pr_to_date",
		label: "PR To Date",
		fieldtype: "Date",
	  },
	  {
		fieldname: "company",
		label: "Company",
		fieldtype: "Link",
		options: "Company",
	  },
	],
  
	onload: function (report) {
	  report.page.add_inner_button("Clear All Filters", function () {
		report.filters.forEach(filter => {
		  report.set_filter_value(filter.df.fieldname, null);
		});
	  });
	},
  
	formatter: function (value, row, column, data, default_formatter) {
	  value = default_formatter(value, row, column, data);
  
	  if (column.fieldname === "excess_qty" && data && data.excess_qty > 0) {
		value = `<span style="color: red;">${data.excess_qty}</span>`;
	  }
  
	  return value;
	},
  };
  