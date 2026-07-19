"""
Comando de gerenciamento Django para aguardar o PostgreSQL estar pronto.
"""

from django.core.management.base import BaseCommand
from django.db import connection
from django.db.utils import OperationalError
import time


class Command(BaseCommand):
    help = 'Aguarda o banco de dados estar disponível antes de iniciar o servidor'

    def add_arguments(self, parser):
        parser.add_argument(
            '--max-retries',
            type=int,
            default=30,
            help='Número máximo de tentativas (padrão: 30)',
        )
        parser.add_argument(
            '--retry-interval',
            type=int,
            default=2,
            help='Intervalo entre tentativas em segundos (padrão: 2)',
        )

    def handle(self, *args, **options):
        max_retries = options['max_retries']
        retry_interval = options['retry_interval']
        
        self.stdout.write('Aguardando PostgreSQL estar disponível...')
        
        for retry in range(1, max_retries + 1):
            try:
                connection.ensure_connection()
                self.stdout.write(
                    self.style.SUCCESS('✓ PostgreSQL está disponível!')
                )
                return
            except OperationalError:
                if retry < max_retries:
                    self.stdout.write(
                        f'PostgreSQL não está disponível ainda. '
                        f'Tentativa {retry}/{max_retries}...'
                    )
                    time.sleep(retry_interval)
                else:
                    self.stdout.write(
                        self.style.ERROR(
                            '✗ Falha ao conectar ao PostgreSQL após várias tentativas.'
                        )
                    )
                    raise

