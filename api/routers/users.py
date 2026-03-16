"""
Gestion des utilisateurs admin/opérateur — accès admin uniquement.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..auth import require_admin, hash_password

router = APIRouter(prefix="/api/admin/users", tags=["users"])


@router.get("/")
def list_users(db: Session = Depends(get_db), payload=Depends(require_admin)):
    users = db.query(models.User).order_by(models.User.created_at.asc()).all()
    return [
        {
            "id":         u.id,
            "username":   u.username,
            "role":       u.role,
            "is_active":  u.is_active,
            "created_at": u.created_at.isoformat() if u.created_at else None,
        }
        for u in users
    ]


@router.post("/")
def create_user(data: schemas.UserCreate, db: Session = Depends(get_db), payload=Depends(require_admin)):
    if db.query(models.User).filter(models.User.username == data.username).first():
        raise HTTPException(400, "Nom d'utilisateur déjà pris")
    if data.role not in ("admin", "operator"):
        raise HTTPException(400, "Rôle invalide (admin | operator)")

    user = models.User(
        username=data.username,
        password_hash=hash_password(data.password),
        role=data.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "username": user.username, "role": user.role, "is_active": user.is_active}


@router.put("/{user_id}")
def update_user(
    user_id: int,
    data: schemas.UserUpdate,
    db: Session = Depends(get_db),
    payload=Depends(require_admin),
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(404, "Utilisateur introuvable")

    # Protège le dernier admin contre une rétrogradation
    if data.role == "operator" and user.role == "admin":
        admin_count = db.query(models.User).filter(models.User.role == "admin").count()
        if admin_count <= 1:
            raise HTTPException(400, "Impossible de rétrograder le dernier administrateur")

    if data.password:
        user.password_hash = hash_password(data.password)
    if data.role is not None:
        user.role = data.role
    if data.is_active is not None:
        user.is_active = data.is_active

    db.commit()
    db.refresh(user)
    return {"id": user.id, "username": user.username, "role": user.role, "is_active": user.is_active}


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    payload=Depends(require_admin),
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(404, "Utilisateur introuvable")

    # Interdit de se supprimer soi-même
    if user.username == payload.get("sub"):
        raise HTTPException(400, "Vous ne pouvez pas supprimer votre propre compte")

    # Interdit de supprimer le dernier admin
    if user.role == "admin":
        admin_count = db.query(models.User).filter(models.User.role == "admin").count()
        if admin_count <= 1:
            raise HTTPException(400, "Impossible de supprimer le dernier administrateur")

    db.delete(user)
    db.commit()
    return {"message": "Utilisateur supprimé"}
