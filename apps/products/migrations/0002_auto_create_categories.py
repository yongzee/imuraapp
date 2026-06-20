from django.db import migrations

def create_default_categories(apps, schema_editor):
    Category = apps.get_model('products', 'Category')
    for name in ['All', 'Male', 'Female']:
        Category.objects.get_or_create(name=name)

class Migration(migrations.Migration):
    dependencies = [
        ('products', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_default_categories),
    ]
