class SessionAlreadyActiveError(Exception):
    pass

class InvalidTopicCountError(Exception):
    pass

class DuplicateTopicError(Exception):
    pass

class InsufficientQuestionPoolError(Exception):
    pass

class QuestionAlreadyOpenedError(Exception):
    pass

class QuestionAlreadyJudgedError(Exception):
    pass

class PlayerNotInSessionError(Exception):
    pass

class InvalidAdjustmentAmountError(Exception):
    pass

class NoActiveSessionError(Exception):
    pass