
"""
This module sets up what is shown on the admin section for this app.

We want to open this up to employees to add, view, and edit
vehicle registrations.  In this case the admin site is the whole app.

"""

import datetime
import re
import sys
sys.path.append('..')

from general.admin import LogAdmin, ReadOnlyAdmin, make_DefaultAdminAuditTable, \
    make_SensibleDefaultAdmin, SelectRelatedModelAdmin, export_as_csv_action
from general.models import LogEntryProxy
from ParkingPermit.models import VehicleType, VehicleColor, VehicleMake, \
    ParkingLocation, Vehicle, VehicleRegistration, UserProfile, MyVehicalsProxy, \
    PendingVehicalsProxy, \
    OffboardedVehicalsProxy, Violation, ViolationReason, LivingArrangement
from django.contrib import admin
from django.forms import ModelForm, TextInput
from django.contrib import messages
from django.core.mail import EmailMultiAlternatives
from django.conf import settings


class UserProfileAdmin(make_SensibleDefaultAdmin(UserProfile)):
    """Could be used for reviewing employee information, also used by Wendye to
    update employee type and gender"""
    _readonly_fields = make_SensibleDefaultAdmin(UserProfile).list_display
    _readonly_fields.remove('employee_type')
    _readonly_fields.remove('gender')
    readonly_fields = _readonly_fields
    search_fields = ['LDAP_name','display_name','description',]
    list_display = make_SensibleDefaultAdmin(UserProfile).list_display + ['date_joined']

class VehicleRegistrationAdmin(make_DefaultAdminAuditTable(VehicleRegistration)):
    class Media:
        #Update javascript on page to make vehicle be searchable
        css = {
            "all": ("js/chosen/chosen.css","vehicle_registration_override.css")
        }
        js = ("js/jquery-1.5.2.min.js","js/chosen/chosen.jquery.min.js",
            "js/apply_chosen.js",'js/list_filter_collapse.js')

    list_display_links = ('vehicle',)

    search_fields = ['vehicle__make__name','vehicle__model','color__name',
        'license_plate','license_plate_state','parking_location__name',
        'parking_number','notes','user__userprofile__LDAP_name','user__userprofile__display_name',
        'user__userprofile__description','user_entered_vehicle_make', 'user_entered_vehicle_model',
        'current_apt_number','non_cred_first_name', 'non_cred_last_name', 'non_cred_dept_company',
        ]

    list_filter = ['parking_location','parking_number_year',
        'agree_to_TOS','active','created_datetime']

    fields =  ['user','user_display_name','user_dept_company','user_phone_email', 
        'non_cred_first_name', 'non_cred_last_name', 'non_cred_dept_company',
        'vehicle','user_entered_vehicle_make', 'user_entered_vehicle_model','color',
        'license_plate',
        'license_plate_state','current_living_arrangement', 'current_apt_number', 'parking_location',
        'agree_to_TOS','active', 'parking_number','parking_number_year','notes',
        ]

    readonly_fields = ('user_phone_email', 'user_display_name', 'user_dept_company')

    list_display = make_DefaultAdminAuditTable(MyVehicalsProxy).list_display + [
        'user_display_name','user_dept_company']

    #### ADMIN ACTIONS ######

    def reset_agree_to_TOS(self, request, queryset):
        """At least once a year security will reset everyone's agreed to TOS checkbox
        so that they will need to come in, review their information and recheck the
        box in order to recieve a new parking permit.

        This also clears out the parking number and parking year.
        Restricted to super users for now.
        """
        if request.user.is_superuser:
            rows_updated = queryset.update(agree_to_TOS=False, parking_number='', parking_number_year=None)
            self.message_user(request, "%s registrations had their fields reset." % rows_updated)
        else:
            self.message_user(request, "Only super users can perform this action.")

    reset_agree_to_TOS.short_description = 'Do a Yearly Reset for the selected registrations'

    actions = [reset_agree_to_TOS, export_as_csv_action(description="Export selected records as CSV file",
                fields=fields, exclude=None, header=True)]

class ViolationAdmin(SelectRelatedModelAdmin,make_DefaultAdminAuditTable(Violation)):
    class Media:
        #Update javascript on page to make vehicle be searchable
        css = {
            "all": ("js/chosen/chosen.css","violation_override.css")
        }
        js = ("js/jquery-1.5.2.min.js","js/chosen/chosen.jquery.min.js",
            "js/apply_chosen_violation.js",'js/list_filter_collapse.js')

    list_display_links = ('serial_number',)

    exclude = make_DefaultAdminAuditTable(Violation).exclude

    search_fields = [
        'vehicle_registration__license_plate', 'vehicle_registration__parking_number',
        'vehicle_registration__user__userprofile__LDAP_name','vehicle_registration__user__userprofile__display_name',
        'vehicle_registration__user__userprofile__description', 'reason__name',
        'notes','serial_number']

    list_filter = ['created_datetime',]

    list_display = ['user_display_name','user_dept_company'] \
        + make_DefaultAdminAuditTable(Violation).list_display
    list_display.remove('serial_number')
    list_display.insert(0, 'serial_number')
    list_select_related = True

    actions = [export_as_csv_action(description="Export selected records as CSV file",
                fields=list_display, exclude=None, header=True)]

class PendingVehiclesAdmin(VehicleRegistrationAdmin):
    """This displays any registrations without a year or parking number."""
    def queryset(self, request):
        results = VehicleRegistration.objects.filter(active=True).exclude(
            parking_number_year__gte=2000,parking_number__gt=0)
        return results

class OffboardedVehiclesAdmin(VehicleRegistrationAdmin):
    """This displays any active registrations for employees who have been offboarded."""
    def queryset(self, request):
        results = VehicleRegistration.objects.filter(active=True, 
            user__userprofile__is_active_employee=False)
        return results

class MyVehiclesAdmin(make_DefaultAdminAuditTable(MyVehicalsProxy)):
    """An admin page for all users to see just their vehicles and edit/add
    in a controlled manner"""
    class Media:
        #Update javascript on page to make vehicle be searchable
        css = {
            "all": ("js/chosen/chosen.css","vehicle_registration_override.css")
        }
        js = ("js/jquery-1.5.2.min.js","js/chosen/chosen.jquery.min.js",
            "js/apply_chosen.js","js/conditional_fields_setup.js")

    #list_display_links = ('vehicle',)
    list_display_links = ('vehicle_for_display',)

    list_display = make_DefaultAdminAuditTable(MyVehicalsProxy).list_display
    dont_display = ['notes','parking_number','parking_number_year','created_by',
        'last_updated_by','parking_location','user','non_cred_first_name','non_cred_last_name','non_cred_dept_company',
        'user_entered_vehicle_make', 'user_entered_vehicle_model','color','vehicle']
    for item in dont_display:
        list_display.remove(item)
    list_display.insert(0,'vehicle_for_display')

    fields =  ['vehicle','user_entered_vehicle_make', 'user_entered_vehicle_model','color','license_plate',
        'license_plate_state','current_living_arrangement','current_apt_number',
        'agree_to_TOS','active'] #'parking_number','notes'

    def queryset(self, request):
        #Only show my own vehicles
        results = VehicleRegistration.objects.filter(user=request.user)
        return results

    def save_model(self, request, obj, form, change):
        """Users can't edit anything if 'parking_number' and 'parking_number_year'
        are set. (except setting to inactive)
        Auto set user field to logged in user.

        We want to send an email if a new registration is added OR a record's agree_to_TOS
        goes from False to True        
        """
        msg_part = "" #store additional no save message
        if change: #update
            vr = VehicleRegistration.objects.get(pk=obj.id)
            if vr.parking_number and vr.parking_number_year:
                if vr.active and not form.cleaned_data['active']:
                    #always allow setting a registration to inactive
                    #(I'm just going to save on the model instance directly 
                    #and short-circuit the whole admin save process to I can 
                    #make sure only this one field is getting changed.)                    
                    vr.active = False
                    vr.save()            
                    messages.warning(request, "Registration %s was set to inactive." % (vr))
                    msg_part = "other "

                #Hide success messages so it doesn't say succeeded when I'm failing it
                messages.set_level(request, messages.WARNING)
                messages.error(request, 
                    "Once a Parking Permit has been assigned, no %sdata can be changed. Please contact security if you need to change your information." % msg_part)
            else:
                #An existing record without an assigned parking number and year is being changed
                if not vr.agree_to_TOS and form.cleaned_data['agree_to_TOS']:
                    #Send an email if user has agreed to TOS
                    obj.send_created_email()
                super(MyVehiclesAdmin, self).save_model(request, obj, form, change)
        else: #new record
            obj.user = request.user
            super(MyVehiclesAdmin, self).save_model(request, obj, form, change)
            #Send email to notify of new record
            if obj.active and obj.agree_to_TOS:
                obj.send_created_email()

   
admin.site.register(PendingVehicalsProxy, PendingVehiclesAdmin)
admin.site.register(Violation, ViolationAdmin)
admin.site.register(VehicleType, make_SensibleDefaultAdmin(VehicleType))
admin.site.register(VehicleColor, make_SensibleDefaultAdmin(VehicleColor))
admin.site.register(VehicleMake, make_SensibleDefaultAdmin(VehicleMake))
admin.site.register(LivingArrangement, make_SensibleDefaultAdmin(LivingArrangement))
admin.site.register(ParkingLocation, make_SensibleDefaultAdmin(ParkingLocation))
admin.site.register(Vehicle, make_DefaultAdminAuditTable(Vehicle))
admin.site.register(ViolationReason, make_SensibleDefaultAdmin(ViolationReason))
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(VehicleRegistration, VehicleRegistrationAdmin)
admin.site.register(OffboardedVehicalsProxy, OffboardedVehiclesAdmin)
admin.site.register(MyVehicalsProxy, MyVehiclesAdmin)
admin.site.register(LogEntryProxy, LogAdmin)


