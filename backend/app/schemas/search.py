from typing import Dict, List
from enum import Enum
from pydantic import BaseModel, Field


class SpiderConfig(BaseModel):
    keywords: str
    location: str
    max_jobs: int
    seniority: int


class AIProviderConfig(BaseModel):
    model: str
    base_url: str
    api_key: str


class Experience(BaseModel):
    """Experience entry in CV."""
    company: str = Field(..., description="Company name")
    position: str = Field(..., description="Job position/title")
    total_months: int = Field(..., description="Total months of experience")
    description: str = Field(...,
                             description="Job description and responsibilities")


class LocationType(Enum):
    remote = "remote"
    onsite = "onsite"
    hybrid = "hybrid"
    any = "any"


class Location(BaseModel):
    """Location entry in CV."""
    country: str = Field(..., description="Country")
    city: str = Field(..., description="City")
    location_type: LocationType = Field(...,
                                        description="Type of location")


class EducationDegree(Enum):
    bachelor = "bachelor"
    master = "master"
    phd = "phd"
    diploma = "diploma"
    college = "college"
    high_school = "high_school"
    course = "course"


class Education(BaseModel):
    """Education entry in CV."""
    degree: EducationDegree = Field(..., description="Degree of education")
    title: str = Field(..., description="Title of the education")
    institution: str = Field(..., description="Institution of the education")
    total_months: int = Field(..., description="Total months of education")


class LanguageProficiency(Enum):
    a1 = 15
    a2 = 30
    b1 = 45
    b2 = 60
    c1 = 75
    c2 = 90
    native = 100


class CV(BaseModel):
    """Normalized CV schema."""
    name: str = Field(..., description="Full name of the person")
    total_experience_months: int = Field(...,
                                         description="Total months of experience")
    skills: List[str] = Field(..., description="Skills of the person")
    education: List[Education] = Field(...,
                                       description="Educational background")
    location: Location = Field(..., description="Location of the person")
    experience: List[Experience] = Field(...,
                                         description="Experience of the person")
    industries: List[str] = Field(...,
                                  description="Industries in which the person worked")
    languages: Dict[str, LanguageProficiency] = Field(...,
                                                      description="Languages spoken by the person")
