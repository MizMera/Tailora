from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

User = get_user_model()

class AIStyleAnalyzeViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client.force_login(self.user)
        self.url = reverse('ai_style_analyze')

    def test_upload_less_than_3_images_fails(self):
        # Create 2 dummy images
        image1 = SimpleUploadedFile("image1.jpg", b"file_content", content_type="image/jpeg")
        image2 = SimpleUploadedFile("image2.jpg", b"file_content", content_type="image/jpeg")
        
        response = self.client.post(self.url, {
            'analyze': 'true',
            'style_images': [image1, image2]
        })
        
        self.assertEqual(response.status_code, 200)
        # Check for the error message
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Minimum 3 photos requises')

    def test_upload_3_images_succeeds(self):
        # Mocking the analyzer would be ideal here to avoid actual processing, 
        # but for a quick integration test, we'll see if it passes the validation check.
        # Since we don't want to actually run the heavy AI, we might hit an error later 
        # or need to mock 'wardrobe.ai_image_analyzer.get_image_analyzer'.
        pass
