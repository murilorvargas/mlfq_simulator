import os
from typing import List, Tuple

from process import Process


class ProgramParser:

    PROGRAMS_DIR = os.path.dirname(os.path.abspath(__file__))

    def __init__(self):
        self._section_markers = {
            ".code": self._parse_code,
            ".endcode": None,
            ".data": self._parse_data,
            ".enddata": None,
        }

    def _parse_filename(self, filename: str) -> Tuple[str, int]:
        name, priority_token, *_ = filename.split("-")

        return name, int(priority_token[4:])

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

    def _parse_file(self, path: str, name: str, priority: int) -> Process:
        with open(path) as source_file:
            source = source_file.read()

        state = {"instructions": [], "labels": {}, "data_memory": {}}

        section_parser = None
        for raw_line in source.splitlines():
            line = raw_line.strip()

            if line == "":
                continue

            if line in self._section_markers:
                section_parser = self._section_markers[line]
                continue

            if section_parser is not None:
                section_parser(state, line)

        return Process(name, priority, state["data_memory"], state["instructions"], state["labels"])

    def parse(self) -> List[Process]:
        processes = []

        for filename in sorted(f for f in os.listdir(self.PROGRAMS_DIR) if f.endswith(".txt")):
            name, priority = self._parse_filename(filename)
            process = self._parse_file(os.path.join(self.PROGRAMS_DIR, filename), name, priority)
            processes.append(process)

        return processes
