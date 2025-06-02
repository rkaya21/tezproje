# createsu.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fazlayiz1.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()
username = "admin"
email = "admin@example.com"
password = "admin1234"

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, email=email, password=password)
    print("✅ Superuser created successfully!")
else:
    print("ℹ️ Superuser already exists.")
