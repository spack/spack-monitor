# Generated by Django 3.2.8 on 2021-10-29 20:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0003_attribute_json_value"),
    ]

    operations = [
        migrations.AlterField(
            model_name="installfile",
            name="name",
            field=models.CharField(
                help_text="The name of the install file, with user prefix removed",
                max_length=500,
            ),
        ),
    ]
