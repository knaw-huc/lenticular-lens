from enum import IntFlag


class Validation(IntFlag):
    ALL = 31
    ACCEPTED = 16
    REJECTED = 8
    NOT_SURE = 4
    NOT_VALIDATED = 2
    MIXED = 1

    @staticmethod
    def get(valid):
        validation_filter = 0
        for type in valid:
            if type == 'accepted':
                validation_filter |= Validation.ACCEPTED
            if type == 'rejected':
                validation_filter |= Validation.REJECTED
            if type == 'not_sure':
                validation_filter |= Validation.NOT_SURE
            if type == 'not_validated':
                validation_filter |= Validation.NOT_VALIDATED
            if type == 'mixed':
                validation_filter |= Validation.MIXED

        return validation_filter if validation_filter != 0 else Validation.ALL
