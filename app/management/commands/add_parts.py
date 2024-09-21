from django.core.management.base import BaseCommand
from app.models import Part

class Command(BaseCommand):
    help = "Добавляет все детали в базу данных"

    def handle(self, *args, **kwargs):
        parts_data = [
            {
                'part_name': 'ENGINE SHORT',
                'specification': 'V8 EFI PETROL',
                'oem_number': 'TF-EXH-2024-001',
                'status': True,
                'image': 'http://localhost:9000/web/parts/1.jpg',
                'short_description': 'Engine assembly - Short для V8 EFI PETROL.',
                'set_composition': '1. Engine assembly - Short',
                'dimensions': '90 см х 60 см х 70 см',
                'weight': 200,
            },
            {
                'part_name': 'TRANSMISSION BRAKE',
                'specification': 'V8 EFI PETROL',
                'oem_number': 'QX-EXH-2024-005',
                'status': True,
                'image': 'http://localhost:9000/web/parts/2.jpg',
                'short_description': 'Transmission brake assembly для V8 EFI PETROL.',
                'set_composition': '''1. Drum-transmission brake
2. Screw-disc fixing
3. Backplate-transmission brake assembly
4. Bolt
5. Kit-transmission brake shoe
6. Kit-transmission brake shoe retention
7. Kit-transmission brake adjuster
8. Kit-transmission brake shoe retention
9. Strut-transmission brake
10. Lever-transmission brake''',
                'dimensions': '80 см х 40 см х 30 см',
                'weight': 30,
            },
            {
                'part_name': 'TAILPIPE',
                'specification': 'V8 EFI PETROL',
                'oem_number': 'ST-EXH-2024-004',
                'status': True,
                'image': 'http://localhost:9000/web/parts/3.jpg',
                'short_description': 'Tailpipe assembly-exhaust system для V8 EFI PETROL.',
                'set_composition': '''1. Tailpipe assembly-exhaust system
2. Heatshield-exhaust system fuel tank — 10 штук
3. Finisher-trim exhaust tailpipe — 2 штуки
4. Nut - Hex — 3 штуки
5. Heatshield-rear floor exhaust system — 4 штуки
6. Washer — 5 штук
7. Screw — 6 штук
8. Nut-flange — 7 штук
9. Mounting-rubber exhaust system — 8 штук
10. Heatshield-spare wheel exhaust system — 9 штук''',
                'dimensions': '120 см х 40 см х 50 см',
                'weight': 15,
            },
            {
                'part_name': 'FUEL TANK & PARTS',
                'specification': '2.5L 6 CYL DIESEL',
                'oem_number': 'TF-EXH-2024-001',
                'status': True,
                'image': 'http://localhost:9000/web/parts/4.jpg',
                'short_description': 'Tank assembly fuel and related parts для 2.5L 6 CYL DIESEL.',
                'set_composition': '''1. Tank assembly fuel
2. Pump-fuel-unit assembly fuel tank
3. Seal-fuel pump unit tank
4. Ring-locking fuel tank
5. Hose assembly-breather fuel
6. Clip-Hose
7. Bracket assembly-fuel tank fuel tank
8. Nut - Hex
9. Washer-Plain
10. Screw-flanged head
11. Heatshield-fuel tank-exhaust system
12. Sender assembly-fuel tank
13. Screw-heatshield to fuel tank special
14. Insert-hose/pipe support
15. Connector fuel lines
16. Tee piece fuel lines''',
                'dimensions': '150 см х 60 см х 50 см',
                'weight': 40,
            },
            {
                'part_name': 'SILL FINISHERS',
                'specification': 'ANY',
                'oem_number': 'TS-EXH-2024-003',
                'status': True,
                'image': 'http://localhost:9000/web/parts/5.jpg',
                'short_description': 'Sill finishers для кузова любой конфигурации.',
                'set_composition': '''1. Finisher-body side sill
2. Plate-floor cover front sill tread
3. Plate-floor cover rear sill tread
4. Cupsac
5. Clip
6. Rivet-plastic-drive
7. Screw
8. Nutsert-blind''',
                'dimensions': '200 см х 30 см х 10 см',
                'weight': 10,
            },
            {
                'part_name': 'FRAME ASSEMBLY',
                'specification': 'V8 EFI PETROL',
                'oem_number': 'DX-EXH-2024-006',
                'status': True,
                'image': 'http://localhost:9000/web/parts/6.jpg',
                'short_description': 'Frame assembly для V8 EFI PETROL.',
                'set_composition': '''1. Frame assembly-chassis
2. Crossmember-gearbox support
3. Crossmember-front
4. Screw-flanged head
5. Nut-flange''',
                'dimensions': '300 см х 100 см х 50 см',
                'weight': 120,
            }
        ]

        parts = [Part(**part_data) for part_data in parts_data]
        Part.objects.bulk_create(parts)
        self.stdout.write(self.style.SUCCESS("Все детали успешно добавлены!"))