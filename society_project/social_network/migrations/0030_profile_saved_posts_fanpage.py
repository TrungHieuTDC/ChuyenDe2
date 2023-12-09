# Generated by Django 4.2.5 on 2023-11-30 12:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("social_fanpage", "0004_albumfanpage"),
        ("social_network", "0029_profile_background_avatar"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="saved_posts_fanpage",
            field=models.ManyToManyField(
                related_name="saved_by_profiles_fanpage", to="social_fanpage.fanpage"
            ),
        ),
    ]
