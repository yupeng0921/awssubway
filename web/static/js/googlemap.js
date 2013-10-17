function addListener(marker)
{
	google.maps.event.addListener(marker, 'click', function() {
				window.open("/" + marker.name, '_self');
			});
}

function initialize()
{
	var mapOptions = {
	center: new google.maps.LatLng(39.904897,116.40765),
	zoom: 12,
	mapTypeId: google.maps.MapTypeId.ROADMAP
	};
	var map = new google.maps.Map(document.getElementById("map_canvas"),
								  mapOptions);
	for (var i = 0 ; i < stations.length ; i++) {
		var station = stations[i];
		var marker = new google.maps.Marker({
			position: new google.maps.LatLng(station.x,station.y),
			name:station.name
			});
		// To add the marker to the map, call setMap();
		marker.setMap(map);
		// must use an independ function, or the marker is always the last one
		addListener(marker);
	}
}
