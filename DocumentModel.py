import connector
from bs4 import BeautifulSoup
import pandas as pd
import io
import re


class DocumentModel:
    def __init__(self, page_id):
        confluence = connector.get_connect()

        # получение информации о странице по id
        page = confluence.get_page_by_id(page_id, expand="body.storage", status=None, version=None)
        page_content = page["body"]["storage"]["value"]

        # Используем BeautifulSoup для парсинга HTML
        soup = BeautifulSoup(page_content, "html.parser")

        # Заменяем содержимое <ac:structured-macro> и <ac:link> на уникальные маркеры
        macro_replacements = {}
        link_replacements = {}

        # Обработка <ac:structured-macro>
        for i, macro in enumerate(soup.find_all("ac:structured-macro")):

            # Получаем атрибуты макроса
            macro_name = macro.get("ac:name")

            # Пропускаем макросы с определённым macro-id или name
            if macro_name == "ui-tab" or macro_name == "ui-tabs":
                continue  # Пропускаем этот макрос и не заменяем его на маркер

            # Если макрос не исключён, заменяем его на маркер
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

        self.id = page_id  # id страницы
        self.keyDoc = None  # ключ документа
        self.title = page["title"]  # заголовок страницы
        self.typeDoc = None  # тип документа
        self.numberDoc = None  # порядковый номер для типа документа
        self.tables = tables  # таблицы на странице
        self.macro_replacements = macro_replacements
        self.__link_replacements = link_replacements
        self.__soup = soup
        self.get_keydoc()

    def get_keydoc(self):
        # Можно брать только таблицу под индексом 0 игнорируя остальные
        for table in self.tables:

            # Преобразуем таблицу в DataFrame
            try:
                df = pd.read_html(io.StringIO(str(table)))[0]

            except ValueError:
                # Пропускаем таблицы, которые не удалось преобразовать
                continue

            try:
                # Транспонируем таблицу, чтобы строки стали столбцами
                df = df.transpose()

                # Используем значения первой строки как заголовки столбцов
                df.columns = df.iloc[0]  # Первая строка становится заголовками
                df = df.drop(0)  # Удаляем первую строку, так как она теперь заголовок

                # Теперь df содержит транспонированную таблицу с новыми заголовками

                # Ищем таблицу паспорта документа из утверждения, что только она содержит столбцы "Код", "Назначение"
                codes_column_name = next((col for col in df.columns if "Код" in str(col)), None)
                if codes_column_name is not None:
                    # Если такие столбцы есть пробуем получить код документа и проверить его на соответствие шаблону
                    code_value = df[codes_column_name][1]

                    if pd.isna(code_value):
                        print(f"Код документа не указан")
                        break
                    else:
                        input_string = self.macro_replacements[code_value]

                        # Шаблон для извлечения значения из <ac:parameter ac:name="key">
                        match = re.search(r'<ac:parameter ac:name="key">([^<]+)</ac:parameter>', input_string)

                        if match:
                            value = match.group(1)  # Извлекаем значение вида "API-SAMPLE-001"

                            # Шаблон для проверки и разбора: три группы, разделенные дефисами
                            # последняя группа только цифры
                            regex = r'^([A-Za-z]+)-([A-Za-z]+)-(\d{3})$'

                            match_parts = re.match(regex, value)

                            if match_parts:
                                # Извлекаем три части: первую, вторую и третью
                                type_part = match_parts.group(1)  # Первая группа (буквы)
                                key_part = match_parts.group(3).zfill(
                                    3)  # Третья группа (цифры), добавляем ведущие нули

                                self.keyDoc = match_parts.group(0)
                                self.typeDoc = type_part
                                self.numberDoc = key_part
                                break
                            else:
                                print(f'Код документа "{value}" не соответствует шаблону.')
                                break
                        else:
                            print('Не удалось получить код документа.')
                            break
            except KeyError:
                print(f"Не удалось преобразовать таблицу для определения кода документа")

    def print_info(self):
        print("******************************")
        print("id страницы: "+str(self.id))
        print("Ключ документа: "+str(self.keyDoc))
        print("Заголовок страницы: "+str(self.title))
        print("Тип документа: "+str(self.typeDoc))
        print("Порядковый номер для типа документа: "+str(self.numberDoc))
        print("******************************")

    def patch_page(self):
        confluence = connector.get_connect()

        soup = self.__soup

        # Восстанавливаем <ac:structured-macro> в остальной части документа
        for placeholder, original_html in self.macro_replacements.items():
            soup = BeautifulSoup(str(soup).replace(placeholder, original_html), "html.parser")

        # Восстанавливаем <ac:link> в остальной части документа
        for placeholder, original_html in self.__link_replacements.items():
            soup = BeautifulSoup(str(soup).replace(placeholder, original_html), "html.parser")

        # Результирующий HTML-код
        updated_html_content = str(soup)

        # обновление страницы полностью
        confluence.update_page(self.id, self.title, updated_html_content, parent_id=None, type='page',
                               representation='storage',
                               minor_edit=False, full_width=False)
        self.__init__(self.id, self.keyDoc)
        print(f'Page {self.title} has been updated')
