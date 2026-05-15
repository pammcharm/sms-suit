import json
from pathlib import Path

from django.core.management.base import BaseCommand
from django.core.serializers.json import DjangoJSONEncoder
from django.forms.models import model_to_dict
from django.utils import timezone

from core.models import (
    ActivityLog,
    BackupLog,
    Branch,
    BusinessProfile,
    Category,
    Customer,
    Employee,
    Expense,
    Payment,
    Product,
    Purchase,
    PurchaseItem,
    Sale,
    SaleItem,
    StockMovement,
    StockTransfer,
    Supplier,
)


class Command(BaseCommand):
    help = 'Export important business data to a JSON backup file.'

    def add_arguments(self, parser):
        parser.add_argument('--output-dir', default='backups')

    def handle(self, *args, **options):
        output_dir = Path(options['output_dir'])
        output_dir.mkdir(parents=True, exist_ok=True)
        stamp = timezone.now().strftime('%Y%m%d-%H%M%S')
        filename = output_dir / f'sms-suite-backup-{stamp}.json'
        models = [
            BusinessProfile, Branch, Category, Supplier, Product, Customer, Employee,
            Sale, SaleItem, Payment, Expense, Purchase, PurchaseItem, StockMovement,
            StockTransfer, ActivityLog,
        ]
        payload = {'created_at': timezone.now().isoformat(), 'tables': {}}
        for model in models:
            payload['tables'][model.__name__] = [model_to_dict(obj) for obj in model.objects.all()]
        filename.write_text(json.dumps(payload, cls=DjangoJSONEncoder, indent=2), encoding='utf-8')
        BackupLog.objects.create(filename=str(filename), notes='Created by backup_business_data command')
        self.stdout.write(self.style.SUCCESS(f'Backup created: {filename}'))
