# http://127.0.0.1:8000/home/search/
# python manage.py runserver
# source venv/bin/activate

# docker system prune -a

# docker load -i my_django_app.tar
# docker run -p 8000:8000 my_django_app:latest

# docker build --no-cache -t my_django_app .
# docker buildx build --platform linux/amd64,linux/arm64 -t my_django_app:latest . # other opt
# docker save my_django_app:latest -o my_django_app.tar
# docker run -p 8000:8000 my_django_app

from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.db import connection
from .forms import SubseqForm
from .sequence import Sequence 
from django.core.cache import cache
import os
from django.conf import settings
from .sequence_storage import sequences_dict
import re
import sqlite3
from io import StringIO
from django.contrib import messages
from .forms import UploadFileForm, DeleteForm

# возможно ускорить, посмотрим
def check_pos(arr, subseq_lst):
    return_arr = []
    for sequence in arr:
        positions = []
        last_pos = -1
        valid = True
        for num in subseq_lst:
            # Если в последовательности вообще нет вхождений для данного числа — выходим.
            if num not in sequence.pos_dict or not sequence.pos_dict[num]:
                valid = False
                break
            # Ищем первое вхождение, которое идёт после last_pos
            found = False
            for pos in sequence.pos_dict[num]:
                if pos > last_pos:
                    positions.append(pos)
                    last_pos = pos
                    found = True
                    break
            if not found:  # если такого вхождения нет, то последовательность не подходит
                valid = False
                break
        if valid:
            return_arr.append(sequence)
    return return_arr


def main_search(request):
    cursor = connection.cursor()
    cursor.execute('SELECT DISTINCT family FROM Sekvenser_unique')  
    families_lst = [row[0] for row in cursor.fetchall()]
    families_lst.sort()

    if request.method == "POST":
        form = SubseqForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            # Преобразуем строку в список чисел
            subseq_list = list(map(int, cd["subseq"].split(",")))
            families = list(map(int, request.POST.getlist("families")))
            transfer1 = []
            
            if len(subseq_list) == 1:
                target_number = subseq_list[0]
                for family in families:
                    if family in sequences_dict and target_number in sequences_dict[family]:
                        transfer1.extend(sequences_dict[family][target_number])
                    else:
                        print(f"No data for family {family} with number {target_number}")
            elif len(subseq_list) > 1:
                result_set = set()
                first = True
                for target_number in subseq_list:
                    transfer_set = set()
                    for family in families:
                        if family in sequences_dict and target_number in sequences_dict[family]:
                            transfer_set.update(sequences_dict[family][target_number])
                    if first:
                        result_set = transfer_set
                        first = False
                    else:
                        result_set = result_set & transfer_set
                transfer1 = check_pos(list(result_set), subseq_list)
            
            # Формируем списки для передачи 
            transfer = []    # текстовые представления последовательностей
            params = []      # параметры секвенций нужен список списков
            positions_list = []  # для каждой последовательности массив позиций по числам из subseq_list

            for seq in transfer1:
                transfer.append(seq.sekvens)
                temporary_params = seq.get_params()
                if len(temporary_params) > 1 :
                    params.append(temporary_params[0])
                    for i in range(len(temporary_params)-1):
                        transfer.append(seq.sekvens)
                        params.append(temporary_params[i+1])
                else:        
                    params.append(seq.get_params()[0])
                pos_for_seq = []
                # Для каждого числа из запроса берём первое вхождение (если есть)
                for num in subseq_list:
                    if num in seq.pos_dict and len(seq.pos_dict[num]) > 0:
                        pos_for_seq.append(seq.pos_dict[num][0])
                    else:
                        pos_for_seq.append("-")  # или можно пропустить, или задать значение по умолчанию
                positions_list.append(pos_for_seq)

            total = len(transfer)
            
            data = {
                "transfer": transfer,
                "params": params,
                "positions": positions_list,
                "total": total,
                "families_lst": families_lst
            }
            
            if request.headers.get("Accept") == "application/json":
                return JsonResponse(data)
            
            return render(request, 'algebradb/algebra/home.html', {
                "transfer": transfer,
                "params": params,
                "positions": positions_list,
                "total": total,
                "form": form,
                "families_lst": families_lst
            })
    else:
        form = SubseqForm()
    return render(request, 'algebradb/algebra/home.html', {
        "form": form,
        "families_lst": families_lst
        })

            
def is_prime(n):
    if n <= 1:
        return False
    if n <= 3:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True

def sequence_summary(request):
    if request.method == "POST":
        # Получаем начальное и конечное число интервала
        start = int(request.POST.get("start"))
        end = int(request.POST.get("end"))
        
        # Получаем выбранные семьи (если ничего не выбрано, можно считать, что выбираются все)
        families = request.POST.getlist("families")
        if families:
            families = list(map(int, families))
        
        prime_only = request.POST.get("prime_only") == "on"
        
        summary = {}
        for number in range(start, end + 1):
            if prime_only and not is_prime(number):
                continue

            count = 0
            for family, inner_dict in sequences_dict.items():
                if families and family not in families:
                    continue
                if number in inner_dict:
                    count += len(inner_dict[number])
            summary[number] = count
        
        return JsonResponse(summary)
    return render(request, 'algebradb/algebra/summary_form.html')

def getinfo(line):
    pattern = r"(\d+);\{([\d,\s]+)\};\{([\d,\s]+)\}"
    match = re.search(pattern, line)
    
    if not match:
        return None  # Если строка не соответствует формату, вернуть None

    lst = []
    lst.append(int(match.group(1)))  # n

    # Проверяем, является ли второй параметр числом или списком
    a_param_str = match.group(2)
    a_param_list = list(map(int, a_param_str.split(", ")))
    
    if len(a_param_list) == 1:
        a_param = a_param_list[0]  # Если одно число, сохраняем как int
    else:
        a_param = a_param_list  # Если список, сохраняем как list

    lst.append(a_param)
    lst.append(list(map(int, match.group(3).split(", "))))  # sekvens
    
    return lst

def process_txt_file(content, fam):
    cursor = connection.cursor()

    cursor.execute('''
                    CREATE TABLE IF NOT EXISTS Sekvenser_temp (
                        sekvens TEXT NOT NULL,
                        n_param INTEGER,
                        a_param NUMERIC,
                        family INTEGER
                    )''')
    
    # Создаём файловый объект из строки
    file_obj = StringIO(content)
          
    cursor.execute("BEGIN TRANSACTION;")
    for sekvens in file_obj:
        b = getinfo(sekvens.strip())  # Убираем пробелы и \n

        if not b:  # Проверяем, есть ли данные
            print(f"Строка пропущена: {sekvens.strip()}")  # Логируем пропуск
            continue

        b2 = ", ".join(map(str, b[2]))  # Преобразуем список чисел в строку
        
        # Обрабатываем a_param
        if isinstance(b[1], list):
            a_param = ", ".join(map(str, b[1]))  # Преобразуем список в строку
        else:
            a_param = b[1]  # Число оставляем как есть
        
        cursor.execute(
            'INSERT INTO Sekvenser_temp (sekvens, n_param, a_param, family) VALUES (%s, %s, %s, %s)', 
                (b2, b[0], a_param, fam)
            )

    # Выбираем уникальные пары (sekvens, family) из исходной таблицы Sekvenser
    cursor.execute("SELECT DISTINCT sekvens, family FROM Sekvenser_temp")
    unique_pairs = cursor.fetchall()
    
    # Вставляем уникальные записи в Sekvenser_unique
    for sekvens, family in unique_pairs:
        cursor.execute("INSERT OR IGNORE INTO Sekvenser_unique (sekvens, family) VALUES (%s, %s)", (sekvens, family))
    connection.commit()

    # Создаём словарь сопоставления
    cursor.execute("SELECT sek_id, sekvens, family FROM Sekvenser_unique")
    mapping = {(row[1], row[2]): row[0] for row in cursor.fetchall()}

    # Перебираем все записи из исходной таблицы Sekvenser
    cursor.execute("SELECT sekvens, family, n_param, a_param FROM Sekvenser_temp")
    rows = cursor.fetchall()
    for sekvens, family, n_param, a_param in rows:
        # Получаем соответствующий sek_id по уникальной паре
        sek_id = mapping[(sekvens, family)]
        cursor.execute("INSERT OR IGNORE INTO Sekvenser_params (sek_id, n_param, a_param, family) VALUES (%s, %s, %s, %s)", 
                    (sek_id, n_param, a_param, family))

    connection.commit()
    cursor.execute("DROP TABLE IF EXISTS Sekvenser_temp")
    connection.commit()    

def admin_panel(request):
    """
    Общая страница панели управления, где выводятся ссылки на добавление/удаление.
    """
    return render(request, "algebradb/algebra/admin_panel.html")


def add_entries(request):
    """
    View для загрузки txt файла и добавления записей в базу.
    """
    if request.method == "POST":
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['file']
            # Читаем и декодируем файл
            content = uploaded_file.read().decode('utf-8')
            family = form.cleaned_data.get("family")
            process_txt_file(content, family)
            messages.success(request, "Файл успешно загружен и данные обработаны.")
            if request.headers.get("Accept") == "application/json":
                return JsonResponse({"status": "ok"})
            return redirect("admin_panel")
    else:
        form = UploadFileForm()
    return render(request, "algebradb/admin/upload.html", {"form": form})


def delete_family(family):
    cursor = connection.cursor()
    cursor.execute("BEGIN TRANSACTION")
    cursor.execute('DELETE FROM Sekvenser_unique WHERE family = %s', (family,))
    cursor.execute('DELETE FROM Sekvenser_params WHERE family = %s', (family,))
    connection.commit()

def delete_ai_n(n_param, a_param, family):
    cursor = connection.cursor()
    cursor.execute("BEGIN TRANSACTION")

    cursor.execute("""
        SELECT sek_id FROM Sekvenser_params
        WHERE n_param = ? AND a_param = ? AND family = ?
    """, (n_param, a_param, family))

    sekv = cursor.fetchall()
    for (sek_id,) in sekv:
        cursor.execute('DELETE FROM Sekvenser_unique WHERE sek_id = %s', (sek_id,))
        cursor.execute('DELETE FROM Sekvenser_params WHERE sek_id = %s', (sek_id,))
    connection.commit()
    
    #if family in sequence_dict and sequence_dict[family]: настроить удаление
        

def delete_sekv(sekvens, family):
    cursor = connection.cursor()
    cursor.execute("BEGIN TRANSACTION")
    cursor.execute('SELECT sek_id FROM Sekvenser_unique WHERE sekvens = %s AND family = %s', (sekvens,family))
    sekv = cursor.fetchall()
    for (sek_id,) in sekv:
        cursor.execute('DELETE FROM Sekvenser_unique WHERE sek_id = %s', (sek_id,))
        cursor.execute('DELETE FROM Sekvenser_params WHERE sek_id = %s', (sek_id,))
    connection.commit()
    

    
def format_string(s):
    s = s.replace(" ", "")
    parts = s.split(",")
    formatted = ", ".join(parts)
    return formatted


def delete_entries(request):
    if request.method == "POST":
        form = DeleteForm(request.POST)
        if form.is_valid():
            n_param = form.cleaned_data.get("n_param")
            a_param = form.cleaned_data.get("a_param")
            sekvens = form.cleaned_data.get("sekvens")
            family = form.cleaned_data.get("family")
            sekvens = format_string(sekvens)
            
            if n_param and a_param:
                delete_ai_n(n_param,a_param,family)
            elif sekvens:
                delete_sekv(sekvens, family)
            else:
                delete_family(family)
            
            success_msg = "Записи успешно удалены."
            messages.success(request, success_msg)
            if request.headers.get("Accept") == "application/json":
                return JsonResponse({"status": "ok", "message": success_msg})
            return redirect("algebradb:admin_panel")

        # невалидный ввод при AJAX?
        if request.headers.get("Accept") == "application/json":
            return JsonResponse({"status": "error", "errors": form.errors}, status=400)

    # если GET или не-AJAX POST — просто возвращаем на панель
    return redirect("algebradb:admin_panel")
