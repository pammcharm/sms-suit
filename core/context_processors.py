from .models import BusinessProfile


MODULES_BY_BUSINESS = {
    'shop': ['pos', 'inventory', 'customers', 'payments', 'reports', 'integrations'],
    'boutique': ['pos', 'inventory', 'customers', 'payments', 'reports', 'integrations'],
    'restaurant': ['pos', 'inventory', 'customers', 'payments', 'employees', 'hospitality', 'expenses', 'reports', 'integrations'],
    'pharmacy': ['pos', 'inventory', 'customers', 'payments', 'suppliers', 'reports', 'integrations'],
    'hardware': ['pos', 'inventory', 'customers', 'payments', 'suppliers', 'transfers', 'reports', 'integrations'],
    'hotel': ['pos', 'inventory', 'customers', 'payments', 'employees', 'hospitality', 'expenses', 'reports', 'integrations'],
    'mini_market': ['pos', 'inventory', 'customers', 'payments', 'employees', 'expenses', 'reports', 'integrations'],
    'wholesale': ['pos', 'inventory', 'customers', 'payments', 'suppliers', 'transfers', 'reports', 'integrations'],
    'salon': ['pos', 'customers', 'payments', 'employees', 'expenses', 'reports', 'integrations'],
    'clinic': ['customers', 'payments', 'employees', 'expenses', 'reports', 'integrations'],
    'garage': ['pos', 'inventory', 'customers', 'payments', 'employees', 'expenses', 'suppliers', 'reports', 'integrations'],
    'laundry': ['pos', 'customers', 'payments', 'employees', 'expenses', 'reports', 'integrations'],
    'construction': ['customers', 'payments', 'employees', 'expenses', 'suppliers', 'reports', 'integrations'],
    'agency': ['customers', 'payments', 'employees', 'expenses', 'reports', 'integrations'],
    'school': ['customers', 'employees', 'payments', 'expenses', 'reports', 'integrations'],
    'club': ['customers', 'employees', 'payments', 'expenses', 'reports', 'integrations'],
    'other': ['pos', 'inventory', 'customers', 'payments', 'employees', 'expenses', 'hospitality', 'suppliers', 'transfers', 'reports', 'integrations'],
}


def active_business(request):
    profile = None
    modules = []
    profile_id = request.session.get('active_profile_id')
    if profile_id and request.user.is_authenticated:
        profile = BusinessProfile.objects.filter(pk=profile_id).first()
        if profile:
            modules = profile.selected_modules or MODULES_BY_BUSINESS.get(profile.business_type, MODULES_BY_BUSINESS['other'])
    return {
        'active_profile': profile,
        'active_modules': modules,
    }
