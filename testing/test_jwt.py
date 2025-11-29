import jwt
import datetime

secret_key = 'your-256-bit-secret'
payload = {
    'user_id': 123,
    'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
}

token = jwt.encode(payload, secret_key, algorithm='HS256')
decoded = jwt.decode(token, secret_key, algorithms=['HS256'])

print(f'Encoded JWT: {token}')
print(f'Decoded JWT payload: {decoded}')