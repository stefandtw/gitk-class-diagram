#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess
import sys
import unittest
from unittest import TestCase
from unittest.mock import patch
from classdiff import main


class TestGvFiles(TestCase):

    def test_iterate(self):
        cases = 0
        for exp_gv in os.listdir("tests"):
            if not exp_gv.endswith(".expected.gv"):
                continue
            base = "tests/" + exp_gv.replace(".expected.gv", "")
            a = base + ".a.tags"
            b = base + ".b.tags"
            ranges = base + ".ranges"
            expected = base + ".expected.gv"
            actual = base + ".actual.gv"
            with self.subTest(msg=exp_gv):
                with patch.object(sys, "argv", ["classdiff", "-r", ranges,
                                                "-o", actual, a, b]):
                    main.main()
                with open(actual, "r") as f:
                    act_content = f.read().strip()
                with open(expected, "r") as f:
                    exp_content = f.read().strip()
                diffcmd = f"diff -u {actual} {expected} | head -n 15"
                diffresult = subprocess.run(diffcmd, check=False, text=True,
                                            stdout=subprocess.PIPE, shell=True)
                msg = diffcmd + "\n" + diffresult.stdout
                self.assertTrue(act_content == exp_content, msg)
            cases += 1
        self.assertGreater(cases, 0)


if __name__ == "__main__":
    unittest.main()
