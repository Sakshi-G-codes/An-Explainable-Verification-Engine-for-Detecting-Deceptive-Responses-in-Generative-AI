from django.core.management.base import BaseCommand
from verification.indexing import build_index

class Command(BaseCommand):
    help = 'Builds the FAISS vector index for medical evidence'

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting indexing process...")
        build_index()
        self.stdout.write(self.style.SUCCESS("Indexing process completed successfully."))
