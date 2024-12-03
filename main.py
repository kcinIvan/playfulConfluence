import urllib3
import DocumentModel
import pageHandler
urllib3.disable_warnings()

if __name__ == '__main__':
    page = DocumentModel.DocumentModel(804702898, "DD-MPA-004")
    pageHandler.add_macros_to_tables_dd(page)
    page.patch_page()
