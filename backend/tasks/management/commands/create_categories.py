from django.core.management.base import BaseCommand
from tasks.models import Category

class Command(BaseCommand):
    help = 'Create default categories'

    def handle(self, *args, **options):
        default_categories = [
            'Работа',
            'Личное',
            'Учёба',
            'Здоровье',
            'Финансы',
            'Дом',
            'Хобби',
            'Важное',
            'Срочное'
        ]

        created_count = 0
        for category_name in default_categories:
            category, created = Category.objects.get_or_create(name=category_name)
            if created:
                created_count += 1
                self.stdout.write(f'Created category: {category_name}')
            else:
                self.stdout.write(f'Category already exists: {category_name}')

        self.stdout.write(
            self.style.SUCCESS(f'Successfully processed {len(default_categories)} categories. Created {created_count} new ones.')
        )
