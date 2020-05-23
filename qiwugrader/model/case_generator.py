import re

import xlrd
import json


class CaseGenerator:

    @staticmethod
    def generate(input_file):
        with open(input_file, encoding='utf-8') as fp:
            input_txt = fp.readlines()

        slot_regex = re.compile(r'<([a-zA-Z_]*)>')
        slots = {}

        if input_txt:
            for l in input_txt:
                ss = slot_regex.findall(l)
                for s in ss:
                    slots[s] = []

        print('读取语义槽完毕：', json.dumps(slots))
        workbook = xlrd.open_workbook(input_file.replace('txt', 'config.xlsx'))
        worksheet = workbook.sheet_by_name(workbook.sheet_names()[0])

        for col in range(0, worksheet.ncols):
            target = worksheet.cell_value(0, col)

            if target not in slots:
                print('没有在txt配置中找到对应的语义槽：', target)
                continue

            for row in range(1, worksheet.nrows):
                v = worksheet.cell_value(row, col)
                if not v:
                    break
                slots[target].append(v)

        for slot in slots:
            if len(slots[slot]) == 0:
                print('语义槽 <' + slot + '> 没有读取到数据')

        import time
        start = time.time()
        sentences = {}

        for l in input_txt:
            def func(temp_s, answer_s=''):
                temp_ss = slot_regex.findall(temp_s)
                if len(temp_ss) == 0:
                    sentences[temp_s] = answer_s.strip()
                else:
                    temp_slot = temp_ss[0]
                    targets = slots[temp_slot]
                    for temp_target in targets:
                        func(temp_s.replace('<' + temp_slot + '>', str(temp_target)),
                             answer_s + ' {}={}'.format(temp_slot, temp_target))

            func(l.strip())

        print('生成了', len(sentences), '条用例')
        print('使用了', time.time() - start, 's')
        start = time.time()

        csv_format = '{},{},{}\n'
        with open(input_file.replace('txt', 'csv'), mode='w', encoding='utf-8') as f:
            f.write(csv_format.format('session', 'ask', 'answer'))

            i = 1
            for sentence in sentences:
                f.write(csv_format.format(i, sentence, sentences[sentence]))

                i += 1

        print('测试用例已保存到', input_file.replace('txt', 'csv'))
        print('保存了', i, '行')
        print('使用了', time.time() - start, 's')
