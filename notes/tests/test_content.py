from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from notes.models import Note
from notes.forms import NoteForm


User = get_user_model()


class TestAuthorizedPages(TestCase):
    LIST_PAGE_URL = reverse('notes:list')
    CREATED_NOTES_NUMBER = 10

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Firuz')

        all_news = [
            Note(
                title=f'Note {index}', text='Text',
                slug=f'note_{index}', author=cls.author,
            )
            for index in range(cls.CREATED_NOTES_NUMBER)
        ]

        Note.objects.bulk_create(all_news)

    def test_notes_count(self):
        self.client.force_login(self.author)
        response = self.client.get(self.LIST_PAGE_URL)
        object_list = response.context['object_list']
        notes_count = object_list.count()
        self.assertEqual(notes_count, self.CREATED_NOTES_NUMBER)

    def test_create_and_update_page_has_form(self):
        self.client.force_login(self.author)
        self.assertTrue(Note.objects.filter(slug='note_1').exists())
        urls = (
            ('notes:add', None),
            ('notes:edit', ('note_1', ))
        )
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                response = self.client.get(url)
                self.assertIn('form', response.context)
                self.assertIsInstance(response.context['form'], NoteForm)
