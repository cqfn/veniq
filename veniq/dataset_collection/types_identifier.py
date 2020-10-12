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
        f_out = open(filename_out, 'w')
        original_file = open(filename_in)
        lines = list(original_file)

        # original code before method invocation, which will be substituted
        lines_before_invoсation = lines[:invocation_line - 1]
        for i in lines_before_invoсation:
            f_out.write(i)

        # body of the original method, which will be inserted
        num_spaces_before = len(lines[invocation_line - 1]) - len(lines[invocation_line - 1].lstrip(' '))
        num_spaces_body = len(lines[body_start_line - 1]) - len(lines[body_start_line - 1].lstrip(' '))
        body_lines = lines[body_start_line - 1:body_end_line]
        for i in body_lines:
            f_out.write(' ' * (num_spaces_before - num_spaces_body))
            f_out.write(i)

        # original code after method invocation
        original_code_lines = lines[invocation_line:]
        for i in original_code_lines:
            f_out.write(i)


class InlineWithReturnWithoutArguments(IBaseInlineAlgorithm):

    def __init__(self):
        super().__init__()

    #def _process_var_declaration(self, lines, )

    def inline_function(
            self,
            filename_in: str,
            invocation_line: int,
            body_start_line: int,
            body_end_line: int,
            filename_out: str):
        f_out = open(filename_out, 'w')
        original_file = open(filename_in)
        lines = list(original_file)
        # original code before method invocation, which will be substituted
        lines_before_invoсation = lines[:invocation_line - 1]
        for i in lines_before_invoсation:
            f_out.write(i)

        num_spaces_before = len(lines[invocation_line - 1]) - len(lines[invocation_line - 1].lstrip(' '))
        num_spaces_body = len(lines[body_start_line - 1]) - len(lines[body_start_line - 1].lstrip(' '))
        # body of the original method, which will be inserted
        body_lines = lines[body_start_line - 1:body_end_line]
        line_with_declaration = lines[invocation_line - 1].split('=')
        is_var_declaration = len(line_with_declaration) > 1
        is_direct_return = len(lines[invocation_line - 1].split('return ')) > 1
        for i, line in enumerate(body_lines):
            f_out.write(' ' * (num_spaces_before - num_spaces_body))
            return_statement = line.split('return ')
            if len(return_statement) == 2 and not is_direct_return:
                if is_var_declaration:
                    variable_declaration = line_with_declaration[0].replace('{', ' ').lstrip()
                    if '{' in body_lines[i-1]:
                        space_for_var_decl_line = (len(body_lines[i-1]) - len(body_lines[i-1].lstrip(' ')) + 4) * ' '
                    else:
                        space_for_var_decl_line = (len(body_lines[i-1]) - len(body_lines[i-1].lstrip(' '))) * ' '
                    instead_of_return = space_for_var_decl_line + variable_declaration + '= ' + return_statement[1]
                    f_out.write(instead_of_return)
                else:
                    instead_of_return = return_statement[1]
                    new_tabs = ' ' * len(return_statement[0])
                    f_out.write(new_tabs + instead_of_return)
            else:
                f_out.write(line)

        # original code after method invocation
        original_code_lines = lines[invocation_line:]
        for i in original_code_lines:
            f_out.write(i)
