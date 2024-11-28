import DocumentModel
from bs4 import BeautifulSoup
import pandas as pd
import io


# Функция для проверки наличия макроса
def contains_macro(cell_value):
    return "_MACRO_PLACEHOLDER_" in cell_value


def insert_col(title_col, position, df):
    if isinstance(title_col, str):
        column_name = '<ac:structured-macro ac:macro-id="53b5d6fb-9774-4048-bea8-98a3e2889eac" ' \
                      'ac:name="requirement-property" ac:schema-version="1">' \
                      '<ac:parameter ac:name="ignore">true</ac:parameter>' \
                      f'</ac:structured-macro>{title_col}'
        if position == "last":
            df.insert(len(df.columns), column_name, "")  # Вставляем столбец на последнюю позицию
        elif position == "first":
            df.insert(0, column_name, "")  # Вставляем столбец на первую позицию
        else:
            raise Exception(f"Неопределенная позиция для вставки столбца: {position}")
        return column_name


def add_macros_to_tables_dd(obj: DocumentModel.DocumentModel):
    # Инициализация счётчика макросов
    macro_counter = 1
    # Обработка всех таблиц, содержащих заголовок "Коды"
    for table in obj.tables:
        # Преобразуем таблицу в DataFrame
        try:
            df = pd.read_html(io.StringIO(str(table)))[0]

        except ValueError:
            # Пропускаем таблицы, которые не удалось преобразовать
            continue

        # Проверяем, содержит ли таблица столбец "Коды"
        codes_column_name = next((col for col in df.columns if "Коды" in str(col)), None)
        if codes_column_name is None:
            # Если столбца "Код" нет, проверяем наличие столбца "Атрибут"
            attributes_column_name = next((col for col in df.columns if "Атрибут" in str(col)), None)
            if attributes_column_name is not None:
                codes_column_name = insert_col("Коды", "first", df)
            else:
                # Пропускаем таблицы без столбца "Атрибуты"
                continue

        # Проверяем наличие столбца "Чтение" и "Запись"
        reading_column_name = next((col for col in df.columns if "Чтение" in str(col)), None)
        if reading_column_name is None:
            reading_column_name = insert_col("Чтение", "last", df)

        writing_column_name = next((col for col in df.columns if "Запись" in str(col)), None)
        if writing_column_name is None:
            writing_column_name = insert_col("Запись", "last", df)

        # Приведение типа столбцов, куда добавляются макросы, к строковому
        df[codes_column_name] = df[codes_column_name].astype(str)
        df[reading_column_name] = df[reading_column_name].astype(str)
        df[writing_column_name] = df[writing_column_name].astype(str)

        # Обрабатываем строки таблицы
        for index, row in df.iterrows():
            if not contains_macro(row[codes_column_name]):
                # Формируем макрос для столбца "Коды"
                codes_macro = f"""<ac:structured-macro ac:name="requirement" ac:schema-version="1" ac:macro-id="78c83295-93e7-46d1-91c3-996d2b19abd4">
                  <ac:parameter ac:name="type">DEFINITION</ac:parameter>
                  <ac:parameter ac:name="key">{obj.keyDoc}-{macro_counter}-w</ac:parameter>
                </ac:structured-macro><p><ac:structured-macro ac:name="requirement" ac:schema-version="1" ac:macro-id="fa95f2ea-fb6d-42b4-8e45-9136dc50604e">
                  <ac:parameter ac:name="type">DEFINITION</ac:parameter>
                  <ac:parameter ac:name="key">{obj.keyDoc}-{macro_counter}-r</ac:parameter>
                </ac:structured-macro></p>"""
                # Добавляем макрос в столбец "Коды"
                df.at[index, codes_column_name] = f"{codes_macro}{str(row[codes_column_name])}"

            if not contains_macro(row[reading_column_name]):
                # Формируем макрос для столбца "Чтение"
                reading_macro = f"""<ac:structured-macro ac:name="requirement-report" ac:schema-version="1" ac:macro-id="2d61b4d7-2599-40ed-9063-4b1af911776e">
                        <ac:parameter ac:name="columns">links?duplicates=false</ac:parameter>
                        <ac:parameter ac:name="query">key='{obj.keyDoc}-{macro_counter}-r'</ac:parameter>
                    </ac:structured-macro>"""
                # Добавляем макрос в столбец "Чтение"
                df.at[index, reading_column_name] = f"{reading_macro}{str(row[reading_column_name])}"

            if not contains_macro(row[writing_column_name]):
                # Формируем макрос для столбца "Запись"
                writing_macro = f"""<ac:structured-macro ac:name="requirement-report" ac:schema-version="1" ac:macro-id="2d61b4d7-2599-40ed-9063-4b1af911776e">
                            <ac:parameter ac:name="columns">links?duplicates=false</ac:parameter>
                            <ac:parameter ac:name="query">key='{obj.keyDoc}-{macro_counter}-w'</ac:parameter>
                        </ac:structured-macro>"""
                # Добавляем макрос в столбец "Запись"
                df.at[index, writing_column_name] = f"{writing_macro}{str(row[writing_column_name])}"

            macro_counter += 1

        # Приведение всех столбцов к строковому типу перед заменой NaN
        df = df.astype(str)

        # Убираем NaN, заменяя их на пустые строки
        df.fillna('', inplace=True)

        # Преобразуем DataFrame обратно в HTML
        updated_table_html = df.to_html(index=False, escape=False)

        # Исключаем все "nan" из результирующего HTML
        updated_table_html = updated_table_html.replace('nan', '')

        # Заменяем HTML исходной таблицы на обновлённый
        table.replace_with(BeautifulSoup(updated_table_html, "html.parser"))


def add_macros_to_tables_intg(obj: DocumentModel.DocumentModel):
    # Инициализация счётчика макросов
    macro_counter = 1
    # Обработка всех таблиц, содержащих заголовок "Коды"
    for table in obj.tables:
        # Преобразуем таблицу в DataFrame
        try:
            df = pd.read_html(io.StringIO(str(table)))[0]

        except ValueError:
            # Пропускаем таблицы, которые не удалось преобразовать
            continue

        # Проверяем, содержит ли таблица столбец "Код"
        codes_column_name = next((col for col in df.columns if "Код" in str(col)), None)
        if codes_column_name is None:
            # Если столбца "Код" нет, проверяем наличие столбца "Атрибуты"
            attributes_column_name = next((col for col in df.columns if "Атрибут" in str(col)), None)
            if attributes_column_name is not None:
                codes_column_name = insert_col("Коды", "first", df)
            else:
                # Пропускаем таблицы без столбцов "Код" и "Атрибут"
                continue

        # Проверяем наличие столбца "Упоминания"
        mentions_column_name = next((col for col in df.columns if "Упоминания" in str(col)), None)
        if mentions_column_name is None:
            mentions_column_name = insert_col("Упоминания", "last", df)

        # Приведение типа столбцов, куда добавляются макросы, к строковому
        df[codes_column_name] = df[codes_column_name].astype(str)
        df[mentions_column_name] = df[mentions_column_name].astype(str)

        # Обрабатываем строки таблицы
        for index, row in df.iterrows():
            if not contains_macro(row[codes_column_name]):
                # Формируем макрос для столбца "Код"
                codes_macro = f"""<ac:structured-macro ac:name="requirement" ac:schema-version="1" ac:macro-id="78c83295-93e7-46d1-91c3-996d2b19abd4">
                  <ac:parameter ac:name="type">DEFINITION</ac:parameter>
                  <ac:parameter ac:name="key">{obj.keyDoc}-{macro_counter}</ac:parameter>"""
                # Добавляем макрос в столбец "Коды"
                df.at[index, codes_column_name] = f"{codes_macro}{str(row[codes_column_name])}"

            if not contains_macro(row[mentions_column_name]):
                # Формируем макрос для столбца "Упоминания"
                reading_macro = f"""<ac:structured-macro ac:name="requirement-report" ac:schema-version="1" ac:macro-id="2d61b4d7-2599-40ed-9063-4b1af911776e">
                        <ac:parameter ac:name="columns">links?duplicates=false</ac:parameter>
                        <ac:parameter ac:name="query">key='{obj.keyDoc}-{macro_counter}'</ac:parameter>
                    </ac:structured-macro>"""
                # Добавляем макрос в столбец "Упоминания"
                df.at[index, mentions_column_name] = f"{reading_macro}{str(row[mentions_column_name])}"

            macro_counter += 1

        # Приведение всех столбцов к строковому типу перед заменой NaN
        df = df.astype(str)

        # Убираем NaN, заменяя их на пустые строки
        df.fillna('', inplace=True)

        # Преобразуем DataFrame обратно в HTML
        updated_table_html = df.to_html(index=False, escape=False)

        # Исключаем все "nan" из результирующего HTML
        updated_table_html = updated_table_html.replace('nan', '')

        # Заменяем HTML исходной таблицы на обновлённый
        table.replace_with(BeautifulSoup(updated_table_html, "html.parser"))
