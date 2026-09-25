import enum


class RoleEnum(str, enum.Enum):
    ADMIN = "ADMIN"
    PM = "PM"
    OCP = "OCP"
    OCVP = "OCVP"
    OC = "OC"


class PartnerTypeEnum(str, enum.Enum):
    SPONSORING = "SPONSORING"
    FOOD = "FOOD"
    DRINKS = "DRINKS"
    FINANCIAL = "FINANCIAL"
    MEDIA = "MEDIA"
    STRATEGIC = "STRATEGIC"
    EVENT = "EVENT"
    SPEAKER = "SPEAKER"
    OTHER = "OTHER"


class PartnerStatusEnum(str, enum.Enum):
    NEW = "NEW"
    CONTACTED = "CONTACTED"
    FOLLOW_UP = "FOLLOW_UP"
    NEGOTIATION = "NEGOTIATION"
    SIGNED = "SIGNED"
    REJECTED = "REJECTED"
    NOT_INTERESTED = "NOT_INTERESTED"


class TargetListItemStatusEnum(str, enum.Enum):
    PROSPECT = "PROSPECT"
    CONTACTED = "CONTACTED"
    RESPONDED = "RESPONDED"
    FOLLOW_UP = "FOLLOW_UP"
    NEGOTIATION = "NEGOTIATION"
    SIGNED = "SIGNED"
    REJECTED = "REJECTED"
    NOT_INTERESTED = "NOT_INTERESTED"


class ContactMethodEnum(str, enum.Enum):
    EMAIL = "EMAIL"
    CALL = "CALL"
    MEETING = "MEETING"
    SOCIAL = "SOCIAL"
    OTHER = "OTHER"


class SpeakerStatusEnum(str, enum.Enum):
    PROSPECT = "PROSPECT"
    CONTACTED = "CONTACTED"
    INTERESTED = "INTERESTED"
    CONFIRMED = "CONFIRMED"
    DECLINED = "DECLINED"
    FOLLOW_UP = "FOLLOW_UP"


class TaskStatusEnum(str, enum.Enum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    OVERDUE = "OVERDUE"
    CANCELLED = "CANCELLED"


class TaskPriorityEnum(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class GoalScopeEnum(str, enum.Enum):
    PROJECT = "PROJECT"
    DEPARTMENT = "DEPARTMENT"
    INDIVIDUAL = "INDIVIDUAL"


class GoalStatusEnum(str, enum.Enum):
    ON_TRACK = "ON_TRACK"
    AT_RISK = "AT_RISK"
    ACHIEVED = "ACHIEVED"
    MISSED = "MISSED"


class MktStatusEnum(str, enum.Enum):
    PLANNED = "PLANNED"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"
    DELAYED = "DELAYED"


class ImportBatchStatusEnum(str, enum.Enum):
    PENDING = "PENDING"
    VALIDATED = "VALIDATED"
    COMMITTED = "COMMITTED"
    FAILED = "FAILED"


class ImportRowStatusEnum(str, enum.Enum):
    NEW = "NEW"
    DUPLICATE = "DUPLICATE"
    ERROR = "ERROR"
