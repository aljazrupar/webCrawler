$(document).ready(function() {
	$(".autoparkPOPUP").fancybox({
		'width'					: 332,
		'height'					: 400,
		'autoScale'				: false,
		'hideOnOverlayClick': true,
		'showCloseButton'	: true,
		'overlayShow'		: true,
		'overlayOpacity'		: 0.5,
		'overlayColor'		: '#000',
		'transitionIn'			: 'elastic',
		'transitionOut'		: 'fade',
		'speedIn'				: 600,
		'speedOut'				: 900,
		'type'						: 'iframe',
		'onComplete'			: function(){
			setTimeout( function() {$.fancybox.close(); },5000); // 1000 = 1 secs
		 },
		'onClosed'				: function(){
			location.reload();
		 }
	 });
});