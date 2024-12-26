import urllib3
import DocumentModel
import pageHandler
urllib3.disable_warnings()

if __name__ == '__main__':
    page = DocumentModel.DocumentModel(979503163)
    # pageHandler.add_macros_to_tables_dd(page)
    # pageHandler.add_macros_to_tables_intg(page)
    page.print_info()
    # page.patch_page()
