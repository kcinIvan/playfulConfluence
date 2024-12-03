from atlassian import Confluence
import keyring

# Как не продолбать пароли в Python скриптах: https://habr.com/ru/articles/435652/
username = 'ISemkin'
password = keyring.get_password("keyring_cred", username)

url = 'https://confluence.app.local/'


def get_connect():
    confluence = Confluence(
        url=url,
        username=username,
        password=password,
        verify_ssl=False)
    return confluence
