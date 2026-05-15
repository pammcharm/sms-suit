import logging

from django.conf import settings
from django.http import Http404
from django.shortcuts import redirect, render

from .models import BusinessProfile


class DjangoSessionRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        allowed_prefixes = (
            '/auth/',
            '/verify-email/',
            '/tour/',
            '/logout/',
            '/admin/',
            '/static/',
        )
        if request.path == '/auth' or request.path.startswith(allowed_prefixes):
            return self.get_response(request)
        if not request.user.is_authenticated:
            return redirect('auth')
        # Email verification happens before opening any business control panel.
        if request.user.is_authenticated:
            try:
                if not request.user.account_profile.email_verified:
                    return redirect('verify_email')
            except Exception:
                return redirect('verify_email')

        setup_paths = (
            '/workspace/',
            '/onboarding/',
            '/logout/',
        )
        if request.path.startswith(setup_paths):
            return self.get_response(request)

        profile_id = request.session.get('active_profile_id')
        if not profile_id:
            return redirect('workspace')
        profile = BusinessProfile.objects.filter(pk=profile_id).first()
        has_access = False
        if profile:
            if profile.owner_email and request.user.email and profile.owner_email.lower() == request.user.email.lower():
                has_access = True
            else:
                has_access = profile.user_accesses.filter(user=request.user, is_active=True).exists()
        if not has_access:
            request.session.pop('active_profile_id', None)
            return redirect('workspace')
        request.business = profile
        request.active_profile = profile
        if not profile.setup_completed:
            return redirect('onboarding')
        return self.get_response(request)


logger = logging.getLogger(__name__)


class FriendlyErrorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            return self.get_response(request)
        except Http404:
            return render(request, 'core/error.html', {
                'title': 'Page not found',
                'message': 'We could not find that page. Please go back and try again.',
            }, status=404)
        except Exception as exc:
            if settings.DEBUG:
                raise
            logger.exception('Unhandled application error on %s', request.path, exc_info=exc)
            return render(request, 'core/error.html', {
                'title': 'Something went wrong',
                'message': 'The system could not complete that action. Please try again or return to your workspace.',
            }, status=500)
