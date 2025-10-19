class User:
    """A base class for all users in the system."""
    def __init__(self, user_id, name):
        self.id = user_id
        self.name = name