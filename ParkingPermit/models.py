
"""
Holds all of the data models for the site for managing campus visitors.

TODO: 

Triggers for history so we don't lose old data - document

Load new data - Update to use user defined make/model

Future:



history

Deploy notes:

"""

import datetime
import re

from django.contrib.auth.models import Group, User
from django.db import models
from django.contrib.admin.models import LogEntry
#from django.contrib.localflavor.us.models import USStateField
from django.contrib.localflavor.us.us_states import STATE_CHOICES
from django.core.mail import EmailMultiAlternatives
from general.models import AuditableTable,LookUp
from django.db.models.signals import post_save
from general.utilities import memoize
from django.conf import settings

#fix Django bug, uggh
User._meta.ordering=["username"]


class VehicleType(LookUp):
    class Meta:
        ordering = ['name']
class VehicleColor(LookUp):
    class Meta:
        ordering = ['name']
class VehicleMake(LookUp):
    class Meta:
        ordering = ['name']
class ParkingLocation(LookUp):
    class Meta:
        ordering = ['name']
class ViolationReason(LookUp):
    class Meta:
        ordering = ['name']
class LivingArrangement(LookUp):
    class Meta:
        ordering = ['name']

class Vehicle(AuditableTable):
    """  """
    vehicle_type = models.ForeignKey(VehicleType)
    make = models.ForeignKey(VehicleMake)
    model = models.CharField(max_length=500)

    class Meta:
        unique_together = ("vehicle_type", "make", "model", )
        ordering = ['vehicle_type', 'make', 'model']

    def __unicode__(self):
        ret_str = "%s %s" % (self.make, self.model)
        return ret_str

class VehicleRegistration(AuditableTable):
    """This is the main table to record the issue of a parking permit
    (registration) for a user/vehicle combination for one parking year.

    Note: These records should generally not be deleted since we want to keep a 
    historical record.
    """
    class Meta:
        ordering = ['-created_datetime']
    user = models.ForeignKey(User, null=True, blank=True)
    vehicle = models.ForeignKey(Vehicle, null=True, blank=True,
        help_text="If you see your vehicle in the dropdown list, select it.  Otherwise <a href='#' id='show_user_vehicle'>click here</a>.")
    user_entered_vehicle_make = models.CharField(max_length=50, blank=True)
    user_entered_vehicle_model = models.CharField(max_length=50, blank=True)
    color = models.ForeignKey(VehicleColor,
        help_text="Choose closest matching color from the list.")
    license_plate = models.CharField(max_length=20, help_text="Please no spaces or dashes")
    #Django hack, update states to include a *foreign option* (instead of using USStateField)
    license_plate_state	= models.CharField(max_length=2, choices=(('ZZ', '*Non - US*'),) + STATE_CHOICES)
    parking_location = models.ForeignKey(ParkingLocation, null=True, blank=True)
    current_living_arrangement = models.ForeignKey(LivingArrangement, 
        verbose_name="Where do you live?")
    current_apt_number = models.CharField(max_length=20, blank=True, help_text="Apartment Number (if applicable)")
    parking_number = models.CharField(max_length=200, blank=True)
    parking_number_year = models.IntegerField(blank=True, null=True)
    notes =  models.CharField(max_length=500, blank=True)
    agree_to_TOS =  models.BooleanField("Policy Agreement", blank=False,
        help_text="I acknowledge that I have read and understand the <a href='http://wiki/wiki/display/policy/Parking+on+Campus'>rules</a> for parking " \
        "on the Janelia Farm Research Campus. I agree to abide by these rules.  I understand " \
        "that failure to follow these rules may result in loss of parking privileges on campus.")
    active = models.BooleanField(default=True, help_text="Uncheck to remove this vehicle.")

    #Fields to collect data for non credentialed employees who won't have their own user 
    #accounts.  The parking system gamekeeper will enter their registrations manually into 
    #the system.
    non_cred_first_name = models.CharField(max_length=255, blank=True, 
        verbose_name="Non-Credentialed User - First Name")
    non_cred_last_name = models.CharField(max_length=255, blank=True, 
        verbose_name="Non-Credentialed User - Last Name")
    non_cred_dept_company = models.CharField(max_length=255, blank=True, 
        verbose_name="Non-Credentialed User - Dept. or Company")

    def vehicle_for_display(self):
        if self.vehicle:
            return str(self.vehicle)
        else:
            return "%s %s" % (self.user_entered_vehicle_make,self.user_entered_vehicle_model)

    def user_display_name(self):
        if self.user:
            return self.user.get_profile().display_name
        else:
            return str(self.non_cred_first_name) + ' ' + str(self.non_cred_last_name)

    def user_dept_company(self):
        if self.user:
            return self.user.get_profile().description
        else:
            return self.non_cred_dept_company

    def user_phone_email(self):
        if self.user:
            return "%s / %s" % (self.user.get_profile().work_phone,
                self.user.email) 
        else:
            return ""

    def __unicode__(self):
        if self.user:
            user_str = str(self.user)
        else:
            user_str = str(self.non_cred_first_name) + ' ' + str(self.non_cred_last_name)
        return "%s, %s, Tags: %s %s Parking #: %s" % (
            user_str,            
            self.vehicle, 
            self.license_plate_state,
            self.license_plate,
            #self.parking_location, #doesn't get included in selected related so leave out
            self.parking_number)

    def get_edit_url(self,include_base=False):
        url = '/ParkingPermit/vehicleregistration/%s/' % self.id
        if include_base:
            url = settings.BASE_URL + url
        return url

    def save(self, *args, **kwargs):
        """Clean up, replace spaces and dashes in license plate"""
        if self.license_plate:
            self.license_plate = self.license_plate.replace('-','').replace(' ','')
        super(VehicleRegistration,self).save(*args, **kwargs)

    def send_created_email(self):
        """Send an email when a new registration is added"""
        if settings.NOTIFY_NEW_REG:
            to = settings.NOTIFY_NEW_REG
            message = """\
Greetings,<br><br>

A new vehicle registration has been submitted by %s.<br><br>

Go here to view or edit the request: <br>
<a href="%s">%s</a>
<br><br>
Sincerely,<br><br>
The Janelia Parking Permit Program
            """ % (self.user_display_name(), self.get_edit_url(True), self.get_edit_url(True))
            subject = 'A new parking permit request has been entered'
            from_email = 'parkingpermit-donotreply@janelia.hhmi.org'
            text_content = re.sub(r'<[^>]+>','',message)
            html_content = message
            msg = EmailMultiAlternatives(subject, text_content, from_email, to)
            msg.attach_alternative(html_content, "text/html")
            msg.send()

class Violation(AuditableTable):
    """ """
    class Meta:        
        ordering = ['serial_number']

    serial_number = models.CharField(max_length=50, unique=True)
    vehicle_registration = models.ForeignKey(VehicleRegistration,) #        limit_choices_to = {'active': True}) .. would be good but breaks old records:-(
    reason = models.ForeignKey(ViolationReason)
    location = models.ForeignKey(ParkingLocation, null=True, blank=True)
    violation_datetime = models.DateTimeField(blank=True)
    notes =  models.CharField(max_length=500, blank=True, help_text="Optional notes")
    photo = models.ImageField(blank=True, upload_to='violation_photos',
        help_text="Optional image of infraction")

    def __unicode__(self):
        ret_str = "%s / %s - %s" % (self.reason, self.created_datetime, 
            self.vehicle_registration)
        return ret_str

    def user_display_name(self):
        if self.vehicle_registration.user:
            return self.vehicle_registration.user.get_profile().display_name
        else:
            return str(self.vehicle_registration.non_cred_first_name) + ' ' + str(self.vehicle_registration.non_cred_last_name)

    def user_dept_company(self):
        if self.vehicle_registration.user:
            return self.vehicle_registration.user.get_profile().description
        else:
            return self.vehicle_registration.non_cred_dept_company


class UserProfile(models.Model):
    """Additional information to be stored with each user"""
    # This field is required.
    user = models.OneToOneField(User)
    work_phone = models.CharField(max_length=255, blank=True)
    job_title = models.CharField(max_length=255, blank=True)
    department = models.CharField(max_length=255, blank=True)
    employee_num = models.CharField(max_length=30)
    LDAP_name = models.CharField(max_length=255)
    description = models.CharField(max_length=500, blank=True)
    company = models.CharField(max_length=500, blank=True)
    display_name = models.CharField(max_length=100, blank=True)
    room = models.CharField(max_length=100, help_text="Location", blank=True)
    is_active_employee = models.BooleanField(default=True)
    date_severed = models.DateField(blank=True)
    employee_type = models.CharField(max_length=100, blank=True, 
        choices=(('SR','Shared Resource'),('RESEARCH','Research')))
    gender = models.CharField(max_length=100, blank=True, 
        choices=(('m','Male'),('f','Female')))

    def date_joined(self):
        return self.user.date_joined

#Make sure a user profile gets created if a user doesn't have one
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
#Use any string with dispatch_uid to prevent signal from being fired once for every
#time the module it imported.  Stupid Django bug ...
post_save.connect(create_user_profile, sender=User, dispatch_uid="models.py")

class MyVehicalsProxy(VehicleRegistration):
    """This is a dummy model for a different object view in admin interface
    see: http://stackoverflow.com/questions/1861897/django-filtering-or-displaying-a-model-method-in-django-admin
    """
    class Meta:
        proxy=True
        verbose_name = "Registered Vehicle"
        verbose_name_plural = "My Registered Vehicles"
        ordering = ['-active','vehicle']

class PendingVehicalsProxy(VehicleRegistration):
    """This is a dummy model for a different object view in admin interface
    see: http://stackoverflow.com/questions/1861897/django-filtering-or-displaying-a-model-method-in-django-admin
    This displays any registrations without a year or parking number.
    """
    class Meta:
        proxy=True
        verbose_name = "Pending Registered Vehicle"
        verbose_name_plural = "Pending Registered Vehicles"
        ordering = ['-updated_datetime']

class OffboardedVehicalsProxy(VehicleRegistration):
    """This is a dummy model for a different object view in admin interface
    see: http://stackoverflow.com/questions/1861897/django-filtering-or-displaying-a-model-method-in-django-admin
    This displays any active registrations for employees who have been offboarded.
    """
    class Meta:
        proxy=True
        verbose_name = "Offboarded Employee - Registered Vehicle"
        verbose_name_plural = "Offboarded Employees - Registered Vehicles"
        ordering = ['-updated_datetime']
        
