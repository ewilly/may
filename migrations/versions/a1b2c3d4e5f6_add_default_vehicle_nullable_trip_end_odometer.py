"""add default_vehicle_id to users, make trip end_odometer nullable

Revision ID: a1b2c3d4e5f6
Revises: 613be8af4376
Create Date: 2026-04-18 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '613be8af4376'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('default_vehicle_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_users_default_vehicle', 'vehicles', ['default_vehicle_id'], ['id'])

    with op.batch_alter_table('trips', schema=None) as batch_op:
        batch_op.alter_column('end_odometer', existing_type=sa.Float(), nullable=True)


def downgrade():
    with op.batch_alter_table('trips', schema=None) as batch_op:
        batch_op.alter_column('end_odometer', existing_type=sa.Float(), nullable=False)

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_constraint('fk_users_default_vehicle', type_='foreignkey')
        batch_op.drop_column('default_vehicle_id')
