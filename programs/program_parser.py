import os
from typing import List, Tuple

from process import Process


class ProgramParser:

    PROGRAMS_DIR = os.path.dirname(os.path.abspath(__file__))

    MIN_PRIORITY = 1
    MAX_PRIORITY = 5

    SECTION_MARKERS = {
        ".code": ".endcode",
        ".data": ".enddata",
    }

    def __init__(self):
        self._section_parsers = {
            ".code": self._parse_code,
            ".data": self._parse_data,
        }

    def _parse_filename(self, filename: str) -> Tuple[str, int]:
        name, priority_token, *_ = filename.split("-")
        priority = int(priority_token[4:])

        if priority < self.MIN_PRIORITY or priority > self.MAX_PRIORITY:
            raise ValueError(f"Priority out of range in '{filename}': {priority}")

        return name, priority

    def _parse_instruction(self, state: dict, line: str) -> None:
        mnemonic, argument = line.split(maxsplit=1)
        mnemonic, argument = mnemonic.strip().upper(), argument.strip()

        state["instructions"].append((mnemonic, argument))

    def _parse_label(self, state: dict, line: str) -> None:
        label, remainder = line.split(":", 1)
        label, remainder = label.strip(), remainder.strip()

        state["labels"][label] = len(state["instructions"])

        if remainder:
            self._parse_instruction(state, remainder)

    def _parse_code(self, state: dict, line: str) -> None:
        if ":" in line:
            self._parse_label(state, line)
            return
        
        self._parse_instruction(state, line)

    def _parse_data(self, state: dict, line: str) -> None:
        name, value = line.split(maxsplit=1)
        name, value = name.strip(), value.strip()

        state["data_memory"][name] = int(value)

    def _strip_comment(self, line: str) -> str:
        for index, character in enumerate(line):
            if character != "#":
                continue

            operand = line[index + 1:]
            if operand[:1] == "-":
                operand = operand[1:]

            if operand[:1].isdigit() is False:
                return line[:index]

        return line

    def _parse_file(self, path: str, name: str, priority: int) -> Process:
        with open(path) as source_file:
            source = source_file.read()

        state = {"instructions": [], "labels": {}, "data_memory": {}}

        start_marker = None
        for raw_line in source.splitlines():
            line = self._strip_comment(raw_line).strip()

            if line == "":
                continue

            if line[:1] == "#":
                raise ValueError(f"Unexpected '#' at line start: '{line}'")

            if line in self.SECTION_MARKERS:
                if start_marker is not None:
                    raise ValueError(f"Unclosed section marker: '{start_marker}'")
                start_marker = line
                continue

            if line in self.SECTION_MARKERS.values():
                if start_marker is None or line != self.SECTION_MARKERS[start_marker]:
                    raise ValueError(f"Unmatched section marker: '{line}'")
                start_marker = None
                continue

            if start_marker is None:
                raise ValueError(f"Content outside of any section: '{line}'")

            self._section_parsers[start_marker](state, line)

        if start_marker is not None:
            raise ValueError(f"Unclosed section marker: '{start_marker}'")

        return Process(name, priority, state["data_memory"], state["instructions"], state["labels"])

    def parse(self) -> List[Process]:
        processes = []

        for filename in sorted(f for f in os.listdir(self.PROGRAMS_DIR) if f.endswith(".txt")):
            name, priority = self._parse_filename(filename)
            process = self._parse_file(os.path.join(self.PROGRAMS_DIR, filename), name, priority)
            processes.append(process)

        return processes
