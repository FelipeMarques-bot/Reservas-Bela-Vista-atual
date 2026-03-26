import cloudinary.uploader
import cloudinary
from django.core.files.storage import Storage
from django.conf import settings
import os

class CloudinaryMediaStorage(Storage):
    def _save(self, name, content):
        folder = os.path.dirname(name)
        result = cloudinary.uploader.upload(
            content,
            folder=folder,
            resource_type='auto',
            use_filename=True,
            unique_filename=False,
        )
        return result['public_id']

    def url(self, name):
        return cloudinary.CloudinaryImage(name).build_url()

    def exists(self, name):
        return False

    def _open(self, name, mode='rb'):
        import urllib.request
        url = self.url(name)
        response = urllib.request.urlopen(url)
        from django.core.files.base import ContentFile
        return ContentFile(response.read())

    def delete(self, name):
        cloudinary.uploader.destroy(name, resource_type='auto')
