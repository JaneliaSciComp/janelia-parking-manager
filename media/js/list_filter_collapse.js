;(function($){ $(document).ready(function(){
    $('#changelist-filter h3,#changelist-filter ul').slideToggle();
    $('#changelist-filter').children('h2').eq(0).click(function(){
            $('#changelist-filter h3,#changelist-filter ul').slideToggle();
        });
    });   
  })(django.jQuery);

