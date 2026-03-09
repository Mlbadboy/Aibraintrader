from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.database.models import User
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
import logging
import os
import uuid
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Security Config
# In production, JWT_SECRET_KEY must be set in the environment.
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    logger.warning("JWT_SECRET_KEY not found in environment. Using development fallback.")
    SECRET_KEY = "DEV_ONLY_INSECURE_KEY_REPLACE_IN_PROD"

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

app = FastAPI(title="Auth-Service")

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "auth-service"}

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@app.post("/auth/register")
def register(email: str, password: str, role: str = "retail", db: Session = Depends(get_db)):
    # Check if user exists
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = pwd_context.hash(password)
    new_user = User(
        id=uuid.uuid4(),
        email=email,
        hashed_password=hashed_password,
        role=role
    )
    db.add(new_user)
    db.commit()
    return {"status": "success", "message": "User registered successfully"}

@app.post("/auth/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not pwd_context.verify(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": str(user.id), "role": user.role})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/auth/google")
async def google_auth(token: str, db: Session = Depends(get_db)):
    """
    Verifies Google ID Token and returns JWT access token.
    Fetches name and profile picture from Google.
    """
    try:
        # Verify Google Token
        idinfo = id_token.verify_oauth2_token(token, google_requests.Request(), GOOGLE_CLIENT_ID)

        # ID token is valid. Get the user's Google ID information from the decoded token.
        email = idinfo['email']
        name = idinfo.get('name')
        picture = idinfo.get('picture')

        # Check if user exists
        user = db.query(User).filter(User.email == email).first()

        if not user:
            # Create new user
            user = User(
                id=uuid.uuid4(),
                email=email,
                full_name=name,
                profile_pic=picture,
                role="retail",
                hashed_password=None # OAuth users don't have passwords
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            # Update profile info if it changed
            user.full_name = name
            user.profile_pic = picture
            db.commit()
            db.refresh(user)

        # Generate JWT
        access_token = create_access_token(data={"sub": str(user.id), "role": user.role})
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "email": user.email,
                "name": user.full_name,
                "picture": user.profile_pic
            }
        }
    except ValueError:
        # Invalid token
        raise HTTPException(status_code=401, detail="Invalid Google token")
    except Exception as e:
        logger.error(f"Google Auth Error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/auth/verify")
def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        role = payload.get("role")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"user_id": user_id, "role": role}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
