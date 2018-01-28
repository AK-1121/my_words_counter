**My_words_counter**

Library my_words_counter helps to gather different words statistics in python
projects.

Now available methods to collect information:
1) display most commonly used words in code (verb/nouns)
2) display most often used function names and local variables names

make_stats_report - public method for getting statistics. 
- It could be called via console or directly in code.
- Input data can be taken from local directories or from github repos
(several repos could be processed at once)
- Resulting information can be printed in the console or saved in json or csv files.


Examples of usage:
1) from code:
```
import my_words_counter

my_words_counter.make_stats_report(
    is_local_data=False,
    remote_paths_tuple=(
        'https://github.com/pallets/flask', 
        'https://github.com/AK-1121/my_words_counter'
    ),
    stats_params_collection=(
       ('words_frequency', 'verb', 100),
       ('words_frequency', 'noun', 100),
       ('ast_names_frequency', 'func_names', 10, 'python'),
       ('ast_names_frequency', 'func_local_var_names', 10, 'python'),
    ),
    # is_data_already_in_working_dir=True,
    report_type='json',
    report_file='results.json'
)
```
2) from command line (not working now):
```
python -m my_words_counter --remote_paths_tuple "('https://github.com/pallets/flask',')" --stats_params_collection "(('ast_names_frequency', 'func_names', 10, 'python'),)"

```


Requirements:
- Github console client (git) should be installed on your system if you want to get statistics about git repositories.
 
Remarks:
1) for finding out part of speach for word is used nltk library -  a Python package for natural language processing:
https://pypi.python.org/pypi/nltk  http://www.nltk.org/
Hear you can find a list of all possible tokens for different types of words (used in nltk):
https://stackoverflow.com/a/41150051
2) this library was conctructed in way to be easily extended for:
- getting information from different remote file services;
- working with different code bases not only python;
- collecting different statistical slices;
- creating different forms of reports;

You are free to evolve this library for your own purposes.


