# Pydantic Basics

## What is Pydantic?
Pydantic is a Python library for data validation using Python type hints. It ensures that the data your application receives matches the expected format and type.

## Basic Model
Create a model by inheriting from BaseModel.

from pydantic import BaseModel

class User(BaseModel):
    name: str
    age: int
    email: str

## Field Validation
Pydantic validates data automatically when you create a model instance. If you pass wrong data types, it raises a ValidationError.

## Optional Fields
Use Optional to make fields optional with a default value.

from typing import Optional

class User(BaseModel):
    name: str
    age: int
    email: Optional[str] = None

## Field Constraints
Use Field to add extra validation rules like minimum and maximum values.

from pydantic import BaseModel, Field

class Product(BaseModel):
    name: str
    price: float = Field(gt=0, description="Price must be greater than 0")
    quantity: int = Field(ge=0, description="Quantity cannot be negative")

## Nested Models
Pydantic supports nested models where one model contains another.

class Address(BaseModel):
    street: str
    city: str
    country: str

class User(BaseModel):
    name: str
    address: Address

## Model Methods
Convert model to dictionary using model_dump.
Convert model to JSON string using model_dump_json.

## Validators
Add custom validation logic using field_validator decorator.

from pydantic import field_validator

class User(BaseModel):
    name: str
    age: int

    @field_validator("age")
    def age_must_be_positive(cls, v):
        if v < 0:
            raise ValueError("Age must be positive")
        return v

## Environment Variables
Pydantic can read environment variables using BaseSettings from pydantic_settings.

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    api_key: str
    debug: bool = False

    class Config:
        env_file = ".env"