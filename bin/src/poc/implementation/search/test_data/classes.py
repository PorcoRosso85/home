"""Classes test file"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


class BaseClass:
    """基底クラス"""
    
    def base_method(self):
        return "base"


class DerivedClass(BaseClass):
    """派生クラス"""
    
    def __init__(self):
        super().__init__()
        self.value = 0
    
    def derived_method(self):
        return "derived"
    
    @property
    def get_value(self):
        return self.value
    
    @staticmethod
    def static_method():
        return "static"
    
    @classmethod
    def class_method(cls):
        return "class"


class AbstractClass(ABC):
    """抽象クラス"""
    
    @abstractmethod
    def abstract_method(self):
        pass


@dataclass
class DataClass:
    """データクラス"""
    name: str
    value: int = 0