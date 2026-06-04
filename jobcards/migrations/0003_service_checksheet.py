from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('jobcards', '0002_add_walkaround_and_advisor'),
    ]

    operations = [
        migrations.CreateModel(
            name='ServiceChecksheet',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('checklist', models.JSONField(blank=True, default=dict)),
                ('battery_voltage', models.CharField(blank=True, max_length=20)),
                ('battery_cell_1', models.CharField(blank=True, max_length=20)),
                ('battery_cell_2', models.CharField(blank=True, max_length=20)),
                ('battery_cell_3', models.CharField(blank=True, max_length=20)),
                ('battery_cell_4', models.CharField(blank=True, max_length=20)),
                ('battery_cell_5', models.CharField(blank=True, max_length=20)),
                ('battery_cell_6', models.CharField(blank=True, max_length=20)),
                ('brake_front_lhs', models.CharField(blank=True, max_length=20)),
                ('brake_front_rhs', models.CharField(blank=True, max_length=20)),
                ('brake_rear_lhs', models.CharField(blank=True, max_length=20)),
                ('brake_rear_rhs', models.CharField(blank=True, max_length=20)),
                ('brake_liners', models.TextField(blank=True)),
                ('diagnostics_report', models.TextField(blank=True)),
                ('job_remarks', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('jobcard', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='checksheet',
                    to='jobcards.jobcard',
                )),
            ],
        ),
    ]
