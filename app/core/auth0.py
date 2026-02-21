import requests
from jose import jwt
from jose.exceptions import JWTError
from app.config import settings

def get_auth0_jwks():
  """Отримати JWKS (публічні ключі) від Auth0"""
  url = f"https://{settings.auth0_domain}/.well-known/jwks.json"
  response = requests.get(url)
  response.raise_for_status()
  return response.json()

def decode_auth0_token(token: str):
  """ Декодує та перевіряє JWT від Auth0. Повертає payload словник або викликає JWTError при невірному токені. """
  jwks = get_auth0_jwks()
  unverified_header = jwt.get_unverified_header(token)
  rsa_key = {}
  for key in jwks["keys"]:
    if key["kid"] == unverified_header.get("kid"):
      rsa_key = {
        "kty": key["kty"],
        "kid": key["kid"],
        "use": key["use"],
        "n": key["n"],
        "e": key["e"]
      }
      break
  if not rsa_key:
    raise JWTError("Unable to find appropriate key for token")
  payload = jwt.decode(
    token,
    rsa_key,
    algorithms=settings.auth0_algorithm,
    audience=settings.auth0_client_id,
    issuer=f"https://{settings.auth0_domain}/"
  )
  return payload
