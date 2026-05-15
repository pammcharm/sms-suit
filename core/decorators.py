from functools import wraps

from django.http import HttpResponseForbidden
from django.db.models import Q
from django.shortcuts import redirect

from .models import ActivityLog, BusinessProfile, Permission, UserBusinessAccess


def _is_authenticated(request):
    user = getattr(request, 'user', None)
    return user is not None and getattr(user, 'is_authenticated', False)


def _login_redirect():
    return redirect('auth')


def _get_business_from_request(request):
    business = getattr(request, 'business', None) or getattr(request, 'active_profile', None)
    if business:
        return business

    profile_id = request.session.get('active_profile_id')
    if not profile_id:
        return None
    return BusinessProfile.objects.filter(pk=profile_id).first()


def _access_filter(user, business, request=None):
    filters = {'business': business, 'is_active': True}
    if user is not None and getattr(user, 'is_authenticated', False):
        return UserBusinessAccess.objects.filter(**filters, user=user)

    if request is None:
        return UserBusinessAccess.objects.none()

    email = getattr(user, 'email', '') or request.session.get('email', '')
    access = UserBusinessAccess.objects.filter(**filters)
    identity_filter = Q()
    if email:
        identity_filter |= Q(email__iexact=email)
    if not identity_filter:
        return UserBusinessAccess.objects.none()
    return access.filter(identity_filter)


def _is_owner(user, business, request=None):
    if not business:
        return False
    if user is not None and getattr(user, 'is_authenticated', False) and business.owner_email:
        return bool(getattr(user, 'email', '')) and user.email.lower() == business.owner_email.lower()
    if request is None:
        return False
    email = getattr(user, 'email', '') or request.session.get('email', '')
    return bool(email and business.owner_email and email.lower() == business.owner_email.lower())


def get_user_role(user, business):
    access = _access_filter(user, business).select_related('role').first()
    return access.role if access else None


def get_user_permissions(user, business):
    access = _access_filter(user, business).select_related('role').first()
    if not access:
        return Permission.objects.none()
    return Permission.objects.filter(role_permissions__role=access.role).distinct()


def user_has_permission(user, business, permission_code):
    if not business:
        return False
    access = _access_filter(user, business).select_related('role').first()
    if not access:
        return False
    return access.role.role_permissions.filter(permission__code=permission_code).exists()


def requires_business_access(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not _is_authenticated(request):
            return _login_redirect()

        business = _get_business_from_request(request)
        if not business:
            return HttpResponseForbidden('Business context is not available')

        user = getattr(request, 'user', None)
        if _is_owner(user, business, request) or _access_filter(user, business, request).exists():
            request.business = business
            return view_func(request, *args, **kwargs)

        return HttpResponseForbidden('You do not have access to this business')

    return wrapper


def has_permission(permission_code):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not _is_authenticated(request):
                return _login_redirect()

            business = _get_business_from_request(request)
            if not business:
                return HttpResponseForbidden('Business context is not available')

            user = getattr(request, 'user', None)
            if _is_owner(user, business, request) or _access_filter(user, business, request).filter(
                role__role_permissions__permission__code=permission_code
            ).exists():
                request.business = business
                return view_func(request, *args, **kwargs)

            return HttpResponseForbidden(f'You do not have permission to access this resource: {permission_code}')

        return wrapper

    return decorator


def requires_role(role_name):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not _is_authenticated(request):
                return _login_redirect()

            business = _get_business_from_request(request)
            if not business:
                return HttpResponseForbidden('Business context is not available')

            user = getattr(request, 'user', None)
            if _is_owner(user, business, request) or _access_filter(user, business, request).filter(role__name=role_name).exists():
                request.business = business
                return view_func(request, *args, **kwargs)

            return HttpResponseForbidden(f'You must have the {role_name} role to access this resource')

        return wrapper

    return decorator


def is_business_owner(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not _is_authenticated(request):
            return _login_redirect()

        business = _get_business_from_request(request)
        if not business:
            return HttpResponseForbidden('Business context is not available')

        if _is_owner(getattr(request, 'user', None), business, request):
            request.business = business
            return view_func(request, *args, **kwargs)

        return HttpResponseForbidden('Only the business owner can access this resource')

    return wrapper


def log_user_activity(user, business, action_type, resource_type, resource_id=None, old_values=None, new_values=None, notes='', request=None):
    actor = 'System'
    if user is not None and getattr(user, 'is_authenticated', False):
        actor = user.get_username()
    elif request is not None:
        actor = request.session.get('email') or 'System'

    details = [f'{action_type.title()} {resource_type}']
    if resource_id is not None:
        details.append(f'#{resource_id}')
    if notes:
        details.append(f'- {notes}')

    return ActivityLog.objects.create(
        profile=business,
        actor=actor,
        action=' '.join(details),
    )


def log_activity(action_type, resource_type):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            response = view_func(request, *args, **kwargs)
            business = _get_business_from_request(request)
            if business:
                log_user_activity(
                    user=getattr(request, 'user', None),
                    business=business,
                    action_type=action_type,
                    resource_type=resource_type,
                    request=request,
                )
            return response

        return wrapper

    return decorator


permission_required = has_permission
role_required = requires_role
