# Generated by Django 5.2 on 2025-04-29 22:22

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        (
            "quoridor",
            "0002_alter_fence_player_id_alter_game_current_player_id_and_more",
        ),
    ]

    operations = [
        migrations.CreateModel(
            name="Device",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("device_id", models.CharField(max_length=12, unique=True)),
                ("name", models.CharField(blank=True, max_length=100)),
                ("registered_at", models.DateTimeField(auto_now_add=True)),
                ("last_seen", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.AddField(
            model_name="game",
            name="player1_device",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="player1_games",
                to="quoridor.device",
            ),
        ),
        migrations.AddField(
            model_name="game",
            name="player2_device",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="player2_games",
                to="quoridor.device",
            ),
        ),
    ]
