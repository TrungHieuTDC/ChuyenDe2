# Generated by Django 4.2.5 on 2023-11-28 11:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("social_profile", "0005_educationuser"),
    ]

    operations = [
        migrations.AddField(
            model_name="educationuser",
            name="end_date",
            field=models.DateField(blank=True, null=True),
        ),
    ]
