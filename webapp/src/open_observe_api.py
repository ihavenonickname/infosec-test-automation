import base64
import json

import requests


class OpenObserveApi():
    def __init__(self, base_url, root_email, root_password) -> None:
        self._base_url = base_url

        encoded = base64.b64encode(
            f'{root_email}:{root_password}'.encode('utf8')).decode('utf8')

        self._base_headers = {
            'authorization': f'Basic {encoded}',
            'Content-Type': 'application/json',
        }

    def _treat_response(self, res):
        print(res.text)

        if res.status_code >= 200 and res.status_code <= 299:
            return True, json.loads(res.text)

        try:
            return False, json.loads(res.text)['message']
        except Exception:
            return False, None

    def create_user(self, email, firstname, lastname, password):
        headers = {
            **self._base_headers,
            'Content-Type': 'application/json'
        }

        payload = json.dumps({
            'email': email,
            'first_name': firstname,
            'last_name': lastname,
            'password': password,
            'role': 'member',
        })

        url = f'{self._base_url}/api/recon/users'

        res = requests.post(url, data=payload, headers=headers)

        return self._treat_response(res)

    def delete_user(self, email):
        url = f'{self._base_url}/api/recon/users/{email}'

        res = requests.delete(url, headers=self._base_headers)

        return self._treat_response(res)

    def list_users(self):
        url = f'{self._base_url}/api/recon/users'

        res = requests.get(url, headers=self._base_headers)

        return self._treat_response(res)
