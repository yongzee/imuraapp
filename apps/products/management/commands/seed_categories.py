from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify
from apps.products.models import Category, Subcategory

DATA = {
    "Clothing": [
        "Dresses", "Gowns", "Tops & Blouses", "Skirts", "Trousers", 
        "Shirts", "T-shirts", "Polos", "Jumpsuits", "Two-Piece", 
        "Suits", "Jackets", "Hoodies", "Native Wear", "Agbada", 
        "Kaftan", "Senator", "Children's Wear"
    ],
    "Shoes": [
        "Sneakers", "Heels", "Sandals", "Slippers", "Loafers", "Boots", "Flats"
    ],
    "Bags": [
        "Handbags", "Backpacks", "Crossbody Bags", "Clutches", "Travel Bags"
    ],
    "Fabrics": [
        "Ankara", "Lace", "Aso-Oke", "Adire", "Plain Fabrics", "Other Fabrics"
    ],
    "Accessories": [
        "Watches", "Jewelry", "Belts", "Caps & Hats", "Sunglasses", "Scarves"
    ],
    "Beauty & Hair": [
        "Wigs", "Hair Extensions", "Makeup", "Perfumes", "Skincare", "Hair Products"
    ],
    "Traditional / Cultural": [
        "Traditional Outfits", "Headwear", "Cultural Accessories", "Aso-Ebi"
    ],
    "Other": [
        "General / Miscellaneous"
    ]
}


class Command(BaseCommand):
    help = "Seeds categories and subcategories into the database"

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("Starting category seed..."))
        
        category_count = 0
        subcategory_count = 0

        for cat_name, sub_names in DATA.items():
            # Get or create parent category (slug will auto-generate in custom save method)
            category, cat_created = Category.objects.get_or_create(
                name=cat_name,
                defaults={"slug": slugify(cat_name)}
            )
            
            if cat_created:
                category_count += 1

            for sub_name in sub_names:
                _, sub_created = Subcategory.objects.get_or_create(
                    category=category,
                    name=sub_name
                )
                if sub_created:
                    subcategory_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully seeded database! Added {category_count} new categories "
                f"and {subcategory_count} new subcategories."
            )
        )