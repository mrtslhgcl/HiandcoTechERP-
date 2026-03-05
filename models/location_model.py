from datetime  import datetime

class LocationModel:
    def __init__(self):
        self.ID : int
        self.name : str
        self.parent_location_ID : int = None
        self.description : str = ""
        self.created_at : datetime
