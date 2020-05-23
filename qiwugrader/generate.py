import sys
from qiwugrader.model.case_generator import CaseGenerator


def generate():
    if len(sys.argv) == 1 or sys.argv[1].find(".txt") == -1:
        print("please provide a txt file!")
    else:
        input_file = sys.argv[1]
        CaseGenerator.generate(input_file)
