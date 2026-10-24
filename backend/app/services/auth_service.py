import hashlib
import re
import secrets

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import Competition, Membership, Organization, UserAccount
from app.schemas import UserLoginRequest, UserRegisterRequest
from app.services.workflows import create_competition


def hash_password(password: str, salt: str | None = None) -> str:
    if not salt:
        salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000)
    return f"{salt}${key.hex()}"

def verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt, hash_hex = stored_hash.split("$", 1)
        computed = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000)
        return secrets.compare_digest(computed.hex(), hash_hex)
    except Exception:
        return False

def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return re.sub(r"^-+|-+$", "", text) or "workspace"

def register_user(db: Session, payload: UserRegisterRequest):
    email = payload.email.strip().lower()
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        raise HTTPException(400, "Please provide a valid email address")

    existing = db.query(UserAccount).filter(UserAccount.email == email).first()
    if existing:
        raise HTTPException(409, "An account with this email address already exists")

    # Create Organization
    base_slug = slugify(payload.organization_name)
    org_slug = f"{base_slug}-{secrets.token_hex(3)}"
    org = Organization(name=payload.organization_name.strip(), slug=org_slug)
    db.add(org)
    db.flush()

    # Create User
    pwd_hash = hash_password(payload.password)
    user = UserAccount(
        email=email,
        full_name=payload.full_name.strip(),
        password_hash=pwd_hash,
        organization_id=org.id,
        role=payload.role,
        status="active",
    )
    db.add(user)
    db.flush()

    # Create Membership
    membership = Membership(
        organization_id=org.id,
        user_id=user.id,
        role=payload.role,
        status="active",
    )
    db.add(membership)
    db.flush()

    # Create initial competition / workspace for this organization
    class CompPayload:
        name = f"{payload.organization_name} Prize Fund"
        description = f"Primary prize distribution workspace for {payload.organization_name}"
        network = "stellar-testnet"
        default_currency = "XLM"
        created_by = payload.full_name.strip()

    default_comp = create_competition(db, CompPayload(), organization_id=org.id)

    db.commit()
    db.refresh(user)
    db.refresh(org)

    token = secrets.token_urlsafe(32)
    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "organization_id": org.id,
            "organization_name": org.name,
            "role": user.role,
        },
        "default_competition_id": default_comp.id,
        "token": token,
    }

def authenticate_user(db: Session, payload: UserLoginRequest):
    email = payload.email.strip().lower()
    user = db.query(UserAccount).filter(UserAccount.email == email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(401, "Invalid email or password")

    org = None
    if user.organization_id:
        org = db.get(Organization, user.organization_id)

    comps = []
    if org:
        comps = db.query(Competition).filter(Competition.organization_id == org.id).order_by(Competition.created_at.desc()).all()

    token = secrets.token_urlsafe(32)
    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "organization_id": org.id if org else None,
            "organization_name": org.name if org else "Personal Workspace",
            "role": user.role,
        },
        "competitions": [{"id": c.id, "name": c.name} for c in comps],
        "default_competition_id": comps[0].id if comps else None,
        "token": token,
    }
