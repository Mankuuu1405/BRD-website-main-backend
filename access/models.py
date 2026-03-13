from django.db import models
import bcrypt


class Role(models.TextChoices):
    MASTER_ADMIN    = 'master_admin',    'Master Admin'
    TENANT_ADMIN    = 'tenant_admin',    'Tenant Admin'
    DASHBOARD_ADMIN = 'dashboard_admin', 'Dashboard Admin'
    BORROWER        = 'borrower',        'Borrower'


ROLE_PREFIX = {
    Role.MASTER_ADMIN:    'MA',
    Role.TENANT_ADMIN:    'TA',
    Role.DASHBOARD_ADMIN: 'DA',
    Role.BORROWER:        'BR',
}


def generate_role_id(role: str) -> str:
    """Auto-generate a role-based ID like MA-00001, BR-00042 etc."""
    prefix = ROLE_PREFIX.get(role, 'US')
    count  = User.objects.filter(role=role).count() + 1
    return f'{prefix}-{count:05d}'


class User(models.Model):
    email         = models.EmailField(unique=True)
    password_hash = models.CharField(max_length=255)
    role          = models.CharField(max_length=32, choices=Role.choices)
    role_id       = models.CharField(max_length=20, unique=True, blank=True)
    created_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'users'

    def save(self, *args, **kwargs):
        # Auto-generate role_id only on first save
        if not self.role_id:
            self.role_id = generate_role_id(self.role)
        super().save(*args, **kwargs)

    def set_password(self, raw_password: str):
        self.password_hash = bcrypt.hashpw(
            raw_password.encode(), bcrypt.gensalt()
        ).decode()

    def check_password(self, raw_password: str) -> bool:
        return bcrypt.checkpw(
            raw_password.encode(),
            self.password_hash.encode()
        )

    def __str__(self):
        return f'{self.role_id} — {self.email}'