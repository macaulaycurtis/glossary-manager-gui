import csv, xlrd, xlwt, xlsxwriter
from collections import OrderedDict
from difflib import SequenceMatcher

class Glossary:

    def __init__(self, filepath, mode, new_path=None):
        if mode == 'new':
            file = filepath.open('w', encoding='utf-8')
            file.close()
        self.filepath = filepath
        self.filetype = filepath.suffix
        self.filename = filepath.name
        self.read_from_file()
        if mode == 'open':
            self.filepath = new_path
            self.filetype = new_path.suffix
            self.filename = new_path.name
            self.save()
        self.modified = False

    def read_from_file(self):
        self.content = {}
        self.last_index = 0
        if self.filetype == '.csv':
            with self.filepath.open('r', newline='', encoding='utf-8-sig') as file:
                fieldnames = ['source','translation','context']
                reader = csv.DictReader(file, fieldnames=fieldnames)
                for row in reader:
                    self.content.update({self.last_index : row})
                    self.last_index += 1
        elif self.filetype == '.xls' or self.filetype == '.xlsx':
            wb = xlrd.open_workbook(self.filepath)
            sheet = wb.sheet_by_index(0)
            self.sheetname = sheet.name
            for row in range(sheet.nrows):
                columns = OrderedDict([('source', ''), ('translation', ''), ('context', '')])
                for i, c in enumerate(columns):
                    try:
                        columns[c] = str(sheet.cell(row, i).value)
                    except IndexError:
                        columns[c] = ''
                self.content.update({self.last_index : columns})
                self.last_index += 1
        else:
            raise FileNotFoundError

    def search(self, search_results, keyword, column='source', minimum_match=0.0):
        """ Receive keyword as a string and a list of results, and append any hits for that keyword to the results list.
        Args: keyword = string
                results = list"""
        keyword = keyword.casefold()
        if minimum_match == 0.0:
            for row in self.content:
                r = self.content[row]
                if keyword in r[column].casefold():
                    search_results.append({
                        'source' : r['source']
                        , 'translation' : r['translation']
                        , 'context': r['context']
                        , 'glossary' : self.filename
                        , 'index' : row
                        , 'ratio' : None
                        })
        else:
            for row in self.content:
                r = self.content[row]
                ratio = SequenceMatcher(None, keyword, r[column].casefold()).ratio()
                if  ratio >= minimum_match:
                    search_results.append({
                        'source' : r['source']
                        , 'translation' : r['translation']
                        , 'context': r['context']
                        , 'glossary' : self.filename
                        , 'index' : row
                        , 'ratio' : ratio
                        })

    def display(self):
        display_results = []
        for row in self.content:
            r = self.content[row]
            display_results.append({
                'source' : r['source']
                , 'translation' : r['translation']
                , 'context': r['context']
                , 'glossary' : self.filename
                , 'index' : row
                , 'ratio' : None
                })
        return display_results

    def add(self, entry):
        """ Receive an entry as an ordered dict and append it to self.content. """
        self.content.update({self.last_index : entry})
        self.last_index += 1
        self.modified = True

    def delete(self, index):
        """ Receive the index of an entry and pop it out of self.content. """
        self.content.pop(index)
        self.modified = True

    def modify(self, index, result):
        """ Receive the index and an amended entry and replace it in self.content. """
        entry = OrderedDict([
            ('source', result['source'])
            , ('translation', result['translation'])
            , ('context', result['context'])
            ])
        if entry == self.content[index]:
            return
        else:
            self.content[index] = entry
            self.modified = True

    def save(self):
        """ Write any changes to file. """
        if self.filetype == '.csv':
            self.save_csv()
        elif self.filetype == '.xls' or '.xlsx':
            self.save_excel()

    def save_csv(self):
        with self.filepath.open('w', newline='', encoding='utf-8') as file:
            fieldnames = ['source','translation','context']
            writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction='ignore')
            writer.writerows(self.content.values())
        self.modified = False

    def save_excel(self):
        if self.filetype == '.xls':
            wb = xlwt.Workbook(encoding='utf-8')
            sheet = wb.add_sheet(self.sheetname)
        else:
            wb = xlsxwriter.Workbook(self.filepath.as_posix())
            sheet = wb.add_worksheet(self.sheetname)
        for row in self.content:
            sheet.write(row, 0, self.content[row]['source'])
            sheet.write(row, 1, self.content[row]['translation'])
            sheet.write(row, 2, self.content[row]['context'])
        if self.filetype == '.xls':
            wb.save(self.filepath.as_posix())
        else:
            wb.close()
