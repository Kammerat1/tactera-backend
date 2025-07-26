# club_models.py

from pydantic import BaseModel


# This is the structure of the data we expect when registering a club
class ClubRegister(BaseModel):
    club_name: str
    manager_email: str

