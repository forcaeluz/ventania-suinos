from django.db import migrations

def move_exits(apps, schema_editor):
    # We can't import the Person model directly as it may be a newer
    # version than this migration expects. We use the historical version.
    AnimalExits = apps.get_model('flocks', 'AnimalExits')
    AnimalFarmExit = apps.get_model('flocks', 'AnimalFarmExit')
    AnimalFlockExit = apps.get_model('flocks', 'AnimalFlockExit')
    AnimalSeparation = apps.get_model('flocks', 'AnimalSeparation')
    for animal_exit in AnimalExits.objects.all():
        farm_exit = AnimalFarmExit(date=animal_exit.date,
                                   weight=animal_exit.total_weight,
                                   number_of_animals=animal_exit.number_of_animals)
        farm_exit.save()
        flock_exit = AnimalFlockExit(weight=animal_exit.total_weight,
                                     number_of_animals=animal_exit.number_of_animals,
                                     flock=animal_exit.flock,
                                     farm_exit=farm_exit)
        flock_exit.save()
        separations = animal_exit.animalseparation_set.all()
        for separation in separations:
            separation.flockexit_id = flock_exit.id
            separation.save()

        animal_exit.delete()

class Migration(migrations.Migration):

    dependencies = [
        ('flocks', '0012_auto_20170604_1025'),
    ]

    operations = [
        migrations.RunPython(move_exits),
    ]