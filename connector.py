from atlassian import Confluence
import keyring

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
