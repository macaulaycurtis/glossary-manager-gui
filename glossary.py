import csv, xlrd, xlwt, xlsxwriter
from collections import OrderedDict
from difflib import SequenceMatcher

class Glossary:

    def __init__(self, filepath, filename, new=False):
        self.filepath = filepath
        self.filename = filename
        self.filetype = filepath[filepath.rfind('.')+1:]
        
        if new == True:
            file = open(self.filepath, 'w', encoding='utf-8')
            file.close()
            
        self.read_from_file()
        self.modified = False

    def read_from_file(self):
        self.content = {}
        self.last_index = 0
        if self.filetype == 'csv':
            with open(self.filepath, 'r', newline='', encoding='utf-8') as file:
                fieldnames = ['source','translation','context']
                reader = csv.DictReader(file, fieldnames=fieldnames)
                for row in reader:
                    self.content.update({self.last_index : row})
                    self.last_index += 1
        elif self.filetype == 'xls' or 'xlsx':
            wb = xlrd.open_workbook(self.filepath)
            sheet = wb.sheet_by_index(0)
            self.sheetname = sheet.name
            for row in range(sheet.nrows):
                try: context = str(sheet.cell(row,2).value)
                except IndexError: context = ''
                self.content.update( {self.last_index : OrderedDict(
                    [('source', str(sheet.cell(row,0).value))
                     , ('translation', str(sheet.cell(row,1).value))
                     , ('context', context)]) } )
                self.last_index += 1

    def search(self, search_results, keyword, column='source', fuzzy=0.0):
        """ Receive keyword as a string and a list of results, and append any hits for that keyword to the results list.
        Args: keyword = string
                results = list"""
        if not fuzzy:
            for row in self.content:
                r = self.content[row]
                if keyword in r[column]:
                    search_results.append({'source' : r['source']
                                    , 'translation' : r['translation']
                                    , 'context': r['context']
                                    , 'glossary' : self.filename
                                    , 'index' : row
                                    , 'ratio' : None})
        if fuzzy:
            for row in self.content:
                r = self.content[row]
                ratio = SequenceMatcher(None, keyword, r[column]).ratio()
                if  ratio > fuzzy:
                    search_results.append({'source' : r['source']
                                    , 'translation' : r['translation']
                                    , 'context': r['context']
                                    , 'glossary' : self.filename
                                    , 'index' : row
                                    , 'ratio' : ratio})

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
        entry = OrderedDict([('source', result['source'])
                         , ('translation', result['translation'])
                         , ('context', result['context'])])
        if entry == self.content[index]:
            return
        else:
            self.content[index] = entry
            self.modified = True

    def save(self):
        """ Write any changes to file. """
        if self.filetype == 'csv': self.save_csv()
        elif self.filetype == 'xls' or 'xlsx': self.save_excel()

    def save_csv(self):
        with open(self.filepath, 'w', newline='', encoding='utf-8') as file:
            fieldnames = ['source','translation','context']
            writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction='ignore')
            writer.writerows(self.content.values())
        self.modified = False

    def save_excel(self):
        if self.filetype == 'xls':
            wb = xlwt.Workbook(encoding='utf-8')
            sheet = wb.add_sheet(self.sheetname)
        else:
            wb = xlsxwriter.Workbook(self.filepath)
            sheet = wb.add_worksheet(self.sheetname)
        for row in self.content:
            sheet.write(row, 0, self.content[row]['source'])
            sheet.write(row, 1, self.content[row]['translation'])
            sheet.write(row, 2, self.content[row]['context'])
        if self.filetype == 'xls': wb.save(self.filepath)
        else: wb.close()
