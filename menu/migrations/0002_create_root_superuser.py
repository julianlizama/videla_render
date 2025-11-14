from django.db import migrations

def create_root_superuser(apps, schema_editor):
    from django.contrib.auth import get_user_model
    User = get_user_model()

    username = "root"
    password = "12345"
    email = "root@example.com"

    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
        )
        print("=== Superusuario 'root' creado ===")
    else:
        print("=== Superusuario 'root' ya existía ===")


def delete_root_superuser(apps, schema_editor):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    User.objects.filter(username="root").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("menu", "0001_initial"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.RunPython(create_root_superuser, delete_root_superuser),
    ]
