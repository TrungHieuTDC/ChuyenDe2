# Generated by Django 4.2.5 on 2023-11-21 13:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("social_network", "0018_remove_comment_comments_closed_post_comments_closed"),
    ]

    operations = [
        migrations.AlterField(
            model_name="membership",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "Pending"),
                    ("approved", "Approved"),
                    ("banned", "Banned"),
                ],
                default="pending",
                max_length=20,
            ),
        ),
    ]
