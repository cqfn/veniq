import abc
from enum import Enum
import os
from typing import List
import pathlib

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
            filename_in: pathlib.Path,
            invocation_line: int,
            body_start_line: int,
            body_end_line: int,
            filename_out: pathlib.Path
) -> str:
        raise NotImplementedError("Cannot run abstract function")


class DoNothing(IBaseInlineAlgorithm):
    """
    When we have case when our function inline is too complex,
    we should ignore it and do nothing
    """

    def inline_function(
            self,
            filename_in: pathlib.Path,
            invocation_line: int,
            body_start_line: int,
            body_end_line: int,
            filename_out: pathlib.Path
) -> str:
        return ""


class InlineWithoutReturnWithoutArguments(IBaseInlineAlgorithm):

    def __init__(self):
        super().__init__()

    def get_lines_before_invocation(
            self,
            filename_out: pathlib.Path,
            filename_in: str,
            invocation_line: str
) -> List[str]:
        """
        This function is aimed to obtain lines from the original
        file before invocation line, which was detected.
        """
        original_file = open(filename_in)
        lines = list(original_file)
        lines_before_invoсation = lines[:invocation_line - 1]
        return lines_before_invoсation

    def get_lines_of_method_body(
            self,
            filename_out: pathlib.Path,
            filename_in: pathlib.Path,
            invocation_line: str,
            body_start_line: int,
            body_end_line: int
) -> List[str]:
        """
        In order to get an appropriate text view, we also need to insert
        lines according to the current number of spaced before the line
        """
        original_file = open(filename_in)
        lines = list(original_file)

        num_spaces_before = len(lines[invocation_line - 1]) - len(lines[invocation_line - 1].lstrip(' '))
        num_spaces_body = len(lines[body_start_line - 1]) - len(lines[body_start_line - 1].lstrip(' '))
        body_lines_without_spaces = lines[body_start_line - 1:body_end_line]
        spaces_in_body = ' ' * (num_spaces_before - num_spaces_body)
        body_lines = [spaces_in_body + i for i in body_lines_without_spaces]
        return body_lines

    def get_lines_after_invocation(
            self,
            filename_out: pathlib.Path,
            filename_in: pathlib.Path,
            invocation_line: str
) -> List[str]:
        """
        This function is aimed to obtain lines from the original
        file after invocation line, which was detected.
        Especially, it will be inserted after body of inlined method.
        """
        original_file = open(filename_in)
        lines = list(original_file)
        lines_after_invoсation = lines[invocation_line:]
        return lines_after_invoсation

    def inline_function(
            self,
            filename_in: pathlib.Path,
            invocation_line: int,
            body_start_line: int,
            body_end_line: int,
            filename_out: pathlib.Path
) -> None:
        f_out = open(filename_out, 'w')
        original_file = open(filename_in)
        lines = list(original_file)

        lines_of_final_file = []
        # original code before method invocation, which will be substituted
        lines_before_invoсation = self.get_lines_before_invocation(
                    filename_out,
                    filename_in,
                    invocation_line
                    )
        lines_of_final_file += lines_before_invoсation

        # body of the original method, which will be inserted
        body_lines = self.get_lines_of_method_body(
            filename_out,
            filename_in,
            invocation_line,
            body_start_line,
            body_end_line
        )
        lines_of_final_file += body_lines

        # original code after method invocation
        original_code_lines = self.get_lines_after_invocation(
                    filename_out,
                    filename_in,
                    invocation_line
                    )
        lines_of_final_file += original_code_lines

        for line in lines_of_final_file:
            f_out.write(line)

        f_out.close()
        original_file.close()


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
<<<<<<< HEAD
        lines = list(original_file)
=======
        lines = original_file.readlines()

>>>>>>> origin
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

        f_out.close()
        original_file.close()
