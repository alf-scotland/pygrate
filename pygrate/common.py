import enum


class SourceAction(str, enum.Enum):
    """ Enum constants used to define actions on source paths """

    NOT_DEFINED = 'Not defined'
    
    COPY = 'Copy'
    
    MOVE = 'Move'
    
    DELETE = 'Delete'
