class TeamException(Exception):
    """Базовое исключение для работы с командами"""
    def __init__(self, message: str, detail: str = None):
        self.message = message
        self.detail = detail
        super().__init__(self.message)


class TeamNotFound(TeamException):
    """Команда не найдена"""
    def __init__(self, team_id: int = None):
        message = f"Команда с ID {team_id} не найдена" if team_id else "Команда не найдена"
        super().__init__(message)


class TeamAccessDenied(TeamException):
    """Нет доступа к команде"""
    def __init__(self, message: str = "Нет доступа к этой команде"):
        super().__init__(message)


class TeamOwnershipRequired(TeamException):
    """Требуются права владельца команды"""
    def __init__(self, action: str = None):
        message = f"Только владелец команды может {action}" if action else "Требуются права владельца команды"
        super().__init__(message)


class InvalidInviteCode(TeamException):
    """Неверный код приглашения"""
    def __init__(self):
        super().__init__("Неверный код приглашения")


class AlreadyInTeam(TeamException):
    """Пользователь уже состоит в команде"""
    def __init__(self):
        super().__init__("Вы уже состоите в команде")


class NotInTeam(TeamException):
    """Пользователь не состоит в команде"""
    def __init__(self, team_id: int = None):
        message = f"Вы не состоите в команде {team_id}" if team_id else "Вы не состоите в этой команде"
        super().__init__(message)


class OwnerCannotLeaveTeam(TeamException):
    """Владелец не может покинуть команду"""
    def __init__(self):
        super().__init__(
            "Владелец не может покинуть команду. Сначала передайте права или удалите команду"
        )


class AppException(Exception):
    """Базовое исключение приложения"""
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class ValidationError(AppException):
    """Ошибка валидации"""
    def __init__(self, message: str, field: str = None):
        self.field = field
        super().__init__(message, 422)


class NotFoundError(AppException):
    """Ресурс не найден"""
    def __init__(self, resource: str = "Ресурс"):
        super().__init__(f"{resource} не найден", 404)


class ForbiddenError(AppException):
    """Доступ запрещен"""
    def __init__(self, message: str = "Доступ запрещен"):
        super().__init__(message, 403)


class UnauthorizedError(AppException):
    """Не авторизован"""
    def __init__(self, message: str = "Требуется авторизация"):
        super().__init__(message, 401)


class AuthException(AppException):
    """Базовое исключение для аутентификации"""
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message, status_code)


class InvalidCredentials(AuthException):
    """Неверные учетные данные"""
    def __init__(self):
        super().__init__("Неверный email или пароль", 401)


class UserAlreadyExists(AuthException):
    """Пользователь уже существует"""
    def __init__(self, email: str = None):
        message = f"Пользователь с email {email} уже существует" if email else "Пользователь уже существует"
        super().__init__(message, 400)


class UserNotFound(AuthException):
    """Пользователь не найден"""
    def __init__(self, identifier: str = None):
        message = f"Пользователь {identifier} не найден" if identifier else "Пользователь не найден"
        super().__init__(message, 404)


class UserNotActive(AuthException):
    """Пользователь неактивен"""
    def __init__(self):
        super().__init__("Аккаунт пользователя деактивирован", 403)


class UserNotVerified(AuthException):
    """Пользователь не верифицирован"""
    def __init__(self):
        super().__init__("Email не верифицирован", 403)


class InvalidToken(AuthException):
    """Недействительный токен"""
    def __init__(self, token_type: str = "токен"):
        super().__init__(f"Недействительный {token_type}", 401)


class TokenExpired(AuthException):
    """Токен истек"""
    def __init__(self, token_type: str = "токен"):
        super().__init__(f"{token_type.capitalize()} истек", 401)


class WeakPassword(AuthException):
    """Слабый пароль"""
    def __init__(self, requirements: str = None):
        message = f"Пароль не соответствует требованиям: {requirements}" if requirements else "Пароль слишком слабый"
        super().__init__(message, 400)


class PermissionDenied(AuthException):
    """Недостаточно прав"""
    def __init__(self, required_role: str = None):
        message = f"Требуется роль: {required_role}" if required_role else "Недостаточно прав для выполнения операции"
        super().__init__(message, 403)


class TaskException(AppException):
    """Базовое исключение для работы с задачами"""
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message, status_code)


class TaskNotFound(TaskException):
    """Задача не найдена"""
    def __init__(self, task_id: int = None):
        message = f"Задача с ID {task_id} не найдена" if task_id else "Задача не найдена"
        super().__init__(message, 404)


class TaskAccessDenied(TaskException):
    """Нет доступа к задаче"""
    def __init__(self, action: str = None):
        message = f"Нет прав на {action} задачи" if action else "Нет доступа к этой задаче"
        super().__init__(message, 403)


class TaskTeamMismatch(TaskException):
    """Задача принадлежит другой команде"""
    def __init__(self):
        super().__init__("Вы можете работать только с задачами своей команды", 403)


class AssigneeNotInTeam(TaskException):
    """Назначаемый пользователь не состоит в команде задачи"""
    def __init__(self):
        super().__init__("Пользователь не состоит в команде этой задачи", 400)


class TaskAlreadyCompleted(TaskException):
    """Задача уже выполнена"""
    def __init__(self):
        super().__init__("Задача уже выполнена", 400)


class InvalidTaskStatus(TaskException):
    """Недопустимый статус задачи"""
    def __init__(self, current_status: str, target_status: str):
        super().__init__(f"Нельзя изменить статус с '{current_status}' на '{target_status}'", 400)


class TaskCreationError(TaskException):
    """Ошибка создания задачи"""
    def __init__(self, reason: str = None):
        message = f"Ошибка создания задачи: {reason}" if reason else "Ошибка создания задачи"
        super().__init__(message, 400)


class MeetingException(AppException):
    """Базовое исключение для работы с встречами"""
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message, status_code)


class MeetingNotFound(MeetingException):
    """Встреча не найдена"""
    def __init__(self, meeting_id: int = None):
        message = f"Встреча с ID {meeting_id} не найдена" if meeting_id else "Встреча не найдена"
        super().__init__(message, 404)


class MeetingAccessDenied(MeetingException):
    """Нет доступа к встрече"""
    def __init__(self, action: str = None):
        message = f"Нет прав на {action} встречи" if action else "Нет доступа к этой встрече"
        super().__init__(message, 403)


class MeetingTimeConflict(MeetingException):
    """Конфликт времени встречи"""
    def __init__(self, participants_count: int = None):
        message = f"Обнаружены конфликты времени для {participants_count} участников" if participants_count else "Конфликт времени встречи"
        super().__init__(message, 400)


class MeetingTeamMismatch(MeetingException):
    """Встреча принадлежит другой команде"""
    def __init__(self):
        super().__init__("Вы можете работать только с встречами своей команды", 403)


class CommentException(AppException):
    """Базовое исключение для работы с комментариями"""
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message, status_code)


class CommentNotFound(CommentException):
    """Комментарий не найден"""
    def __init__(self, comment_id: int = None):
        message = f"Комментарий с ID {comment_id} не найден" if comment_id else "Комментарий не найден"
        super().__init__(message, 404)


class CommentAccessDenied(CommentException):
    """Нет доступа к комментарию"""
    def __init__(self, action: str = None):
        message = f"Нет прав на {action} комментария" if action else "Нет доступа к этому комментарию"
        super().__init__(message, 403)


class EvaluationException(AppException):
    """Базовое исключение для работы с оценками"""
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message, status_code)


class EvaluationNotFound(EvaluationException):
    """Оценка не найдена"""
    def __init__(self, evaluation_id: int = None):
        message = f"Оценка с ID {evaluation_id} не найдена" if evaluation_id else "Оценка не найдена"
        super().__init__(message, 404)


class EvaluationAccessDenied(EvaluationException):
    """Нет доступа к оценке"""
    def __init__(self, action: str = None):
        message = f"Нет прав на {action} оценки" if action else "Нет доступа к этой оценке"
        super().__init__(message, 403)
