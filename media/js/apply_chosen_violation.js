$(document).ready(function() {
    // Set up vehicle to be searchable when page loads
    $("#id_vehicle_registration").chosen({allow_single_deselect:true, search_contains:true});

    //Re-setup vehicle into searchable widget after a new item is added to the 
    //select list, e.g., user added new option
    function onMod() {
      //Find largest option id and select that.  There will probably be
      //edge cases where this won't work but it's the bests we can do.
      var max_option_val = 0;
      $('#id_vehicle_registration').find('option').each(function() {
        var new_val = parseInt($(this).val());
        if (new_val > max_option_val) max_option_val = new_val;
      });
      $("#id_vehicle_registration").val(max_option_val);
      $("#id_vehicle_registration").trigger("liszt:updated");
    }
    var vehicle_select = document.getElementById ("id_vehicle_registration");
    if (vehicle_select) {
        //Warning this doesn't work in IE, but Django admin doesn't do popups
        // in IE? so I guess it's ok.
        vehicle_select.addEventListener ('DOMNodeInserted', onMod, false);
    }
});

