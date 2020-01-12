
import os
import re
from classdiff.tag_model import LineRange


class DiffRangeFactory:
    def fromfile(self, path, model):
        if not path or not os.path.isfile(path):
            return
        with open(path) as rangesfile:
            fname = ""
            for linecmp in rangesfile:
                line = linecmp.rstrip()
                if line.startswith("+++ "):
                    fname = line.split()[-1]
                elif fname and fname in model:
                    self._match(line, model[fname])

    def _match(self, line, file):
        match = re.search(r"^@@@?( \S+){1,2} \+(\d+)(,(\d+))? @@@?", line)
        if match:
            start = int(match[2])
            count = int(match[4]) if match[3] else 1
            r = LineRange(start, start + count - 1)
            file.add_diff_range(r)
