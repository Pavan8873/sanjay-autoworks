from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('jobcards', '0003_service_checksheet'),
    ]

    operations = [
        migrations.CreateModel(
            name='LabourCharge',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.CharField(max_length=200)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('jobcard', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='labour_charges', to='jobcards.jobcard')),
            ],
        ),
        migrations.CreateModel(
            name='ManualJobPart',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('quantity', models.PositiveIntegerField(default=1)),
                ('unit_price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('jobcard', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='manual_parts', to='jobcards.jobcard')),
            ],
        ),
        migrations.AlterField(
            model_name='jobcard',
            name='labor_rate',
            field=models.DecimalField(decimal_places=2, default=0, help_text='Per hour', max_digits=8),
        ),
    ]
