from enum import IntFlag


class Validation(IntFlag):
    ALL = 31
    ACCEPTED = 16
    REJECTED = 8
    UNCERTAIN = 4
    UNCHECKED = 2
    DISPUTED = 1

    @staticmethod
    def get(valid):
        validation_filter = 0
        for type in valid:
            if type == 'accepted':
                validation_filter |= Validation.ACCEPTED
            if type == 'rejected':
                validation_filter |= Validation.REJECTED
            if type == 'uncertain':
                validation_filter |= Validation.UNCERTAIN
            if type == 'unchecked':
                validation_filter |= Validation.UNCHECKED
            if type == 'disputed':
                validation_filter |= Validation.DISPUTED

        return validation_filter if validation_filter != 0 else Validation.ALL
