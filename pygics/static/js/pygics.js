var page_current = null;
var url_current = null;

var sched_id = null;
var sched_msec = 10000;
var sched_toggle = false;

function GetCookie(c_name)
{
	if (document.cookie.length > 0) {
		c_start = document.cookie.indexOf(c_name + "=");
		if (c_start != -1) {
			c_start = c_start + c_name.length + 1;
			c_end = document.cookie.indexOf(";", c_start);
			if (c_end == -1) c_end = document.cookie.length;
			return unescape(document.cookie.substring(c_start,c_end));
		}
	}
	return "";
};

function SetSchedBtnOn() {
	sched_toggle = true;
	sched_id = new Date().getTime();
	Scheduler(sched_id);
	$("#sched-toggle-btn").html('<i class="fa fa-refresh fa-2x fa-spin"></i>');
};

function SetSchedBtnOff() {
	sched_toggle = false;
	sched_id = null;
	$("#sched-toggle-btn").html('<i class="fa fa-refresh fa-2x"></i>');
};

function Scheduler(id) {
	if (sched_toggle == true && sched_id == id && url_current != null) {
		var start = new Date().getTime();
		$.ajax({
			type: "GET",
			url: url_current,
			dataType: "json",
			success : function(data) {
				$("#subject-menu").html(ParseViewDom(page_current.attr("id") + '-m-', data.menu))
				ParseViewData(data.menu);
				page_current.html(ParseViewDom(page_current.attr("id") + '-', data.page));
				ParseViewData(data.page);
				var end = new Date().getTime();
				var delay_time = sched_msec - (end - start);
				if (delay_time <= 0) { delay_time = 0; }
				setTimeout(function() { Scheduler(id); }, delay_time);
			},
			error : function(xhr, status, thrown) {
				window.alert("Session Timeout!");
				window.location.replace('/');
			}
		});
	}
};

$(document).ready(function() {
	var brand = $(".navbar-brand");
	var apps = $(".app");
	var pages = $(".page");
	var dynpages = $(".dynpage");
	var app_selector = $(".app-selector");
	var page_selector = $(".page-selector");
	var admin_selector = $(".admin-selector");
	var loading_page = $("#loading-page");
	var subject_page = $("#subject-page");
	var dashboard_page = $("#dashboard-page");
	var admin_page = $("#archon-admin-page");

	apps.hide();
	pages.collapse({'toggle': false});
	
	$("#sched-toggle-btn").click(function() {
		if (sched_toggle == false) { SetSchedBtnOn(); }
		else { SetSchedBtnOff(); }
	});
	
	brand.click(function() {
		SetSchedBtnOff();
		page_current = dashboard_page;
		url_current = "/dashboard/";
		app_selector.css("background-color", "transparent");
		page_selector.css("color", "#777");
		apps.fadeOut(350);
		dashboard_page.fadeOut(350);
		admin_page.fadeOut(350);
		subject_page.fadeOut(350);
		dynpages.fadeOut(350);
		dashboard_page.collapse("hide");
		admin_page.collapse("hide");
		subject_page.collapse("hide");
		dynpages.collapse("hide");
		dynpages.html(null);
		loading_page.collapse("show");
		$.ajax({
			url : "/dashboard/",
			dataType : "json",
			success : function(data) {
				if ( page_current == dashboard_page ) {
					setTimeout(function() {
						dashboard_page.html(ParseViewDom(dashboard_page.attr("id") + '-', data.page));
						ParseViewData(data.page);
						dashboard_page.css("height", "calc(100% - 50px)");
						loading_page.collapse("hide");
						dashboard_page.fadeIn(350);
						dashboard_page.collapse("show");
					}, 400);
				}
			},
			error : function(xhr, status, thrown) {
				window.alert("Session Timeout!");
				window.location.replace('/');
			}
		});
	});
	
	app_selector.click(function() {
		var selector = $(this);
		var app = $(selector.attr("app"));
		apps.hide();
		app_selector.css("background-color", "transparent");
		selector.css("background-color", "#e7e7e7");
		app.fadeIn(200);
	});
	
	page_selector.click(function() {
		SetSchedBtnOff();
		var selector = $(this);
		var page = $(selector.attr("page"));
		var url = selector.attr("view");
		page_current = page;
		url_current = url;
		page_selector.css("color", "#777");
		selector.css("color", "#337ab7");
		dashboard_page.fadeOut(350);
		admin_page.fadeOut(350);
		subject_page.fadeOut(350);
		dynpages.fadeOut(350);
		dashboard_page.collapse("hide");
		admin_page.collapse("hide");
		subject_page.collapse("hide");
		dynpages.collapse("hide");
		dynpages.html(null);
		loading_page.collapse("show");
		$.ajax({
			url : url,
			dataType : "json",
			success : function(data) {
				if ( page_current == page ) {
					setTimeout(function() {
						$("#subject-title").html(selector.html());
						$("#subject-title").attr("onclick", "GetData('" + url + "');");
						$("#subject-menu").html(ParseViewDom(page.attr("id") + '-m-', data.menu))
						ParseViewData(data.menu);
						page.html(ParseViewDom(page.attr("id") + '-', data.page));
						ParseViewData(data.page);
						page.css("height", "calc(100% - 100px)");
						loading_page.collapse("hide");
						subject_page.fadeIn(350);
						page.fadeIn(350);
						subject_page.collapse("show");
						page.collapse("show");
					}, 400);
				}
			},
			error : function(xhr, status, thrown) {
				window.alert("Session Timeout!");
				window.location.replace('/');
			}
		});
	});
	
	admin_selector.click(function() {
		SetSchedBtnOff();
		var selector = $(this);
		var page = $("#archon-admin-page");
		var url = selector.attr("view");
		page_current = page;
		url_current = url;
		page_selector.css("color", "#777");
		dashboard_page.fadeOut(350);
		admin_page.fadeOut(350);
		subject_page.fadeOut(350);
		dynpages.fadeOut(350);
		dashboard_page.collapse("hide");
		admin_page.collapse("hide");
		subject_page.collapse("hide");
		dynpages.collapse("hide");
		dynpages.html(null);
		loading_page.collapse("show");
		$.ajax({
			url : url,
			dataType : "json",
			success : function(data) {
				if ( page_current == page ) {
					setTimeout(function() {
						$("#subject-title").html(selector.html());
						$("#subject-title").attr("onclick", "GetData('" + url + "');");
						$("#subject-menu").html(ParseViewDom(page.attr("id") + '-m-', data.menu))
						ParseViewData(data.menu);
						page.html(ParseViewDom(page.attr("id") + '-', data.page));
						ParseViewData(data.page);
						page.css("height", "calc(100% - 100px)");
						loading_page.collapse("hide");
						subject_page.fadeIn(350);
						page.fadeIn(350);
						subject_page.collapse("show");
						page.collapse("show");
					}, 400);
				}
			},
			error : function(xhr, status, thrown) {
				window.alert("Session Timeout!");
				window.location.replace('/');
			}
		});
	});
	
	if (page_current == null) { brand.click(); }
});

function GetData(url) {
	SetSchedBtnOff();
	url_current = url;
	var dynpages = $(".dynpage");
	var subject_page = $("#subject-page");
	dynpages.fadeOut(350);
	dynpages.collapse("hide");
	$.ajax({
		type: "GET",
		url: url,
		dataType: "json",
		success : function(data) {
			setTimeout(function(){
				$("#subject-menu").html(ParseViewDom(page_current.attr("id") + '-m-', data.menu))
				ParseViewData(data.menu);
				page_current.html(ParseViewDom(page_current.attr("id") + '-', data.page));
				ParseViewData(data.page);
				if (page_current.attr("id") == "dashboard-page") { page_current.css("height", "calc(100% - 50px)"); } 
				else { page_current.css("height", "calc(100% - 100px)"); }
				page_current.fadeIn(350);
				page_current.collapse("show");
			}, 400);
		},
		error : function(xhr, status, thrown) {
			window.alert("Session Timeout!");
			window.location.replace('/');
		}
	});
};

function PostData(uuid, url) {
	SetSchedBtnOff();
	var dynpages = $(".dynpage");
	var subject_page = $("#subject-page");
	var data = {};
	$(uuid).each(function(index) {
		view = $(this);
		data[view.attr("name")] = view.val();
	});
	dynpages.fadeOut(350);
	dynpages.collapse("hide");
	$.ajax({
		type: "POST",
		url: url,
		contentType: "application/json; charset=utf-8",
		headers: { "X-CSRFToken": GetCookie("csrftoken") },
		dataType: "json",
		data: JSON.stringify(data),
		success : function(data) {
			setTimeout(function() {
				$("#subject-menu").html(ParseViewDom(page_current.attr("id") + '-m-', data.menu))
				ParseViewData(data.menu);
				page_current.html(ParseViewDom(page_current.attr("id") + '-', data.page));
				ParseViewData(data.page);
				page_current.css("height", "calc(100% - 100px)");
				page_current.fadeIn(350);
				page_current.collapse("show");
			}, 400);
		},
		error : function(xhr, status, thrown) {
			window.alert("Session Timeout!");
			window.location.replace('/');
		}
	});
};

function PostFile(uuid, url) {
	SetSchedBtnOff();
	var dynpages = $(".dynpage");
	var subject_page = $("#subject-page");
	var finput = $("#" + uuid + "-file");
	var form = new FormData($("#" + uuid));
	form.append(finput.attr("NAME"), finput[0].files[0]);
	dynpages.fadeOut(350);
	dynpages.collapse("hide");
	$.ajax({
		type: "POST",
		url: url,
		data: form,
		cache: false,
		contentType: false,
		processData: false,
		headers: { "X-CSRFToken": GetCookie("csrftoken") },
		success : function(data) {
			setTimeout(function() {
				$("#subject-menu").html(ParseViewDom(page_current.attr("id") + '-m-', data.menu))
				ParseViewData(data.menu);
				page_current.html(ParseViewDom(page_current.attr("id") + '-', data.page));
				ParseViewData(data.page);
				page_current.css("height", "calc(100% - 100px)");
				page_current.fadeIn(350);
				page_current.collapse("show");
			}, 400);
		},
		error : function(xhr, status, thrown) {
			window.alert("Session Timeout!");
			window.location.replace('/');
		}
	});
};

function DeleteData(url) {
	SetSchedBtnOff();
	var dynpages = $(".dynpage");
	var subject_page = $("#subject-page");
	dynpages.fadeOut(350);
	dynpages.collapse("hide");
	$.ajax({
		type: "DELETE",
		url: url,
		dataType: "json",
		success : function(data) {
			setTimeout(function() {
				$("#subject-menu").html(ParseViewDom(page_current.attr("id") + '-m-', data.menu))
				ParseViewData(data.menu);
				page_current.html(ParseViewDom(page_current.attr("id") + '-', data.page));
				ParseViewData(data.page);
				page_current.css("height", "calc(100% - 100px)");
				page_current.fadeIn(350);
				page_current.collapse("show");
			}, 400);
		},
		error : function(xhr, status, thrown) {
			window.alert("Session Timeout!");
			window.location.replace('/');
		}
	});
};

function ParseViewDom(page, view) {
	if (typeof view == "object") {
		var html = "";
		var attrs = view.attrs;
		var elems = view.elems;
		
		html += "<" + view.tag;
		for (var key in attrs) {
			html += ' ' + key + '="' + attrs[key] + '"';
		}
		html += ">";
		for (var i = 0, elem; elem = elems[i]; i++) {
			html += ParseViewDom(page, elem);
		}
		html += "</" + view.tag + ">";
		return html;
	}
	return view;
};

function ParseViewData(view) {
	if (typeof view == "object") {
		var elems = view.elems;
		for (var i = 0, elem; elem = elems[i]; i++) { ParseViewData(elem); }
		switch(view.tag) {
		case "TABLE": UXTable(view); break;
		case "DIV":
		case "CANVAS":
		case "SPAN":
			UXChart(view);
			break;
		}
	}
};

function UXTable(view) {
	switch(view.attrs.LIB) {
	case "table_basic": UXDataTableBasic(view); break;
	case "table_async": UXDataTableAsync(view); break;
	case "table_flip": UXFooTable(view); break;
	}
};

function UXChart(view) {
	switch(view.attrs.LIB) {
	case "dimple": UXDimple(view); break;
	case "peity": UXPeity(view); break;
	case "arbor": UXArbor(view); break;
	case "justgage": UXJustgage(view); break;
	case "flipclock": UXFlipClock(view); break;
	}
}; 