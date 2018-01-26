import os, threading
from glossary import Glossary

class GlossaryManager:

    def __init__(self, path):
        self.glossaries = {}
        self.load_all(path)

    def load_all(self, path):
        """Attempt to load all files in the directory (str)"""
        self.glossary_dir = path
        try:
            filenames = (os.listdir(self.glossary_dir))
            for filename in filenames:
               filepath = self.glossary_dir + '/' + filename
               if os.path.isfile(filepath):
                   t = threading.Thread(target=self.add_glossary, args=(filepath, filename))
                   t.start()
                   t.join()
        except FileNotFoundError:
            pass

    def add_glossary(self, filepath, filename, new=False):
        """ Add a glossary to the glossaries dict.
        ARGS: filepath (string), short_name (string) """
        self.glossaries.update({filename : Glossary(filepath, filename, new)})

    def new_glossary(self, filepath, filename):
        """ Add a new empty glossary to the glossaries dict.
        ARGS: filename (str) """
        try:
            if not filename in os.listdir(self.glossary_dir):
                self.add_glossary(filepath, filename, new=True)
        except FileNotFoundError:
            self.add_glossary(filepath, filename, new=True)

    def list_glossaries(self):
        """ List all the currently loaded glossaries by short name """
        glossary_list = list(self.glossaries.keys())
        for g in glossary_list:
            g.replace('\'', '')
        return glossary_list
   
    def search(self, keyword, fuzzy=0, column='source'):
        """ Searches all glossaries for a keyword. ARGS: keyword (string) """
        search_results = []
        for glossary in self.glossaries:
            t = threading.Thread(
                target=self.glossaries[glossary].search
                , args=(search_results, keyword, column, fuzzy)
                )
            t.start()
            t.join()
        if fuzzy:
            search_results.sort(key = lambda s: s['ratio'], reverse=True)
        else:
            search_results.sort(key = lambda s: len(s['source']))
        return search_results

    def display_contents(self, glossary):
        return self.glossaries[glossary].display()

    def unsaved_changes(self):
        for g in self.glossaries:
            if self.glossaries[g].modified: return True
        return False
        
    def delete(self, result):
        """Delete an entry from a Glossary.
        ARGS: short_name (string), index (from search results; int) """
        self.glossaries[result['glossary']].delete(result['index'])
        
    def replace_entry(self, result):
        """Replace an entry in a Glossary.
        ARGS: new entry (OrderedDict), short_glossary (string), index (from search results; int) """
        self.glossaries[result['glossary']].modify(result['index'], result)

    def add_entry(self, entry, glossary):
        """Add an entry to the active Glossary.
        ARGS: new entry (OrderedDict) """
        self.glossaries[glossary].add(entry)

    def save(self, glossary=False):
        """ Save a Glossary (or all) and return a list of saved glossaries.
        ARGS: short name (string)
        RETURNS: saved glossaries (list) """
        saved_glossaries = []
        if not glossary:
            for g in self.glossaries:
                if self.glossaries[g].modified:
                    self.glossaries[g].save()
                    saved_glossaries.append(self.glossaries[g].filename)
            return str(saved_glossaries).strip('[]').replace('\'', '')
        elif self.glossaries[glossary].modified:
            self.glossaries[glossary].save()
            return glossary
