"""
seed_categories.py — Populate the 10 default system categories.

Usage:
    python manage.py seed_categories
"""
from django.core.management.base import BaseCommand

from tracker.models import Category

CATEGORIES = [
    {'name': 'Study / Learning',          'icon': '📚', 'color': '#2196F3'},
    {'name': 'Career / Skills',           'icon': '💼', 'color': '#9C27B0'},
    {'name': 'Fitness / Body',            'icon': '💪', 'color': '#F44336'},
    {'name': 'Mental Health',             'icon': '🧠', 'color': '#00BCD4'},
    {'name': 'Nutrition / Diet',          'icon': '🥦', 'color': '#4CAF50'},
    {'name': 'Finance / Money',           'icon': '💰', 'color': '#FF9800'},
    {'name': 'Relationships',             'icon': '❤️',  'color': '#E91E63'},
    {'name': 'Personal Goals',            'icon': '🎯', 'color': '#673AB7'},
    {'name': 'Leisure / Entertainment',   'icon': '🎮', 'color': '#FF5722'},
    {'name': 'Lifestyle / Discipline',    'icon': '⏰', 'color': '#607D8B'},
]


class Command(BaseCommand):
    help = 'Seed the database with 10 default system categories'

    def handle(self, *args, **options):
        created = 0
        for data in CATEGORIES:
            _, was_created = Category.objects.get_or_create(
                name=data['name'],
                defaults={'icon': data['icon'], 'color': data['color']},
            )
            if was_created:
                created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Done. {created} new categories created, '
                f'{len(CATEGORIES) - created} already existed.'
            )
        )
