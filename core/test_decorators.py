from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpResponse
from django.test import RequestFactory, TestCase

from .decorators import (
    get_user_permissions,
    get_user_role,
    has_permission,
    is_business_owner,
    log_activity,
    requires_business_access,
    requires_role,
    role_required,
    user_has_permission,
)
from .models import ActivityLog, BusinessProfile, Permission, Role, RolePermission, UserBusinessAccess


def ok_view(request):
    return HttpResponse('ok')


class PermissionDecoratorTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.business = BusinessProfile.objects.create(
            name='Test Business',
            owner_email='owner@example.com',
            setup_completed=True,
        )
        self.user = get_user_model().objects.create_user(
            username='manager',
            email='manager@example.com',
            password='password',
        )
        self.role, _ = Role.objects.get_or_create(name='manager', defaults={'display_name': 'Manager'})
        self.permission, _ = Permission.objects.get_or_create(code='view_reports', defaults={'name': 'View reports'})
        RolePermission.objects.get_or_create(role=self.role, permission=self.permission)
        UserBusinessAccess.objects.create(user=self.user, business=self.business, role=self.role)

    def request(self, user=None, business=None, session=None):
        request = self.factory.get('/')
        SessionMiddleware(lambda req: None).process_request(request)
        request.session.update(session or {})
        request.user = user if user is not None else self.user
        if business is not None:
            request.business = business
        return request

    def test_has_permission_allows_user_with_role_permission(self):
        response = has_permission('view_reports')(ok_view)(self.request(business=self.business))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'ok')

    def test_has_permission_denies_missing_permission(self):
        response = has_permission('delete_business')(ok_view)(self.request(business=self.business))

        self.assertEqual(response.status_code, 403)
        self.assertIn(b'delete_business', response.content)

    def test_requires_role_allows_matching_role(self):
        response = requires_role('manager')(ok_view)(self.request(business=self.business))

        self.assertEqual(response.status_code, 200)

    def test_role_required_alias_denies_non_matching_role(self):
        response = role_required('admin')(ok_view)(self.request(business=self.business))

        self.assertEqual(response.status_code, 403)
        self.assertIn(b'admin', response.content)

    def test_requires_business_access_allows_any_active_access(self):
        response = requires_business_access(ok_view)(self.request(business=self.business))

        self.assertEqual(response.status_code, 200)

    def test_is_business_owner_allows_owner_email(self):
        owner = get_user_model().objects.create_user(
            username='owner',
            email='owner@example.com',
            password='password',
        )
        request = self.request(
            user=owner,
            business=self.business,
        )

        response = is_business_owner(ok_view)(request)

        self.assertEqual(response.status_code, 200)

    def test_unauthenticated_user_redirects_to_auth(self):
        response = has_permission('view_reports')(ok_view)(self.request(user=AnonymousUser(), business=self.business))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/auth/')

    def test_helper_functions_return_role_and_permissions(self):
        self.assertEqual(get_user_role(self.user, self.business), self.role)
        self.assertTrue(user_has_permission(self.user, self.business, 'view_reports'))
        self.assertIn(self.permission, list(get_user_permissions(self.user, self.business)))

    def test_log_activity_creates_activity_log_after_view(self):
        request = self.request(business=self.business)

        response = log_activity('view', 'report')(ok_view)(request)

        self.assertEqual(response.status_code, 200)
        log = ActivityLog.objects.get(profile=self.business)
        self.assertEqual(log.actor, 'manager')
        self.assertEqual(log.action, 'View report')
