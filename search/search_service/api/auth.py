from flask_restful import Resource, reqparse
from ddp_auth.jwt import get_auth0_token
from http import HTTPStatus

class AuthTokenAPI(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser(bundle_errors=True)
        self.parser.add_argument('client_id', required=True, type=str, location='json')
        self.parser.add_argument('client_secret', required=True, type=str, location='json')
        super().__init__()

    def post(self):
        args = self.parser.parse_args(strict=True)
        client_id = args.get('client_id')
        client_secret = args.get('client_secret')
        try:
            token_response = get_auth0_token(client_id=client_id, client_secret=client_secret)
            return token_response, HTTPStatus.OK
        except Exception as e:
            return {'message': str(e)}, HTTPStatus.UNAUTHORIZED