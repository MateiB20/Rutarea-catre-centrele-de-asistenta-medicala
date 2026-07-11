from logging_manager import log_error

class InvalidInputError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(message)
        log_error(message)

def process_location(lon, lat, name):
    if not (47.05 <= lat <= 47.25 and 27.45 <= lon <= 27.75):
        log_error(f"Locația {name} nu este în Iași")
        raise InvalidInputError(f"Locația {name} nu este în Iași")
    return "Locație validă"



class DatabaseError(Exception):
    def __init__(self, message, errors):
        self.message = message
        super().__init__(message)
        self.errors = errors
        log_error(errors)
