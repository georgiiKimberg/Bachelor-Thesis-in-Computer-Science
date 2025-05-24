from django.apps import AppConfig
from django.db import connection
import os
import sys

def table_exists(table_name):
    return table_name in connection.introspection.table_names()

class AlgebradbConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'algebradb'

    def ready(self):
        import re
        import tracemalloc
        from .sequence import Sequence  # Импорт класса для обработки
        from .sequence_storage import sequences_dict  # Глобальный словарь для хранения данных

        skip_commands = {'migrate', 'makemigrations', 'collectstatic', 'shell', 'test'}
        if len(sys.argv) >= 2 and sys.argv[1] in skip_commands:
            return

        # Не выполнять preload в первом процессе runserver (без RUN_MAIN)
        if 'runserver' in sys.argv and os.environ.get('RUN_MAIN') != 'true':
            return

        # Убедимся, что таблица есть (иначе при migrate база может быть пустой)
        if not table_exists('Sekvenser_unique'):
            print("Table Sekvenser_unique doesn't exist, skipping preload")
            return
        print("Preloading data")
        tracemalloc.start() 
        sequences_dict.clear()

        cursor = connection.cursor()
        cursor.execute('SELECT sekvens, family, sek_id FROM Sekvenser_unique')
        rows = cursor.fetchall()
        print(f"Number of sekvenser: {len(rows)}")

        # Каждая строка имеет порядок: sekvens, family, sek_id
        for row in rows:
            seq_instance = Sequence(
                sekvens=row[0],
                family=row[1],
                sek_id=row[2],
            )

            # Извлекаем уникальные числа из атрибута sorted_sekvens (уже преобразованного в список чисел)
            unique_numbers = set(map(int, re.findall(r"\d+", row[0])))

            # Если для данной семьи ещё нет внутреннего словаря — создаём его
            if seq_instance.family not in sequences_dict:
                sequences_dict[seq_instance.family] = {}

            # Для каждого уникального числа добавляем экземпляр Sequence в соответствующий список
            for number in unique_numbers:
                if number not in sequences_dict[seq_instance.family]:
                    sequences_dict[seq_instance.family][number] = []
                sequences_dict[seq_instance.family][number].append(seq_instance)

        current, peak = tracemalloc.get_traced_memory()
        print(f"Memory used during preload: {current / 1024**2:.2f} MB (peak: {peak / 1024**2:.2f} MB)")
        tracemalloc.stop()

        print("Loading completed")






