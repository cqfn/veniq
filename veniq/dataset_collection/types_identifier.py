import abc


class SingletonDecorator:
    def __init__(self, klass):
        self.klass = klass
        self.instance = None

    def __call__(self, *args, **kwds):
        if self.instance is None:
            self.instance = self.klass(*args, **kwds)
        return self.instance


class AlgorithmFactory:
    objects = {1: lambda: InlineWithoutReturnWithoutArguments,
               0: lambda: InlineWithoutReturnWithoutArguments,
               -1: lambda: DoNothing}

    def create_obj(self, val_type):
        return self.objects.get(val_type)()


class IBaseInlineAlgorithm(metaclass=abc.ABCMeta):

    def __init__(self):
        pass

    @abc.abstractmethod
    def inline_function(
            self,
            filename_in: str,
            line: int,
            src_line_inline: int,
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
            line: int,
            src_line_inline: int,
            filename_out: str) -> str:
        return ""


class InlineWithoutReturnWithoutArguments(IBaseInlineAlgorithm):

    def __init__(self):
        super().__init__()

    def inline_function(
            self,
            filename_in: str,
            line: int,
            src_line_inline: int,
            filename_out: str):
        # TODO insert code when it is ready
        print("Run InlineWithoutReturnWithoutArguments")


class InlineWithReturnWithoutArguments(IBaseInlineAlgorithm):

    def __init__(self):
        super().__init__()

    def inline_function(
            self,
            filename_in: str,
            line: int,
            src_line_inline: int,
            filename_out: str):
        # TODO insert code when it is ready
        print("Run InlineWithReturnWithoutArguments")
