Library my_words_counter helps to count frequency of English words in code.

In library is used nltk -  a Python package for natural language processing:
https://pypi.python.org/pypi/nltk
http://www.nltk.org/

Public methods now available:
1. count_verbs(path, projects, top_size) - count verbs in project.
Method determines that a word is a verb with the help of nltk averaged perceptron tagger.
In case of not existing path you will get error.

2. set_logging(level, is_using_formatter, is_remove_existing_handlers, log_format) 
- set logging parameters manually. This method could be called before main counting methods
