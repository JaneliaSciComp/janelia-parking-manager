
# Common project-wide code we want to run right away when server loads

import logging
import sys
sys.path.append('..')
import django_auth_ldap.backend
from django.contrib.auth.models import Group, User

logger = logging.getLogger('django_auth_ldap')
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)

# Some LDAP overhead - connect to the populate user signal to handle custom
# permissions based on LDAP description.
#to use this function, connect it to this signal
#django_auth_ldap.backend.populate_user.connect(update_groups_and_user_flags)
def update_groups_and_user_flags(sender, user=None, ldap_user=None, **kwargs):
    """
    Look at LDAP description
    if "Facilities - Security" in description can read/edit visitor table [1]
    if "Scientific Computing" or "Help Desk" then is superuser

    [1] This would work (if uncomment those lines below) however these users 
    are not set up properly in LDAP.  They have a random password assigned in
    LDAP and it is never synched with their Janelia password.  We are using 
    permanent Django users instead for them for now.
    """
    logger.info("in update_groups_and_user_flags: user: %s, ldap_user: %s" % (user,ldap_user))
    # Remember that every attribute maps to a list of values
    descriptions = ldap_user.attrs.get("description", [])
    description = (descriptions and descriptions[0] or '').lower()

    logger.info("description=%s" % description)

    user_group = Group.objects.get(name="ParkingPermitUser")
    staff_group = Group.objects.get(name="ViolationsUser")

    if "facilities - security" in description:
        user.groups.add(staff_group)
        user.groups.add(user_group)
        user.is_staff = True
        logger.info("add staff")
    else:
        user.is_staff = True
        #user.is_superuser = False
        user.groups.add(user_group)
        logger.info("added normal user")

# Some LDAP overhead - connect to the populate user signal to handle custom
# permissions based on LDAP description.
django_auth_ldap.backend.populate_user.connect(update_groups_and_user_flags)

