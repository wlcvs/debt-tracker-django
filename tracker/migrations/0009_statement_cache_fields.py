from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0008_add_llm_feedback'),
    ]

    operations = [
        migrations.AddField(
            model_name='statement',
            name='algo_results',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name='statement',
            name='llm_results',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name='statement',
            name='extracted_text',
            field=models.TextField(blank=True, default=''),
        ),
    ]
