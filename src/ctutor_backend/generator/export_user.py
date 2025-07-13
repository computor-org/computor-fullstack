from typing import Optional
import pandas as pd
from pydantic import BaseModel, EmailStr, Field
from text_unidecode import unidecode

# pip install odfpy

class ExportUser(BaseModel):
  first_name: str = Field()
  family_name: str = Field()
  email: EmailStr = Field()
  username: Optional[str] = Field(default=None)
  role: str

  @staticmethod
  def read_excel(file_path: str):

    if file_path.endswith(".ods"):
      df = pd.read_excel(file_path, engine="odf")
    elif file_path.endswith(".xlsx"):
      df = pd.read_excel(file_path)
    elif file_path.endswith(".csv"):
      df = pd.read_csv(file_path)
    else:
      raise Exception("File format unknown.")
    
    df.fillna(value="-", inplace=True)

    users: list[ExportUser] = []
    for index, row in df.iterrows():
        
      first_name = str(row["first_name"]).rstrip().lstrip()
      family_name = str(row["family_name"]).rstrip().lstrip()
      email = str(row["email"]).rstrip().lstrip()
      username = str(row["username"]).rstrip().lstrip().removeprefix("@")
      role = str(row["role"]).rstrip().lstrip()

      users.append(ExportUser(
        first_name=first_name,
        family_name=family_name,
        email=email,
        username=username,
        role=role))
    
    return users
  
  @staticmethod
  def replace_special_chars(name: str) -> str:
    return unidecode(name.lower().replace("ö","oe").replace("ä","ae").replace("ü","ue").encode().decode("utf8"))
  
  def gitlab_project_path(self):
    first_name = ExportUser.replace_special_chars(self.first_name).replace(" ", "_")
    family_name = ExportUser.replace_special_chars(self.family_name).replace(" ", "_")

    return f"{family_name}_{first_name}"

  def gitlab_project_name(self):
    return f"{self.first_name} {self.family_name}"
  
  def get_first_name_utf8(self):
    first_name = self.replace_special_chars(self.first_name)
    return " ".join(elem.capitalize() for elem in first_name.split())

  def get_family_name_utf8(self):
    family_name = self.replace_special_chars(self.family_name)
    return " ".join(elem.capitalize() for elem in family_name.split())