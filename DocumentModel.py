import connector
from bs4 import BeautifulSoup


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
        self.keyDoc = "DD-MPA-919"  # ключ документа
        self.title = page["title"] # заголовок страницы
        self.typeDoc = "non"  # тип документа
        self.numberDoc = 0  # порядковый номер для типа документа
        self.tables = tables  # таблицы на странице
        self.__macro_replacements = macro_replacements
        self.__link_replacements = link_replacements
        self.__soup = soup

    def patch_page(self):
        confluence = connector.get_connect()

        soup = self.__soup

        # Восстанавливаем <ac:structured-macro> в остальной части документа
        for placeholder, original_html in self.__macro_replacements.items():
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
        self.__init__(self.id)
        print('Page has been updated')
