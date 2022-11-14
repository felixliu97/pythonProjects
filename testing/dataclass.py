from dataclasses import dataclass

@dataclass
class Person:
    name: str
    address: str

person = Person(name="John", address="123 Main Street")
print(person)