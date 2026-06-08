Set-Location 'D:\sol\test-leave'
$env:DJANGO_DEBUG = 'True'
$env:DJANGO_SECRET_KEY = 'dev-local-secret-key'
$env:DJANGO_ALLOWED_HOSTS = 'localhost,127.0.0.1,[::1]'
$env:DEFAULT_IMPORT_PASSWORD = 'ChangeMe123!'
python manage.py runserver 127.0.0.1:8000
