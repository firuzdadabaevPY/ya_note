from http import HTTPStatus
from pytils.translit import slugify

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.models import Note
from notes.forms import WARNING

User = get_user_model()


class NoteCreation(TestCase):
    TITLE_NOTE = 'Note 1'
    TEXT_NOTE = 'It is text'
    SLUG_NOTE = 'slug_ab1'

    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('notes:add')
        cls.success_url = reverse('notes:success')
        cls.user = User.objects.create(username='Firuz')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)
        cls.form_data = {
            'title': cls.TITLE_NOTE,
            'text': cls.TEXT_NOTE,
            'slug': cls.SLUG_NOTE,
        }

    def test_anonymous_user_cant_create_note(self):
        login_url = reverse('users:login')
        response = self.client.post(self.url, data=self.form_data)
        self.redirect_url = f'{login_url}?next={self.url}'
        self.assertRedirects(response, self.redirect_url)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 0)

    def test_user_can_create_note(self):
        response = self.auth_client.post(self.url, data=self.form_data)
        self.assertRedirects(response, self.success_url)

        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)

        note = Note.objects.get()
        self.assertEqual(note.title, self.TITLE_NOTE)
        self.assertEqual(note.text, self.TEXT_NOTE)
        self.assertEqual(note.slug, self.SLUG_NOTE)


class TestNotetEditDelete(TestCase):
    NOTE_TEXT = 'It is note TEXT'
    TITLE_NOTE = 'Note 1'
    SLUG_NOTE = 'slug_ab1'

    NEW_NOTE_TEXT = 'It is new note TEXT'

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор комментария')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)

        cls.reader = User.objects.create(username='Читатель')
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)

        cls.note_data = {
            'title': cls.TITLE_NOTE,
            'text': cls.NOTE_TEXT,
            'slug': cls.SLUG_NOTE,
            'author': cls.author,
        }

        cls.note = Note.objects.create(
            title=cls.note_data['title'],
            text=cls.note_data['text'],
            slug=cls.note_data['slug'],
            author=cls.author,
        )

        cls.url_list = reverse('notes:list')
        cls.add_note_url = reverse('notes:add')
        cls.success_url = reverse('notes:success')
        cls.edit_url = reverse('notes:edit', args=(cls.note.slug,))
        cls.delete_url = reverse('notes:delete', args=(cls.note.slug,))

        cls.form_data = {
            'title': cls.TITLE_NOTE,
            'text': cls.NEW_NOTE_TEXT,
            'slug': cls.SLUG_NOTE,
        }

    def test_author_can_delete_comment(self):
        response = self.author_client.delete(self.delete_url)
        self.assertRedirects(response, self.success_url)
        note_count = Note.objects.count()
        self.assertEqual(note_count, 0)

    def test_user_cant_delete_another_note(self):
        response = self.reader_client.delete(self.delete_url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

        note_count = Note.objects.count()
        self.assertEqual(note_count, 1)

    def test_author_can_edit_note(self):
        response = self.author_client.post(self.edit_url, data=self.form_data)
        self.assertRedirects(response, self.success_url)
        self.note.refresh_from_db()
        self.assertEqual(self.note.text, self.NEW_NOTE_TEXT)

    def test_user_cant_edit_another_note(self):
        response = self.reader_client.post(self.edit_url, data=self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.note.refresh_from_db()
        self.assertEqual(self.note.text, self.NOTE_TEXT)

    def test_not_unique_slug(self):
        response = self.author_client.post(
            self.add_note_url, data=self.note_data)
        self.assertEqual(Note.objects.count(), 1)

        self.assertFormError(
            response, form='form', field='slug',
            errors=(self.note.slug + WARNING))

    def test_empty_slug(self):
        self.note_data.pop('slug')
        response = self.author_client.post(
            self.add_note_url, data=self.note_data
        )
        self.assertEqual(Note.objects.count(), 2)
        self.assertRedirects(response, self.success_url)

        note = Note.objects.exclude(slug=self.SLUG_NOTE).get()
        expected_slug = slugify(note.title)[:100]

        self.assertEqual(note.slug, expected_slug)
