import io
from PIL import Image

from rest_framework.test import APITestCase, APIClient
from rest_framework.authtoken.models import Token
from rest_framework import status

from django.contrib.auth.models import User
from django.urls import reverse
from django.contrib.contenttypes.models import ContentType

from apps.posts.models.posts import Post
from apps.comments.models.comment import Comment
from apps.comments.models.minor_comment import MinorComment


class ImageAPITests(APITestCase):
    def generate_photo_file(self) -> io.BytesIO:
        file = io.BytesIO()
        image = Image.new('RGBA', size=(100, 100), color=(155, 0, 0))
        image.save(file, 'png')
        file.name = 'test.png'
        file.seek(0)
        return file

    def setUp(self):
        self.test_user1 = User.objects.create(username='Guido', password='python123', email='emails@com.com')
        self.test_user1_token = 'Token ' + Token.objects.create(user=self.test_user1).key

        self.test_user2 = User.objects.create(username='Linus', password='linux123', email='email@com.com')
        self.test_user2_token = 'Token ' + Token.objects.create(user=self.test_user2).key

        post = Post.objects.create(
            profile=self.test_user1.profile.get(),
            title='Title',
            content='Hello, Ouvert!',
            content_object=self.test_user2.profile.get()
        )
        post_content_type = ContentType.objects.get_for_id(10)
        comment = Comment.objects.create(
            profile=self.test_user1.profile.get(),
            content='it is a coment',
            content_type=ContentType.objects.get_for_id(10),
            object_id=post.id
        )
        minor_comment = MinorComment.objects.create(
            profile=self.test_user1.profile.get(),
            main_comment=comment,
            content='itis a minor comment'
        )

    def test_create_image(self):
        """
        Test that authenticated user can create image for its profile.
        """
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=self.test_user1_token)
        user_profile = self.test_user1.profile.get()
        count_images_before = user_profile.images.count()
        image_data = {
            'caption': '',
            'image': self.generate_photo_file(),
            'content_type': 9,
            'object_id': user_profile.id
        }
        url = reverse('images-list')

        response = client.post(url, image_data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue('id' in response.data)
        self.assertTrue('profile' in response.data)
        self.assertTrue('caption' in response.data)
        self.assertTrue('created' in response.data)
        self.assertTrue('image' in response.data)
        self.assertTrue('content_type' in response.data)
        self.assertTrue('object_id' in response.data)
        self.assertTrue('content_object' in response.data)
        self.assertEqual(user_profile.images.count(), count_images_before + 1)

    def test_create_image_by_not_authenticated_user(self):
        """
        Test that not authenticated user cannot create an image.
        """
        user_profile = self.test_user1.profile.get()
        count_images_before = user_profile.images.count()
        image_data = {
            'caption': '',
            'image': self.generate_photo_file(),
            'content_type': 9,
            'object_id': user_profile.id
        }
        url = reverse('images-list')

        response = self.client.post(url, image_data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(user_profile.images.count(), count_images_before)

    def test_create_image_for_others_profile(self):
        """
        Test that user cannot create image for others profile.
        """
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=self.test_user1_token)
        user_profile = self.test_user2.profile.get()
        count_images_before = user_profile.images.count()
        image_data = {
            'caption': '',
            'image': self.generate_photo_file(),
            'content_type': 9,
            'object_id': user_profile.id
        }
        url = reverse('images-list')

        response = client.post(url, image_data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(user_profile.images.count(), count_images_before)

    def test_patch_request_to_image(self):
        """
        Test that user can patch its image.
        """
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=self.test_user1_token)
        user_profile = self.test_user1.profile.get()
        image_data = {
            'caption': '',
            'image': self.generate_photo_file(),
            'content_type': 9,
            'object_id': user_profile.id
        }
        url = reverse('images-list')
        response = client.post(url, image_data, format='multipart')
        count_images_before = user_profile.images.count()

        url = f"{reverse('images-list')}{response.data['id']}/"
        updated_image_data = {
            'caption': 'New caption',
            'image': self.generate_photo_file(),
            'content_type': 9,
            'object_id': user_profile.id
        }
        response = client.patch(url, updated_image_data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['caption'], updated_image_data['caption'])
        self.assertEqual(user_profile.images.count(), count_images_before)

    def test_patch_request_by_not_owner(self):
        """
        Test that user cannot send `PATCH` request to others image.
        """
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=self.test_user1_token)
        user_profile = self.test_user1.profile.get()
        image_data = {
            'caption': '',
            'image': self.generate_photo_file(),
            'content_type': 9,
            'object_id': user_profile.id
        }
        url = reverse('images-list')
        response = client.post(url, image_data, format='multipart')
        count_images_before = user_profile.images.count()

        url = f"{reverse('images-list')}{response.data['id']}/"
        updated_image_data = {
            'caption': 'New caption',
            'image': self.generate_photo_file(),
            'content_type': 9,
            'object_id': user_profile.id
        }
        client.credentials(HTTP_AUTHORIZATION=self.test_user2_token)
        response = client.patch(url, updated_image_data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(user_profile.images.count(), count_images_before)

    def test_put_request_to_image(self):
        """
        Test that user can send `PUT` request to its image.
        """
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=self.test_user1_token)
        user_profile = self.test_user1.profile.get()
        image_data = {
            'caption': '',
            'image': self.generate_photo_file(),
            'content_type': 9,
            'object_id': user_profile.id
        }
        url = reverse('images-list')
        response = client.post(url, image_data, format='multipart')
        count_images_before = user_profile.images.count()

        url = f"{reverse('images-list')}{response.data['id']}/"
        updated_image_data = {
            'caption': 'New caption',
            'image': self.generate_photo_file(),
            'content_type': 9,
            'object_id': user_profile.id
        }
        response = client.put(url, updated_image_data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['caption'], updated_image_data['caption'])
        self.assertEqual(user_profile.images.count(), count_images_before)

    def test_put_request_to_others_image(self):
        """
        Test that user cannot send `PUT` request to others image.
        """
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=self.test_user1_token)
        user_profile = self.test_user1.profile.get()
        image_data = {
            'caption': '',
            'image': self.generate_photo_file(),
            'content_type': 9,
            'object_id': user_profile.id
        }
        url = reverse('images-list')
        response = client.post(url, image_data, format='multipart')
        count_images_before = user_profile.images.count()

        url = f"{reverse('images-list')}{response.data['id']}/"
        updated_image_data = {
            'caption': 'New caption',
            'image': self.generate_photo_file(),
            'content_type': 9,
            'object_id': user_profile.id
        }
        client.credentials(HTTP_AUTHORIZATION=self.test_user2_token)
        response = client.put(url, updated_image_data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(user_profile.images.count(), count_images_before)

    def test_delete_request_to_image(self):
        """
        Test that user can send `delete` request to its image.
        """
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=self.test_user1_token)
        user_profile = self.test_user1.profile.get()
        image_data = {
            'caption': '',
            'image': self.generate_photo_file(),
            'content_type': 9,
            'object_id': user_profile.id
        }
        url = reverse('images-list')
        response = client.post(url, image_data, format='multipart')
        count_images_before = user_profile.images.count()

        url = f"{reverse('images-list')}{response.data['id']}/"

        response = client.delete(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(user_profile.images.count(), count_images_before - 1)

    def test_delete_request_by_not_owner(self):
        """
        Test that user cannot send `DELETE` request to others image.
        """
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=self.test_user1_token)
        user_profile = self.test_user1.profile.get()
        image_data = {
            'caption': '',
            'image': self.generate_photo_file(),
            'content_type': 9,
            'object_id': user_profile.id
        }
        url = reverse('images-list')
        response = client.post(url, image_data, format='multipart')
        count_images_before = user_profile.images.count()

        url = f"{reverse('images-list')}{response.data['id']}/"

        client.credentials(HTTP_AUTHORIZATION=self.test_user2_token)
        response = client.delete(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(user_profile.images.count(), count_images_before)

    def test_create_image_for_post(self):
        """
        Test that image can be created for post.
        """
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=self.test_user1_token)
        user_profile = self.test_user1.profile.get()
        image_data = {
            'caption': '',
            'image': self.generate_photo_file(),
            'content_type': 10,
            'object_id': Post.objects.last().id
        }
        count_images_before = Post.objects.last().images.count()
        url = reverse('images-list')
        response = client.post(url, image_data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue('caption' in response.data)
        self.assertTrue('image' in response.data)
        self.assertTrue('content_type' in response.data)
        self.assertTrue('object_id' in response.data)
        self.assertEqual(Post.objects.last().images.count(), count_images_before + 1)

    def test_create_image_for_profile(self):
        """
        Test that image can be created for user profile.
        """
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=self.test_user1_token)
        user_profile = self.test_user1.profile.get()
        image_data = {
            'caption': '',
            'image': self.generate_photo_file(),
            'content_type': 9,
            'object_id': user_profile.id
        }
        count_images_before = user_profile.images.count()
        url = reverse('images-list')
        response = client.post(url, image_data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue('caption' in response.data)
        self.assertTrue('image' in response.data)
        self.assertTrue('content_type' in response.data)
        self.assertTrue('object_id' in response.data)
        self.assertEqual(user_profile.images.count(), count_images_before + 1)

    def test_create_image_for_comment(self):
        """
        Test that image can be created for comment.
        """
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=self.test_user1_token)
        user_profile = self.test_user1.profile.get()
        image_data = {
            'caption': '',
            'image': self.generate_photo_file(),
            'content_type': 12,
            'object_id': Comment.objects.last().id,
        }
        url = reverse('images-list')
        response = client.post(url, image_data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue('caption' in response.data)
        self.assertTrue('image' in response.data)
        self.assertTrue('content_type' in response.data)
        self.assertTrue('object_id' in response.data)

    def test_create_image_for_minor_comment(self):
        """
        Test that image can be created for minor comment
        """
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=self.test_user1_token)
        user_profile = self.test_user1.profile.get()
        image_data = {
            'caption': '',
            'image': self.generate_photo_file(),
            'content_type': 13,
            'object_id': MinorComment.objects.last().id
        }
        count_images_before = MinorComment.objects.last().images.count()
        url = reverse('images-list')
        response = client.post(url, image_data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue('caption' in response.data)
        self.assertTrue('image' in response.data)
        self.assertTrue('content_type' in response.data)
        self.assertTrue('object_id' in response.data)
        self.assertEqual(MinorComment.objects.last().images.count(), count_images_before + 1)
