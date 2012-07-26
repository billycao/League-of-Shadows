jQuery(function() {
	var note = $('#note'),
		ts = new Date(2012, 7, 1, 10, 30).getTime();

	$('#countdown').countdown({
		timestamp	: ts,
		callback	: function(days, hours, minutes, seconds){
			var message = "";
			message += days + " day" + ( days==1 ? '':'s' ) + ", ";
			message += hours + " hour" + ( hours==1 ? '':'s' ) + ", ";
			message += minutes + " minute" + ( minutes==1 ? '':'s' ) + " and ";
			message += seconds + " second" + ( seconds==1 ? '':'s' ) + " <br />";
			message += "left until the games begin!";
			note.html(message);
		}
	});
});