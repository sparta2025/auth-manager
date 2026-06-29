"""Seed script v3 — idempotent."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.models import Permission, Role, RolePermission, User, UserRole

ROLES = [
    {"name": "administrator", "description": "Полный доступ к системе", "is_system": True},
    {"name": "manager",       "description": "Управление отчётами и документами", "is_system": False},
    {"name": "user",          "description": "Базовый доступ (по умолчанию)", "is_system": False},
]

PERMISSIONS = [
    {"code": "users:create",   "resource": "users",     "action": "create"},
    {"code": "users:read",     "resource": "users",     "action": "read"},
    {"code": "users:update",   "resource": "users",     "action": "update"},
    {"code": "users:delete",   "resource": "users",     "action": "delete"},
    {"code": "users:manage",   "resource": "users",     "action": "manage"},
    {"code": "reports:create", "resource": "reports",   "action": "create"},
    {"code": "reports:read",   "resource": "reports",   "action": "read"},
    {"code": "reports:update", "resource": "reports",   "action": "update"},
    {"code": "reports:delete", "resource": "reports",   "action": "delete"},
    {"code": "documents:create","resource": "documents","action": "create"},
    {"code": "documents:read", "resource": "documents", "action": "read"},
    {"code": "documents:update","resource": "documents","action": "update"},
    {"code": "documents:delete","resource": "documents","action": "delete"},
    {"code": "settings:read",  "resource": "settings",  "action": "read"},
    {"code": "settings:update","resource": "settings",  "action": "update"},
    {"code": "audit:read",     "resource": "audit",     "action": "read"},
    {"code": "notifications:read","resource":"notifications","action":"read"},
]

ROLE_PERMISSIONS = {
    "administrator": [p["code"] for p in PERMISSIONS],
    "manager": [
        "reports:create","reports:read","reports:update","reports:delete",
        "documents:create","documents:read","documents:update","documents:delete",
        "settings:read",
    ],
    "user": ["reports:read","documents:read","settings:read"],
}

USERS = [
    # ── Существующие (seed-пользователи) ──
    {"email":"admin@example.com",   "password":"Admin1234!",   "first_name":"Admin",   "last_name":"System",  "role":"administrator"},
    {"email":"manager@example.com", "password":"Manager1234!", "first_name":"John",    "last_name":"Manager", "role":"manager"},
    {"email":"user@example.com",    "password":"User1234!",    "first_name":"Jane",    "last_name":"User",    "role":"user"},

    # ── 10 менеджеров ──
    {"email":"manager1@example.com",  "password":"Test1234!", "first_name":"Алексей",   "last_name":"Соколов",    "role":"manager"},
    {"email":"manager2@example.com",  "password":"Test1234!", "first_name":"Ольга",     "last_name":"Белова",     "role":"manager"},
    {"email":"manager3@example.com",  "password":"Test1234!", "first_name":"Дмитрий",   "last_name":"Козлов",     "role":"manager"},
    {"email":"manager4@example.com",  "password":"Test1234!", "first_name":"Елена",     "last_name":"Новикова",   "role":"manager"},
    {"email":"manager5@example.com",  "password":"Test1234!", "first_name":"Сергей",     "last_name":"Морозов",    "role":"manager"},
    {"email":"manager6@example.com",  "password":"Test1234!", "first_name":"Анна",      "last_name":"Волкова",    "role":"manager"},
    {"email":"manager7@example.com",  "password":"Test1234!", "first_name":"Павел",     "last_name":"Зайцев",     "role":"manager"},
    {"email":"manager8@example.com",  "password":"Test1234!", "first_name":"Татьяна",   "last_name":"Соловьёва",  "role":"manager"},
    {"email":"manager9@example.com",  "password":"Test1234!", "first_name":"Николай",   "last_name":"Васильев",   "role":"manager"},
    {"email":"manager10@example.com", "password":"Test1234!", "first_name":"Юлия",      "last_name":"Павлова",    "role":"manager"},

    # ── 10 пользователей ──
    {"email":"user1@example.com",  "password":"Test1234!", "first_name":"Иван",     "last_name":"Петров",     "role":"user"},
    {"email":"user2@example.com",  "password":"Test1234!", "first_name":"Мария",    "last_name":"Кузнецова",  "role":"user"},
    {"email":"user3@example.com",  "password":"Test1234!", "first_name":"Андрей",   "last_name":"Смирнов",    "role":"user"},
    {"email":"user4@example.com",  "password":"Test1234!", "first_name":"Екатерина","last_name":"Иванова",    "role":"user"},
    {"email":"user5@example.com",  "password":"Test1234!", "first_name":"Максим",   "last_name":"Попов",      "role":"user"},
    {"email":"user6@example.com",  "password":"Test1234!", "first_name":"Наталья",  "last_name":"Фёдорова",   "role":"user"},
    {"email":"user7@example.com",  "password":"Test1234!", "first_name":"Артём",    "last_name":"Орлов",      "role":"user"},
    {"email":"user8@example.com",  "password":"Test1234!", "first_name":"Светлана", "last_name":"Михайлова",  "role":"user"},
    {"email":"user9@example.com",  "password":"Test1234!", "first_name":"Владимир", "last_name":"Титов",      "role":"user"},
    {"email":"user10@example.com", "password":"Test1234!", "first_name":"Ксения",   "last_name":"Громова",    "role":"user"},
]


def seed() -> None:
    db = SessionLocal()
    try:
        print("Seeding roles...")
        role_map: dict[str, Role] = {}
        for r in ROLES:
            existing = db.query(Role).filter(Role.name == r["name"]).first()
            if not existing:
                role = Role(name=r["name"], description=r["description"], is_system=r["is_system"])
                db.add(role); db.flush()
                role_map[r["name"]] = role
                print(f"  + role: {r['name']}")
            else:
                # Update is_system flag if needed
                existing.is_system = r["is_system"]
                role_map[r["name"]] = existing

        print("Seeding permissions...")
        perm_map: dict[str, Permission] = {}
        for p in PERMISSIONS:
            existing = db.query(Permission).filter(Permission.code == p["code"]).first()
            if not existing:
                perm = Permission(**p)
                db.add(perm); db.flush()
                perm_map[p["code"]] = perm
                print(f"  + permission: {p['code']}")
            else:
                perm_map[p["code"]] = existing

        print("Assigning permissions to roles...")
        for role_name, codes in ROLE_PERMISSIONS.items():
            role = role_map[role_name]
            for code in codes:
                perm = perm_map.get(code)
                if not perm:
                    continue
                exists = (db.query(RolePermission)
                          .filter(RolePermission.role_id == role.id,
                                  RolePermission.permission_id == perm.id).first())
                if not exists:
                    db.add(RolePermission(role_id=role.id, permission_id=perm.id))
        db.flush()

        print("Seeding users...")
        for u in USERS:
            existing = db.query(User).filter(User.email == u["email"]).first()
            if not existing:
                user = User(
                    email=u["email"],
                    password_hash=hash_password(u["password"]),
                    first_name=u["first_name"], last_name=u["last_name"],
                    is_active=True,
                )
                db.add(user); db.flush()
                role = role_map[u["role"]]
                db.add(UserRole(user_id=user.id, role_id=role.id))
                db.flush()
                print(f"  + user: {u['email']} ({u['role']})")

        db.commit()
        print("Seed complete.")
    except Exception as exc:
        db.rollback()
        print(f"Seed failed: {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
