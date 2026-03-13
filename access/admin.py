import bcrypt
from django.contrib import admin
from django.utils.html import format_html
from .models import User, Role


@admin.register(User)
class UserAdmin(admin.ModelAdmin):

    # ── List view ────────────────────────────────────────────────────────────
    list_display    = ('role_id', 'email', 'role_badge', 'created_at')
    list_filter     = ('role',)
    search_fields   = ('email', 'role_id')
    ordering        = ('-created_at',)
    readonly_fields = ('role_id', 'password_hash', 'created_at')

    # ── Detail / edit form ───────────────────────────────────────────────────
    fieldsets = (
        ('Account', {
            'fields': ('email', 'role', 'role_id'),
            'description': 'Role ID is auto-generated when the user is created.',
        }),
        ('Security', {
            'fields': ('password_hash',),
            'description': 'Password is stored as a bcrypt hash. Use "Set password" below to change it.',
        }),
        ('Timestamps', {
            'fields': ('created_at',),
        }),
    )

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        if 'new_password' not in fields:
            fields = list(fields) + ['new_password']
        return fields

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        from django import forms
        form.base_fields['new_password'] = forms.CharField(
            label='Set new password',
            required=False,
            widget=forms.PasswordInput(render_value=False),
            help_text='Leave blank to keep the current password.',
        )
        return form

    def save_model(self, request, obj, form, change):
        new_password = form.cleaned_data.get('new_password')
        if new_password:
            obj.set_password(new_password)
        obj.save()

    # ── Coloured role badge ───────────────────────────────────────────────────
    ROLE_COLORS = {
        Role.MASTER_ADMIN:    ('#4A1B0C', '#F0997B'),   # coral
        Role.TENANT_ADMIN:    ('#042C53', '#85B7EB'),   # blue
        Role.DASHBOARD_ADMIN: ('#412402', '#EF9F27'),   # amber
        Role.BORROWER:        ('#173404', '#97C459'),   # green
    }

    @admin.display(description='Role')
    def role_badge(self, obj):
        color, bg = self.ROLE_COLORS.get(obj.role, ('#2C2C2A', '#D3D1C7'))
        return format_html(
            '<span style="'
            'background:{bg};color:{color};'
            'padding:2px 10px;border-radius:99px;'
            'font-size:11px;font-weight:500;'
            '">{label}</span>',
            bg=bg,
            color=color,
            label=obj.get_role_display(),
        )

    # ── Bulk actions ──────────────────────────────────────────────────────────
    actions = ['reset_to_temp_password']

    @admin.action(description='Reset selected users to temp password: changeme123')
    def reset_to_temp_password(self, request, queryset):
        for user in queryset:
            user.set_password('changeme123')
            user.save()
        self.message_user(request, f'{queryset.count()} password(s) reset to "changeme123".')