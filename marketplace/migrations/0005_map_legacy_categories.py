from django.db import migrations


def map_legacy_categories(apps, schema_editor):
    Listing = apps.get_model('marketplace', 'Listing')
    category_mapping = {
        'HOUSING': 'DORM_LIVING',
        'FURNITURE': 'DORM_LIVING',
        'CLOTHING': 'FASHION',
        'LAB_SUPPLIES': 'STATIONERY',
    }
    for old_cat, new_cat in category_mapping.items():
        Listing.objects.filter(category=old_cat).update(category=new_cat)


def reverse_legacy_categories(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('marketplace', '0004_alter_listing_category'),
    ]

    operations = [
        migrations.RunPython(map_legacy_categories, reverse_legacy_categories),
    ]
