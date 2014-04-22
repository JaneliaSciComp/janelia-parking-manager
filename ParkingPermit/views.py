import datetime
import re
from collections import OrderedDict
import sys
sys.path.append('..')

import simplejson

from django.conf import settings
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.template.loader import get_template
from django.template import Context, RequestContext
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.db import connection, transaction
from django.db.models import Q
from django.contrib import messages
from django.forms import ModelForm
from django import forms
from django.forms.formsets import formset_factory
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.context_processors import csrf
from django.contrib.auth.models import Group, User
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import EmailMultiAlternatives
from django.contrib.auth.models import Group, User

from django.contrib.localflavor.us.forms import USStateField

from ParkingPermit.models import VehicleType, VehicleColor, VehicleMake, \
    ParkingLocation, Vehicle, VehicleRegistration, UserProfile, \
    LivingArrangement

#from general import recommendations

def send_non_cred_created_email(regform):
    """Send an email when a new non-cred registration is added"""
    if settings.NOTIFY_NEW_REG:
        info_str = '<br>\n'.join([': '.join([str(key).title(),str(val)]) for key, val in sorted(regform.cleaned_data.items())])
        to = settings.NOTIFY_NEW_REG
        message = """\
Greetings,<br><br>

A new vehicle registration has been submitted by a non-credentialed user.<br><br>

Please create a new entry in the Vehicle Registration Table: <br>
<a href="http://parking.int.janelia.org/ParkingPermit/vehicleregistration/">http://parking.int.janelia.org/ParkingPermit/vehicleregistration/</a>
<br><br>
Information Provided: <br><br>

%s

<br><br>
Sincerely,<br><br>
The Janelia Parking Permit Program
        """ % (info_str)
        subject = 'A non-credentialed new parking permit request has been entered'
        from_email = 'parkingpermit-donotreply@janelia.hhmi.org'
        text_content = re.sub(r'<[^>]+>','',message)
        html_content = message
        msg = EmailMultiAlternatives(subject, text_content, from_email, to)
        msg.attach_alternative(html_content, "text/html")
        msg.send()

def non_credentialed_register(request):
    """
    Display a form to non credentialed users 
    Simply email the results to the Parking Game Master
    Users won't be able to review or change results
    """
    class RegisterForm(forms.Form):
        user_first_name = forms.CharField(label="First Name", max_length=255)
        user_last_name = forms.CharField(label="Last Name", max_length=255)
        employee_dept_company = forms.CharField(label="Company or Department", max_length=255)
        vehicle_make = forms.CharField(max_length=255)
        vehicle_model = forms.CharField(max_length=255)
        vehicle_color = forms.CharField(max_length=255)
        license_plate = forms.CharField(max_length=255, help_text="Please no dashes or spaces")
        license_plate_state	= USStateField(help_text="Leave blank if not applicable.", required=False)
        current_living_arrangement = forms.ModelChoiceField(label="Where do you live?", 
            queryset=LivingArrangement.objects.all())
        current_apt_number = forms.CharField(max_length=20, required=False, help_text="Apartment Number (if applicable)")
        agree_to_TOS =  forms.BooleanField(label="Policy Agreement",
            help_text="I acknowledge that I have read and understand the <a href='http://wiki/wiki/display/policy/Parking+on+Campus'>rules</a> for parking " \
        "on the Janelia Farm Research Campus. I agree to abide by these rules.  I understand " \
        "that failure to follow these rules may result in loss of parking privileges on campus.")
        is_new =  forms.ChoiceField(label="Is this a new registration?", required=True, 
            choices=(('','---'),('Yes','Yes'),('No','No')), )
    if request.POST:
        regform = RegisterForm(request.POST)
        if regform.is_valid():
            send_non_cred_created_email(regform)
            messages.add_message(request, messages.SUCCESS, "Your information has been submitted.")
    else:
        regform = RegisterForm()

    return render_to_response('non_cred_reg.html', locals(), RequestContext(request))

@login_required
def stats(request):
    """Show vehicle stats and recommendations"""
    return HttpResponse('Coming soon!')
    '''
    #work in progress:
    regs = VehicleRegistration.objects.all()
    vehicle_ratings = {}
    for reg in regs:
        key = (reg.vehicle.make, reg.vehicle.model)
        if not key in vehicle_ratings:
            vehicle_ratings[key] = {}
        vehicle_ratings[key][reg.user] = 5
    #delete vehicles occuring only once?
    #for vehicle, dusers in vehicle_ratings.items():
    #    if len(dusers)<2:
    #        del vehicle_ratings[vehicle]

    import pprint
    pprint.pprint(sorted(vehicle_ratings.items()))

    my_vehicles = VehicleRegistration.objects.filter(user=request.user)
    for my_reg in my_vehicles:
        results = recommendations.topMatches(vehicle_ratings, (my_reg.vehicle.make, my_reg.vehicle.model))
        print my_reg.vehicle
        print results

    #working here, similarity is always 0

    test = Vehicle.objects.get(id=18)
    results = recommendations.topMatches(vehicle_ratings, (test.make, test.model))
    print test
    print results

    return render_to_response('stats.html', locals(), RequestContext(request))
    '''

