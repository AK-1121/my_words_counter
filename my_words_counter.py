# Task from here:
# https://gist.github.com/Melevir/5754a1b553eb11839238e43734d0eb79


import ast
import os
import collections
import logging

from nltk import download, pos_tag

PATH = '/Users/install/projects/project01/'
# PATH = '/Users/install/venvs'
TOP_SIZE = 200

PROJECTS_NAMES = [
    'django',
    'flask',
    'pyramid',
    'reddit',
    'requests',
    'sqlalchemy',
    'ETL',
    'external_api',
    'external-api'
]


def _flat(_list):
    """ [(1,2), (3,4)] -> [1, 2, 3, 4]"""
    return sum([list(item) for item in _list], [])


def _is_verb(word):
    print(u"XX35: {}".format(word))
    if not word:
        return False
    pos_info = pos_tag([word])
    return pos_info[0][1] == 'VB'


def _get_py_file_names(dirname, files, max_number_of_py_files=100):
    """
    :param str dirname: path to dir
    :param list files: list file names
    :param max_number_of_py_files:
    :return list: list of paths to files
    """
    filenames = []
    for file in files:
        if not file.endswith('.py'):
            continue
        filenames.append(os.path.join(dirname, file))
        if len(filenames) == max_number_of_py_files:
            break
    return filenames


def _get_file_data(main_file_content, with_file_content=False):
    data_about_file = []
    if with_file_content:
        data_about_file.append(main_file_content)
    try:
        tree = ast.parse(main_file_content)
        data_about_file.append(tree)
    except SyntaxError as e:
        print(e)
    return data_about_file


def _get_trees(path, with_filenames=False, with_file_content=False):
    print(u"XX01: {}".format(path))
    trees = []
    filenames = []
    for dirname, dirs, files in os.walk(path, topdown=True):
        if dirs:
            print(u"XX74: {} - {} -- {}".format(dirname, dirs, files))
        filenames = _get_py_file_names(dirname, files)
    print('total %s files' % len(filenames))

    for filename in filenames:
        print(u"XX92: {}".format(filename))
        with open(filename, 'r', encoding='utf-8') as attempt_handler:
            main_file_content = attempt_handler.read()
        if with_filenames:
            trees.append(filename)
        data_about_file = _get_file_data(main_file_content, with_file_content)
        trees.extend(data_about_file)
    print('trees generated')
    return trees


def _get_all_names(tree):
    return [node.id for node in ast.walk(tree) if isinstance(node, ast.Name)]


def _get_verbs_from_function_name(function_name):
    print(u"XX81: {}".format(function_name))
    return [word for word in function_name.split('_') if _is_verb(word)]


def _split_snake_case_name_to_words(name):
    return [n for n in name.split('_') if n]


def _get_all_words_in_path(path):
    trees = [t for t in _get_trees(path) if t]
    function_names = [f for f in _flat([_get_all_names(t) for t in trees]) if not (f.startswith('__') and f.endswith('__'))]
    return _flat([_split_snake_case_name_to_words(function_name) for function_name in function_names])


def _parse_function_names(trees):
    results = []
    for t in trees:
        results += [node.name.lower() for node in ast.walk(t) if isinstance(node, ast.FunctionDef)]
    print(u"XX35: {}".format(results))
    functions = [f for f in results if not (f.startswith('__') and f.endswith('__'))]
    return functions


def _get_top_verbs_in_path(path, top_size=10):
    """
    :param str path:
    :param int top_size:
    :return:
    """
    trees = [t for t in _get_trees(path) if t]
    functions = _parse_function_names(trees)
    print('functions extracted')
    verbs = _flat([_get_verbs_from_function_name(function_name) for function_name in functions])
    return collections.Counter(verbs).most_common(top_size)


def _get_top_functions_names_in_path(path, top_size=10):
    t = _get_trees(path)
    nms = [f for f in _flat([[node.name.lower() for node in ast.walk(t) if isinstance(node, ast.FunctionDef)] for t in t]) if not (f.startswith('__') and f.endswith('__'))]
    return collections.Counter(nms).most_common(top_size)


def _print_statistics(words, most_common_limit=200):
    print('total number of words: %s; (unique: %s)' % (len(words), len(set(words))))
    print('By words statistic')
    for word, occurence in collections.Counter(words).most_common(most_common_limit):
        print(word, occurence)


def main(path, projects, top_size):
    download('averaged_perceptron_tagger')
    words = []
    for project in projects:
        project_path = os.path.join(path, project)
        print(u"XX02: {}".format(project_path))
        words += _get_top_verbs_in_path(project_path)
    _print_statistics(words, top_size)


if __name__ == '__main__':
    main(PATH, PROJECTS_NAMES, TOP_SIZE)
