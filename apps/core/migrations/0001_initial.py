"""
Initial migration for core app with all models and constraints.
"""
import django.contrib.postgres.fields.ranges
import django.contrib.postgres.indexes
import django.contrib.postgres.constraints
from django.conf import settings
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.operations import BtreeGistExtension
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        # Enable btree_gist extension for ExclusionConstraint
        BtreeGistExtension(),
        
        migrations.CreateModel(
            name='Role',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=64, unique=True)),
            ],
            options={
                'verbose_name': 'Role',
                'verbose_name_plural': 'Roles',
                'db_table': 'core_role',
            },
        ),
        migrations.CreateModel(
            name='Team',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128, unique=True)),
            ],
            options={
                'verbose_name': 'Team',
                'verbose_name_plural': 'Teams',
                'db_table': 'core_team',
            },
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, verbose_name='username')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='email address')),
                ('role', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.role')),
                ('team', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.team')),
            ],
            options={
                'verbose_name': 'User',
                'verbose_name_plural': 'Users',
                'db_table': 'core_user',
            },
        ),
        migrations.CreateModel(
            name='Room',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=32, unique=True)),
                ('name', models.CharField(max_length=128)),
                ('capacity', models.IntegerField(blank=True, null=True)),
                ('features', models.JSONField(blank=True, default=dict)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name': 'Room',
                'verbose_name_plural': 'Rooms',
                'db_table': 'core_room',
            },
        ),
        migrations.CreateModel(
            name='ItemCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=64, unique=True)),
                ('slug', models.SlugField(max_length=64, unique=True)),
                ('description', models.TextField(blank=True, default='')),
            ],
            options={
                'verbose_name': 'Item Category',
                'verbose_name_plural': 'Item Categories',
                'db_table': 'core_item_category',
            },
        ),
        migrations.CreateModel(
            name='Item',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128)),
                ('status', models.CharField(choices=[('ACTIVE', 'Active'), ('BROKEN', 'Broken'), ('LOST', 'Lost')], default='ACTIVE', max_length=16)),
                ('meta', models.JSONField(blank=True, default=dict)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='items', to='core.itemcategory')),
                ('room', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='items', to='core.room')),
            ],
            options={
                'verbose_name': 'Item',
                'verbose_name_plural': 'Items',
                'db_table': 'core_item',
            },
        ),
        migrations.CreateModel(
            name='Request',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('WAITING', 'Waiting'), ('APPROVED', 'Approved'), ('DISMISSED', 'Dismissed')], default='WAITING', max_length=16)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('status_changed_at', models.DateTimeField(auto_now=True)),
                ('note', models.TextField(blank=True, default='')),
                ('decided_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='decided_requests', to=settings.AUTH_USER_MODEL)),
                ('room', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='requests', to='core.room')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='requests', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Request',
                'verbose_name_plural': 'Requests',
                'db_table': 'core_request',
            },
        ),
        migrations.CreateModel(
            name='Appointment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_at', models.DateTimeField()),
                ('end_at', models.DateTimeField()),
                ('time_range', django.contrib.postgres.fields.ranges.DateTimeRangeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('item', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='appointments', to='core.item')),
                ('request', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='appointments', to='core.request')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='appointments', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Appointment',
                'verbose_name_plural': 'Appointments',
                'db_table': 'core_appointment',
            },
        ),
        migrations.AddField(
            model_name='team',
            name='manager',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='managed_teams', to=settings.AUTH_USER_MODEL),
        ),
        # Indexes
        migrations.AddIndex(
            model_name='room',
            index=models.Index(fields=['is_active'], name='core_room_is_active_idx'),
        ),
        migrations.AddIndex(
            model_name='item',
            index=models.Index(fields=['room', 'status'], name='core_item_room_status_idx'),
        ),
        migrations.AddIndex(
            model_name='request',
            index=models.Index(fields=['status', 'created_at'], name='core_request_status_created_idx'),
        ),
        migrations.AddIndex(
            model_name='appointment',
            index=models.Index(fields=['item', 'start_at'], name='core_appointment_item_start_idx'),
        ),
        # GistIndex for time_range
        migrations.AddIndex(
            model_name='appointment',
            index=django.contrib.postgres.indexes.GistIndex(fields=['time_range'], name='core_appointment_time_range_gist_idx'),
        ),
        # CheckConstraint for end_at > start_at
        migrations.AddConstraint(
            model_name='appointment',
            constraint=models.CheckConstraint(check=models.Q(('end_at__gt', models.F('start_at'))), name='appointment_end_after_start'),
        ),
        # ExclusionConstraint for overlapping appointments on same item
        migrations.AddConstraint(
            model_name='appointment',
            constraint=django.contrib.postgres.constraints.ExclusionConstraint(
                expressions=[
                    ('item', '='),
                    ('time_range', '&&'),
                ],
                name='exclude_overlap_per_item',
            ),
        ),
        # User permissions
        migrations.AddField(
            model_name='user',
            name='groups',
            field=models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups'),
        ),
        migrations.AddField(
            model_name='user',
            name='user_permissions',
            field=models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions'),
        ),
    ]

