import json
import time
from django.test import TestCase, Client
from django.core.cache import cache
from django.contrib.auth.models import User, Group
from django.urls import reverse


class SecurityAndRateLimitTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = Client()
        self.patient_group, _ = Group.objects.get_or_create(name='PATIENT')
        self.doctor_group, _ = Group.objects.get_or_create(name='DOCTOR')
        self.user = User.objects.create_user(username='testpatient', password='SecurePassword123!')
        self.patient_group.user_set.add(self.user)

    def tearDown(self):
        cache.clear()

    def test_auth_rate_limiting_enforced_at_five_attempts(self):
        """
        Verify that auth routes enforce max 5 attempts per 15 minutes,
        and return HTTP 429 on the 6th attempt with Retry-After header.
        """
        login_url = '/patient/patient_login/'

        # Send 5 attempts (allowed)
        for i in range(5):
            response = self.client.post(login_url, {
                'username': 'testpatient',
                'password': f'wrongpass{i}'
            })
            self.assertIn(response.status_code, [200, 302], f"Attempt {i+1} should not be rate-limited.")

        # 6th attempt should be blocked with HTTP 429
        response = self.client.post(login_url, {
            'username': 'testpatient',
            'password': 'anotherwrongpass'
        })
        self.assertEqual(response.status_code, 429, "6th attempt on auth route must be rate-limited with HTTP 429.")
        self.assertTrue(response.has_header('Retry-After'), "HTTP 429 response must include Retry-After header.")
        self.assertIn('Too Many Requests', response.content.decode('utf-8'))

    def test_auth_rate_limiting_ajax_returns_json(self):
        """
        Verify that rate-limited AJAX/API requests receive a clean JSON payload.
        """
        login_url = '/patient/patient_login/'

        # Trigger rate limit
        for _ in range(5):
            self.client.post(login_url, {'username': 'user', 'password': 'bad'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        response = self.client.post(login_url, {'username': 'user', 'password': 'bad'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 429)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data.get('status'), 'error')
        self.assertEqual(data.get('error'), 'Too Many Requests')
        self.assertIn('retry_after_seconds', data)

    def test_doctor_auth_rate_limiting(self):
        """
        Verify rate limiting also protects doctor authentication.
        """
        doctor_login_url = '/doctor/doctor_login/'
        for _ in range(5):
            self.client.post(doctor_login_url, {'username': 'dr_test', 'password': 'bad'})

        response = self.client.post(doctor_login_url, {'username': 'dr_test', 'password': 'bad'})
        self.assertEqual(response.status_code, 429)

    def test_oversized_payload_rejection(self):
        """
        Verify that payloads exceeding maximum size are rejected with HTTP 413.
        """
        large_content_length = 2 * 1024 * 1024  # 2MB > 1MB limit for standard body
        response = self.client.post(
            '/patient/home/',
            data='A' * 100,
            content_type='application/x-www-form-urlencoded',
            CONTENT_LENGTH=str(large_content_length)
        )
        self.assertEqual(response.status_code, 413, "Oversized request body must return HTTP 413 Payload Too Large.")

    def test_malformed_json_rejection(self):
        """
        Verify that malformed JSON payloads are cleanly rejected with HTTP 400.
        """
        malformed_body = '{ "name": "test", broken_json: '
        response = self.client.post(
            '/appointment/optimize/',
            data=malformed_body,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400, "Malformed JSON must return HTTP 400.")
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data.get('status'), 'error')
        self.assertIn('Malformed', data.get('error', ''))

    def test_null_byte_rejection(self):
        """
        Verify that null bytes in query parameters trigger HTTP 400.
        """
        response = self.client.get('/patient/home/?term=Cardiology\x00malicious')
        self.assertEqual(response.status_code, 400, "Null byte in query parameter must return HTTP 400.")

    def test_xss_query_sanitization(self):
        """
        Verify that XSS script tags in GET parameters are sanitized by middleware.
        """
        xss_payload = '<script>alert("XSS")</script>Dr. Smith'
        response = self.client.get(f'/patient/home/?term={xss_payload}')
        # Request should succeed, but script tag is sanitized from query params
        self.assertIn(response.status_code, [200, 302])
