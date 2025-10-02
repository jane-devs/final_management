"""initial migration

Revision ID: 5fad9aae7069
Revises: 
Create Date: 2025-10-01 20:28:01.926974

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5fad9aae7069'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('users',
        sa.Column('first_name', sa.String(length=100), nullable=False),
        sa.Column('last_name', sa.String(length=100), nullable=False),
        sa.Column('role', sa.Enum('USER', 'MANAGER', 'ADMIN', name='userrole'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('email', sa.String(length=320), nullable=False),
        sa.Column('hashed_password', sa.String(length=1024), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_superuser', sa.Boolean(), nullable=False),
        sa.Column('is_verified', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    
    op.create_table('teams',
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('invite_code', sa.String(length=50), nullable=True),
        sa.Column('owner_id', sa.UUID(), nullable=True),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('invite_code')
    )
    op.create_index(op.f('ix_teams_id'), 'teams', ['id'], unique=False)
    
    op.add_column('users', sa.Column('team_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_users_team_id', 'users', 'teams', ['team_id'], ['id'])
    op.create_table('meetings',
    sa.Column('title', sa.String(length=200), nullable=False, comment='Название встречи'),
    sa.Column('description', sa.Text(), nullable=True, comment='Описание встречи, повестка дня'),
    sa.Column('start_time', sa.DateTime(timezone=True), nullable=False, comment='Дата и время начала встречи'),
    sa.Column('end_time', sa.DateTime(timezone=True), nullable=False, comment='Дата и время окончания встречи'),
    sa.Column('location', sa.String(length=255), nullable=True, comment='Место проведения встречи или ссылка на видеоконференцию'),
    sa.Column('creator_id', sa.UUID(), nullable=False, comment='ID создателя встречи'),
    sa.Column('team_id', sa.Integer(), nullable=False, comment='ID команды'),
    sa.Column('id', sa.Integer(), nullable=False, comment='Уникальный идентификатор записи'),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True, comment='Дата создания записи'),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True, comment='Дата последнего обновления'),
    sa.ForeignKeyConstraint(['creator_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_meetings_id'), 'meetings', ['id'], unique=False)
    op.create_table('tasks',
    sa.Column('title', sa.String(length=200), nullable=False, comment='Заголовок задачи'),
    sa.Column('description', sa.Text(), nullable=True, comment='Подробное описание задачи'),
    sa.Column('status', sa.Enum('OPEN', 'IN_PROGRESS', 'COMPLETED', name='taskstatus'), nullable=True, comment='Текущий статус задачи'),
    sa.Column('priority', sa.Enum('LOW', 'MEDIUM', 'HIGH', 'URGENT', name='taskpriority'), nullable=True, comment='Приоритет задачи'),
    sa.Column('deadline', sa.DateTime(timezone=True), nullable=True, comment='Крайний срок выполнения задачи'),
    sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True, comment='Дата и время завершения задачи'),
    sa.Column('creator_id', sa.UUID(), nullable=False, comment='ID создателя задачи'),
    sa.Column('assignee_id', sa.UUID(), nullable=True, comment='ID исполнителя задачи'),
    sa.Column('team_id', sa.Integer(), nullable=False, comment='ID команды, к которой относится задача'),
    sa.Column('id', sa.Integer(), nullable=False, comment='Уникальный идентификатор записи'),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True, comment='Дата создания записи'),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True, comment='Дата последнего обновления'),
    sa.ForeignKeyConstraint(['assignee_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['creator_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tasks_id'), 'tasks', ['id'], unique=False)
    op.create_table('evaluations',
    sa.Column('score', sa.Integer(), nullable=False, comment='Оценка от 1 до 5 баллов'),
    sa.Column('comment', sa.Text(), nullable=True, comment='Комментарий к оценке от руководителя'),
    sa.Column('task_id', sa.Integer(), nullable=False, comment='ID оцениваемой задачи'),
    sa.Column('user_id', sa.UUID(), nullable=False, comment='ID оцениваемого пользователя'),
    sa.Column('evaluator_id', sa.UUID(), nullable=False, comment='ID того, кто ставит оценку'),
    sa.Column('id', sa.Integer(), nullable=False, comment='Уникальный идентификатор записи'),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True, comment='Дата создания записи'),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True, comment='Дата последнего обновления'),
    sa.CheckConstraint('score >= 1 AND score <= 5', name='valid_score_range'),
    sa.CheckConstraint('user_id != evaluator_id', name='cannot_evaluate_self'),
    sa.ForeignKeyConstraint(['evaluator_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_evaluations_id'), 'evaluations', ['id'], unique=False)
    op.create_table('meeting_participants',
    sa.Column('meeting_id', sa.Integer(), nullable=False, comment='ID встречи'),
    sa.Column('user_id', sa.UUID(), nullable=False, comment='ID участника'),
    sa.ForeignKeyConstraint(['meeting_id'], ['meetings.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('meeting_id', 'user_id'),
    comment='Связь между встречами и их участниками'
    )
    op.create_table('task_comments',
    sa.Column('content', sa.Text(), nullable=False, comment='Текст комментария'),
    sa.Column('task_id', sa.Integer(), nullable=False, comment='ID задачи, к которой относится комментарий'),
    sa.Column('author_id', sa.UUID(), nullable=False, comment='ID автора комментария'),
    sa.Column('id', sa.Integer(), nullable=False, comment='Уникальный идентификатор записи'),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True, comment='Дата создания записи'),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True, comment='Дата последнего обновления'),
    sa.ForeignKeyConstraint(['author_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_task_comments_id'), 'task_comments', ['id'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_task_comments_id'), table_name='task_comments')
    op.drop_table('task_comments')
    op.drop_table('meeting_participants')
    op.drop_index(op.f('ix_evaluations_id'), table_name='evaluations')
    op.drop_table('evaluations')
    op.drop_index(op.f('ix_tasks_id'), table_name='tasks')
    op.drop_table('tasks')
    op.drop_index(op.f('ix_meetings_id'), table_name='meetings')
    op.drop_table('meetings')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    op.drop_index(op.f('ix_teams_id'), table_name='teams')
    op.drop_table('teams')
    # ### end Alembic commands ###
