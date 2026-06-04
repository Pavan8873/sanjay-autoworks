# Generated migration to remove unused vehicle types and convert to car/suv

from django.db import migrations


def convert_vehicle_types(apps, schema_editor):
    """Convert removed vehicle types to 'car' (default)."""
    Vehicle = apps.get_model('customers', 'Vehicle')
    
    # Map removed types to 'car' (the default type)
    removed_types = ['bike', 'scooter', 'truck', 'auto', 'other']
    
    for vehicle in Vehicle.objects.filter(vehicle_type__in=removed_types):
        vehicle.vehicle_type = 'car'
        vehicle.save()


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0003_fix_vehicle_type_case'),
    ]

    operations = [
        migrations.RunPython(convert_vehicle_types),
    ]
