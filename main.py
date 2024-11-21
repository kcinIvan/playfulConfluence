from atlassian import Confluence
import keyring
import urllib3
import pandas as pd
from bs4 import BeautifulSoup
import io

urllib3.disable_warnings()

username = 'ISemkin'
password = keyring.get_password("keyring_cred", username)

url = 'https://confluence.app.local/'
page_id = 957066302

keydoc = 'DD-MPA-019'

if __name__ == '__main__':
    confluence = Confluence(
        url=url,
        username=username,
        password=password,
        verify_ssl=False)

    # получение информации о странице по id
    page = confluence.get_page_by_id(page_id, expand="body.storage", status=None, version=None)
    pageContent = page["body"]["storage"]["value"]

    # Используем BeautifulSoup для парсинга HTML
    soup = BeautifulSoup(pageContent, "html.parser")

    # Заменяем содержимое <ac:structured-macro> и <ac:link> на уникальные маркеры
    macro_replacements = {}
    link_replacements = {}

    # Обработка <ac:structured-macro>
    for i, macro in enumerate(soup.find_all("ac:structured-macro")):
        placeholder = f"__MACRO_PLACEHOLDER_{i}__"
        macro_replacements[placeholder] = str(macro)
        macro.replace_with(placeholder)

    # Обработка <ac:link>
    for i, link in enumerate(soup.find_all("ac:link")):
        placeholder = f"__LINK_PLACEHOLDER_{i}__"
        link_replacements[placeholder] = str(link)
        link.replace_with(placeholder)

    # Находим таблицы на странице (по умолчанию ищет все <table> элементы)
    tables = soup.find_all("table")

    # Проверяем, нашли ли таблицы
    if not tables:
        raise Exception("No tables found on the webpage.")

    # Инициализация счётчика макросов
    macro_counter = 1

    # Обработка всех таблиц, содержащих заголовок "Коды"
    for table in tables:
        # Преобразуем таблицу в DataFrame
        try:
            df = pd.read_html(io.StringIO(str(table)))[0]

        except ValueError:
            # Пропускаем таблицы, которые не удалось преобразовать
            continue

        # Проверяем, содержит ли таблица столбец "Коды"
        codes_column_name = next((col for col in df.columns if "Коды" in str(col)), None)
        if codes_column_name is None:
            # Пропускаем таблицы без столбца "Коды"
            continue

        # Проверяем наличие столбца "Чтение" и "Запись"
        reading_column_name = next((col for col in df.columns if "Чтение" in str(col)), None)
        if reading_column_name is None:
            raise Exception(f"Table with 'Коды' column does not have a corresponding 'Чтение' column.")

        writing_column_name = next((col for col in df.columns if "Запись" in str(col)), None)
        if writing_column_name is None:
            raise Exception(f"Table with 'Коды' column does not have a corresponding 'Запись' column.")

        # Приведение типа столбцов, куда добавляются макросы, к строковому
        df[codes_column_name] = df[codes_column_name].astype(str)
        df[reading_column_name] = df[reading_column_name].astype(str)
        df[writing_column_name] = df[writing_column_name].astype(str)

        # Функция для проверки наличия макроса
        def contains_macro(cell_value):
            return "_MACRO_PLACEHOLDER_" in cell_value

        # Обрабатываем строки таблицы
        for index, row in df.iterrows():
            if not contains_macro(row[codes_column_name]):
                # Формируем макрос для столбца "Коды"
                codes_macro = f"""<ac:structured-macro ac:name="requirement" ac:schema-version="1" ac:macro-id="78c83295-93e7-46d1-91c3-996d2b19abd4">
          <ac:parameter ac:name="type">DEFINITION</ac:parameter>
          <ac:parameter ac:name="key">{keydoc}-{macro_counter}-w</ac:parameter>
        </ac:structured-macro><p><ac:structured-macro ac:name="requirement" ac:schema-version="1" ac:macro-id="fa95f2ea-fb6d-42b4-8e45-9136dc50604e">
          <ac:parameter ac:name="type">DEFINITION</ac:parameter>
          <ac:parameter ac:name="key">{keydoc}-{macro_counter}-r</ac:parameter>
        </ac:structured-macro></p>"""
                # Добавляем макрос в столбец "Коды"
                df.at[index, codes_column_name] = f"{codes_macro}{str(row[codes_column_name])}"

            if not contains_macro(row[reading_column_name]):
                # Формируем макрос для столбца "Чтение"
                reading_macro = f"""<ac:structured-macro ac:name="requirement-report" ac:schema-version="1" ac:macro-id="2d61b4d7-2599-40ed-9063-4b1af911776e">
                <ac:parameter ac:name="columns">links?duplicates=false</ac:parameter>
                <ac:parameter ac:name="query">key='{keydoc}-{macro_counter}-r'</ac:parameter>
            </ac:structured-macro>"""
                # Добавляем макрос в столбец "Чтение"
                df.at[index, reading_column_name] = f"{reading_macro}{str(row[reading_column_name])}"

            if not contains_macro(row[writing_column_name]):
                # Формируем макрос для столбца "Запись"
                writing_macro = f"""<ac:structured-macro ac:name="requirement-report" ac:schema-version="1" ac:macro-id="2d61b4d7-2599-40ed-9063-4b1af911776e">
                    <ac:parameter ac:name="columns">links?duplicates=false</ac:parameter>
                    <ac:parameter ac:name="query">key='{keydoc}-{macro_counter}-w'</ac:parameter>
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

    # Восстанавливаем <ac:structured-macro> в остальной части документа
    for placeholder, original_html in macro_replacements.items():
        soup = BeautifulSoup(str(soup).replace(placeholder, original_html), "html.parser")

    # Восстанавливаем <ac:link> в остальной части документа
    for placeholder, original_html in link_replacements.items():
        soup = BeautifulSoup(str(soup).replace(placeholder, original_html), "html.parser")

    # Результирующий HTML-код
    updated_html_content = str(soup)

    # обновление страницы полностью
    confluence.update_page(page_id, page['title'], updated_html_content, parent_id=None, type='page',
                           representation='storage',
                           minor_edit=False, full_width=False)
    print('done')
    