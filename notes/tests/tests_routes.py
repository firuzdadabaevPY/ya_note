from http import HTTPStatus

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from notes.models import Note


User = get_user_model()


class TestRoutes(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Firuz')
        cls.another_author = User.objects.create(username='Masrur')
        cls.note = Note.objects.create(
            title='First Note',
            text='Text',
            slug='first_note',
            author=cls.author,
        )

    def test_page_availabality_for_anonymous_user(self):
        urls = (
            'notes:home',
            'users:login',
            'users:logout',
            'users:signup',
        )

        for name in urls:
            with self.subTest(name=name):
                url = reverse(name)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_availability_for_owner_and_noOwner_user(self):
        '''The Test is for checking editing, deleting and detail show for owner of note and no owner'''
        user_statuses = (
            (self.author, HTTPStatus.OK),
            (self.another_author, HTTPStatus.NOT_FOUND)
        )

        for user, status in user_statuses:
            self.client.force_login(user)
            for name in ('notes:edit', 'notes:detail', 'notes:delete'):
                with self.subTest(user=user, name=name):
                    url = reverse(name, args=(self.note.slug,))
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, status)

    def test_availability_for_authorized_user(self):
        SUCCESS = HTTPStatus.OK
        users = (
            self.author,
            self.another_author
        )
        for user in users:
            self.client.force_login(user)
            for name in ('notes:add', 'notes:list', 'notes:success'):
                with self.subTest(user=user, name=name):
                    url = reverse(name)
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, SUCCESS)

    def test_redirect_for_anonymous_client(self):
        SLUG = (self.note.slug, )
        urls = (
            ('notes:add', None),
            ('notes:edit', SLUG),
            ('notes:detail', SLUG),
            ('notes:delete', SLUG),
            ('notes:list', None),
            ('notes:success', None)
        )

        for name, args in urls:
            login_url = reverse('users:login')
            with self.subTest(name=name):
                url = reverse(name, args=args)
                redirect_url = f'{login_url}?next={url}'
                response = self.client.get(url)
                self.assertRedirects(response, redirect_url)
