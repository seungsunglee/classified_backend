# Generated by Django 3.2.7 on 2022-03-03 14:02

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('classifieds', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Option',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('term', models.IntegerField()),
                ('price', models.DecimalField(decimal_places=2, max_digits=8)),
            ],
            options={
                'ordering': ['term'],
            },
        ),
        migrations.CreateModel(
            name='Type',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slug', models.CharField(choices=[('fixed', 'FIXED'), ('highlight', 'HIGHLIGHT')], max_length=255)),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('index', models.IntegerField()),
                ('note', models.CharField(blank=True, max_length=255, null=True)),
            ],
            options={
                'ordering': ['index'],
            },
        ),
        migrations.CreateModel(
            name='PaymentHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('payment_intent', models.CharField(max_length=255)),
                ('total_price', models.DecimalField(decimal_places=2, max_digits=8)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('item', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='classifieds.item')),
                ('options', models.ManyToManyField(blank=True, to='promotion.Option')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddField(
            model_name='option',
            name='type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='promotion.type'),
        ),
    ]
