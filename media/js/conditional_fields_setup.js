//Hide div.user_entered_vehicle_make, div.user_entered_vehicle_model, and current_apt_number
//when page loads.
//Clicking a#show_user_vehicle shows make/model fields
//Choosing "Apartments" in select#id_current_living_arrangement shows apt number field.

//Also hide plus buttons: a.add-another

$(document).ready(function() {
    //Hide add-another plus signs since you shouldn't be able to add any fields on this page
    //It's a django bug that causes these to be shown to begin with.
    $('a.add-another').hide();
    if ($('div.user_entered_vehicle_make input').val() == "") {
        $('div.user_entered_vehicle_make').hide();
    }
    if ($('div.user_entered_vehicle_model input').val() == "") {
        $('div.user_entered_vehicle_model').hide();
    }
    if ($('div.current_apt_number input').val() == "") {
        $('div.current_apt_number').hide();
    }

    $('a#show_user_vehicle').click(function() {
        $('div.user_entered_vehicle_make').toggle(700);
        $('div.user_entered_vehicle_model').toggle(700);
    });

    $('select#id_current_living_arrangement').change(function() {
        var pattern = /.*apartment.*/i;
        //var chosen_text = $(this).val();
        var chosen_text = $('select#id_current_living_arrangement option:selected').html();
        console.log(chosen_text);
        if (pattern.test(chosen_text)) {
            $('div.current_apt_number').fadeIn(700);
        }
        else {
            $('div.current_apt_number').fadeOut(500);
        }
    });

});
