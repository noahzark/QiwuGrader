import csv
import xlrd
import sys


def compare():
    if len(sys.argv) == 1 or sys.argv[1].find(".csv") == -1:
        print("please provide a csv file!")
        return

    infile = sys.argv[1]

    workbook = xlrd.open_workbook(infile.replace('csv', 'xlsx'))
    worksheet = workbook.sheet_by_name(workbook.sheet_names()[0])

    pass_num = 0
    fail_num = 0

    with open(infile.replace('.csv', '_new.csv'), 'w', newline='', encoding='utf-8') as out:
        writer = csv.writer(out)

        with open(infile, newline='', encoding='utf-8') as csvfile:
            results = csv.reader(csvfile)

            for row in results:
                line = results.line_num
                if line >= worksheet.nrows:
                    break

                standard = worksheet.cell_value(line, 2)
                standard_nlus = standard.split(' ')
                standard_nlus.sort()
                print("standard", standard_nlus)

                nlu = row[-1]
                passed = True
                if nlu.find('{') != -1:
                    print("result", nlu)
                    passed = False
                else:
                    nlus = nlu.split(' ')
                    nlus.sort()
                    print("result", nlus)

                    for standard_nlu in standard_nlus:
                        if standard_nlu not in nlus:
                            passed = False
                            break
                row[6] = passed and "Passed" or "Wrong"
                print(row[6])
                writer.writerow(row)

                if passed:
                    pass_num += 1
                else:
                    fail_num += 1
    print("passed ", pass_num, " failed ", fail_num)


if __name__ == "__main__":
    compare()
