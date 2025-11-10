import requests
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError, jwk
from jose.utils import base64url_decode
from sqlalchemy.orm import Session

from app.models import models
from app.models.models import User

from db.dbconfig import get_db
from config import settings

import logging

# --- Your Cognito Configuration ---
COGNITO_REGION = settings.COGNITO_REGION
USER_POOL_ID = settings.COGNITO_USER_POOL_ID
APP_CLIENT_ID = settings.COGNITO_APP_CLIENT_ID
# ----------------------------------

# Construct the JWKS URL
jwks_url = f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{USER_POOL_ID}/.well-known/jwks.json"

# Download and cache the JWKS keys
# In a real app, you might cache this for longer
try:
    response = requests.get(jwks_url)
    response.raise_for_status()
    jwks = response.json()["keys"]
except requests.RequestException as e:
    # This is a fatal error; the application cannot start without the keys
    raise RuntimeError(f"Could not fetch JWKS: {e}") from e

auth_scheme = HTTPBearer()

async def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(auth_scheme),
    db: Session = Depends(get_db)
) -> dict:

    token = creds.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Get the unverified header from the token
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        if not kid:
            raise JWTError("Missing 'kid' in token header")

        # Find the matching public key
        rsa_key = None
        for key in jwks:
            if key["kid"] == kid:
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"],
                }
                break
        
        if not rsa_key:
            raise JWTError("Unable to find matching 'kid' in JWKS")
        
        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=["RS256"],
            audience=APP_CLIENT_ID,
            issuer=f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{USER_POOL_ID}",
            options={"verify_at_hash": False}
        )
        
        user_sub = payload.get("sub")
        
        # Check if user exists in Supabase DB
        user = db.query(models.User).filter(models.User.id == user_sub).first()
        
        if not user:
            # Create the user in the DB
            new_user = models.User(
                id=user_sub,
                email=payload.get("email"),
            )
            
            try:
                db.add(new_user)
                db.commit()
            except Exception as e:
                db.rollback()
                raise HTTPException(
                    status_code=500,
                    detail=f"Error provisioning user in database: {e}"
                )
        
        return payload
    
    except JWTError as e:
        logging.error(f"JWT Validation Error: {e}")
        raise credentials_exception from e
