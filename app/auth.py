import requests


class Auth:
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.__set_token()
    # TODO: Change 'set_token' to 'get_token'
    def __set_token(self):
        oauth_url = 'https://id.twitch.tv/oauth2/token'
        auth_params = {
            'client_id':      self.client_id,
            'client_secret':  self.client_secret,
            'grant_type':     'client_credentials'
            }
        with requests.post(oauth_url, data=auth_params) as req:
            self.auth_tok = req.json()
            self.bear_tok = {
                'Authorization':  'Bearer ' + self.auth_tok['access_token'],
                'Client_ID':      self.client_id
                }