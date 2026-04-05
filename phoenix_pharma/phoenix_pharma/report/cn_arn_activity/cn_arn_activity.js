// Copyright (c) 2025, Navin R C and contributors
// For license information, please see license.txt

frappe.query_reports["CN ARN Activity"] = {
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
      fieldname: "batch",
      label: "Batch",
      fieldtype: "Link",
      options: "Batch",
    },
    {
      fieldname: "from_date",
      label: "Posting Date From",
      fieldtype: "Date",
      default: frappe.datetime.add_months(frappe.datetime.nowdate(), -1),
    },
    {
      fieldname: "to_date",
      label: "Posting Date To",
      fieldtype: "Date",
      default: frappe.datetime.nowdate(),
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
  
	  if (column.fieldname === "out_qty" && data && data.out_qty !== 0) {
		value = `<span style="color: red;">${data.out_qty}</span>`;
	  }
     if (column.fieldname === "in_qty" && data && data.in_qty !== 0) {
		value = `<span style="color: green;">${data.in_qty}</span>`;
	  }
	  return value;
	},
};

