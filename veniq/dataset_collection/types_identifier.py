import abc
from enum import Enum


class InlineTypesAlgorithms(Enum):
    WITH_RETURN_WITHOUT_ARGUMENTS = 0
    WITHOUT_RETURN_WITHOUT_ARGUMENTS = 1
    DO_NOTHING = -1


class SingletonDecorator:
    def __init__(self, klass):
        self.klass = klass
        self.instance = None

    def __call__(self, *args, **kwds):
        if self.instance is None:
            self.instance = self.klass(*args, **kwds)
        return self.instance


class Singleton(type):
    _instances = {}  # type: ignore

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class AlgorithmFactory(metaclass=Singleton):
    objects = {
        InlineTypesAlgorithms.WITH_RETURN_WITHOUT_ARGUMENTS:
            lambda: InlineWithReturnWithoutArguments,
        InlineTypesAlgorithms.WITHOUT_RETURN_WITHOUT_ARGUMENTS:
            lambda: InlineWithoutReturnWithoutArguments,
        InlineTypesAlgorithms.DO_NOTHING:
            lambda: DoNothing}

    def create_obj(self, val_type):
        return self.objects.get(val_type)()


class IBaseInlineAlgorithm(metaclass=abc.ABCMeta):

    def __init__(self):
        pass

    @abc.abstractmethod
    def inline_function(
            self,
            filename_in: str,
            invocation_line: int,
            body_start_line: int,
            body_end_line: int,
            filename_out: str) -> str:
        raise NotImplementedError("Cannot run abstract function")


class DoNothing(IBaseInlineAlgorithm):
    """
    When we have case when our function inline is too complex,
    we should ignore it and do nothing
    """

    def inline_function(
            self,
            filename_in: str,
            invocation_line: int,
            body_start_line: int,
            body_end_line: int,
            filename_out: str) -> str:
        return ""


class InlineWithoutReturnWithoutArguments(IBaseInlineAlgorithm):

    def __init__(self):
        super().__init__()

    def inline_function(
            self,
            filename_in: str,
            invocation_line: int,
            body_start_line: int,
            body_end_line: int,
            filename_out: str):
        # TODO insert code when it is ready
        print("Run InlineWithoutReturnWithoutArguments")


class InlineWithReturnWithoutArguments(IBaseInlineAlgorithm):

    def __init__(self):
        super().__init__()

    def inline_function(
            self,
            filename_in: str,
            invocation_line: int,
            body_start_line: int,
            body_end_line: int,
            filename_out: str):
        # TODO insert code when it is ready
        print("Run InlineWithReturnWithoutArguments")
