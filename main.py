import urllib3
import DocumentModel
import pageHandler
urllib3.disable_warnings()

if __name__ == '__main__':
    pageDD = DocumentModel.DocumentModel(957066302)
    pageHandler.add_macros_to_tables_dd(pageDD)
    pageDD.patch_page()
