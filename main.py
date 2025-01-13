import urllib3
import DocumentModel
import pageHandler

urllib3.disable_warnings()

if __name__ == '__main__':
    page = DocumentModel.DocumentModel(809825482)
    page.print_info()
    if page.typeDoc == "DD":
        pageHandler.add_macros_to_tables_dd(page)
        page.patch_page()
    elif page.typeDoc == "INTG":
        pageHandler.add_macros_to_tables_intg(page)
        page.patch_page()
    else:
        print("Не поддерживаемый тип документа")
