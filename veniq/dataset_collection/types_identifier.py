import abc
from enum import Enum
from typing import List, Union
import pathlib
import re


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

    def get_spaces_diff(self, line: str) -> int:
        """
        Here we can get num of spaces in the
        line begining.
        """
        # line = line.replace('\t', ' ' * 4)
        diff = len(line) - len(line.lstrip())
        return diff

    def get_spaces_var_decl(self, line: str) -> str:
        """
        Here we can get num of spaces form the original method
        in the line where method invocation inside variable
        declaration.
        """
        if '{' in line:
            space_for_var_decl_line = (self.get_spaces_diff(line) + 4) * ' '
        else:
            space_for_var_decl_line = (self.get_spaces_diff(line)) * ' '
        return space_for_var_decl_line

    def complement_spaces(
            self,
            body_start_line: int,
            invocation_line: int,
            lines: List[str]
    ) -> str:
        """
        In this function we obtain suitable number of spaces
        at the beginning of new inserted lines.
        """
        num_spaces_before = self.get_spaces_diff(lines[invocation_line - 1])
        num_spaces_body = self.get_spaces_diff(lines[body_start_line - 1])
        spaces_in_body = ' ' * (num_spaces_before - num_spaces_body)
        return spaces_in_body

    def get_lines_before_invocation(
            self,
            filename_out: pathlib.Path,
            filename_in: pathlib.Path,
            invocation_line: int
    ) -> List[str]:
        """
        This function is aimed to obtain lines from the original
        file before invocation line, which was detected.
        """
        original_file = open(filename_in, encoding='utf-8')
        lines = list(original_file)
        lines_before_invoсation = lines[:invocation_line - 1]
        return lines_before_invoсation

    def get_lines_after_invocation(
            self,
            filename_out: pathlib.Path,
            filename_in: pathlib.Path,
            invocation_line: int
    ) -> List[str]:
        """
        This function is aimed to obtain lines from the original
        file after invocation line, which was detected.
        Especially, it will be inserted after body of inlined method.
        """
        original_file = open(filename_in, encoding='utf-8')
        lines = list(original_file)
        lines_after_invoсation = lines[invocation_line:]
        return lines_after_invoсation

    @abc.abstractmethod
    def inline_function(
            self,
            filename_in: pathlib.Path,
            invocation_line: int,
            body_start_line: int,
            body_end_line: int,
            filename_out: pathlib.Path
    ) -> Union[None, str]:
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

    def get_lines_of_method_body(
            self,
            filename_out: pathlib.Path,
            filename_in: pathlib.Path,
            invocation_line: int,
            body_start_line: int,
            body_end_line: int
    ) -> List[str]:
        """
        In order to get an appropriate text view, we also need to insert
        lines according to the current number of spaced before the line
        """
        original_file = open(filename_in, encoding='utf-8')
        lines = list(original_file)

        body_lines_without_spaces = lines[body_start_line - 1:body_end_line - 1]
        num_spaces_in_body = self.complement_spaces(body_start_line, invocation_line, lines)
        spaces_in_body = self.complement_spaces(body_start_line, invocation_line, lines)
        body_lines = [spaces_in_body + i for i in body_lines_without_spaces]
        return body_lines

    def inline_function(
            self,
            filename_in: pathlib.Path,
            invocation_line: int,
            body_start_line: int,
            body_end_line: int,
            filename_out: pathlib.Path
    ) -> None:
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

        f_out = open(filename_out, 'w', encoding='utf-8')
        for line in lines_of_final_file:
            f_out.write(line)
        f_out.close()


class InlineWithReturnWithoutArguments(IBaseInlineAlgorithm):

    def __init__(self):
        super().__init__()

    def is_var_declaration(
            self,
            lines: List[str],
            invocation_line: int
    ) -> bool:
        """
        Check the line contains variable declaration
        """
        line_with_declaration = lines[invocation_line - 1].split('=')
        return len(line_with_declaration) > 1

    def is_direct_return(
            self,
            lines: List[str],
            invocation_line: int
    ) -> bool:
        """
        Check the line return method invocation.
        """
        line_with_return = lines[invocation_line - 1].split('return ')
        return len(line_with_return) > 1

    def eluminate_cases_before(
            self,
            line: str
    ) -> str:
        before_case = line.replace('\t', ' ' * 4)
        before_case = re.match("(.*?){", line)  # type: ignore
        if before_case:
            before_case = before_case.group()[:-1]  # type: ignore
            return line
        else:
            before_case_line = line.replace('{', ' ')
            return before_case_line

    def get_lines_of_method_body(
            self,
            filename_out: pathlib.Path,
            filename_in: pathlib.Path,
            invocation_line: int,
            body_start_line: int,
            body_end_line: int
    ) -> List[str]:
        """
        In order to get an appropriate text view, we also need to insert
        lines according to the current number of spaced before the line
        """

        body_lines = []
        original_file = open(filename_in, encoding='utf-8')
        lines = list(original_file)

        # body of the original method, which will be inserted
        body_lines_without_spaces = lines[body_start_line - 1:body_end_line]
        line_with_declaration = lines[invocation_line - 1].split('=')
        var_declaration = self.is_var_declaration(lines, invocation_line)
        is_direct_return = self.is_direct_return(lines, invocation_line)
        spaces_in_body = self.complement_spaces(body_start_line, invocation_line, lines)
        for i, line in enumerate(body_lines_without_spaces):
            return_statement = line.split('return ')
            if i == 0 and len(body_lines_without_spaces) > 1:
                line_after_declaration = self.eluminate_cases_before(line)
                body_lines.append(spaces_in_body + line_after_declaration)
                continue

            if len(return_statement) == 2 and not is_direct_return:
                if var_declaration:
                    variable_declaration = line_with_declaration[0].replace('{', ' ').lstrip()
                    current_line = body_lines_without_spaces[i - 1]
                    space_for_var_decl_line = self.get_spaces_var_decl(current_line)
                    instead_of_return = space_for_var_decl_line + variable_declaration + '= ' + return_statement[1]
                    body_lines.append(spaces_in_body + instead_of_return)
                else:
                    instead_of_return = return_statement[1]
                    tabs_before_return = return_statement[0]
                    body_lines.append(spaces_in_body + tabs_before_return + instead_of_return)
            else:
                body_lines.append(spaces_in_body + line)
        return body_lines

    def inline_function(
            self,
            filename_in: pathlib.Path,
            invocation_line: int,
            body_start_line: int,
            body_end_line: int,
            filename_out: pathlib.Path
    ) -> None:
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
            body_end_line - 1
        )
        lines_of_final_file += body_lines

        # original code after method invocation
        original_code_lines = self.get_lines_after_invocation(
            filename_out,
            filename_in,
            invocation_line
        )
        lines_of_final_file += original_code_lines

        f_out = open(filename_out, 'w', encoding='utf-8')
        for line in lines_of_final_file:
            f_out.write(line)
        f_out.close()
