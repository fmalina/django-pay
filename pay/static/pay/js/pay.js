function change_method(){
    if($('input[value=pp]').is(':checked')){
        $('#cc-fields').fadeOut();
    } else {
        $('#cc-fields').fadeIn();
    }
}
function  newCard(){
	$('.last-card').hide();
	$('.new-card').show();
	$('.hc').hide().show();
	$('#id_last_card').val('');
}

function lastCard(){
	$('.last-card').show();
	$('.new-card').hide();
	$('.hc').hide().show();
	$('#id_last_card').val('on');
}

$(function(){
    change_method();
    $('#method').change(function(){
        change_method();
    });
	$('.payment-card i').click(function(){
		$('.payment-card i').removeClass('active');
		$(this).addClass('active');
	});
    $('.cc-fields__cvv .badge').click(function(){
        $('.cc-fields__cvv img').animate({ 
            height: 'toggle', 
            opacity: 'toggle' 
        }, 'fast');
    });
    window.chat_open = false;
    window.onbeforeunload = function(){
		leaving_callback();
    };
});
