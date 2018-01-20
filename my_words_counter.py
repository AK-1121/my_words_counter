import ast
import os
import collections
import logging
import sys

from nltk import download, pos_tag

TOP_SIZE = 200

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
ch = logging.StreamHandler(sys.stdout)
logger.addHandler(ch)


def _flat(_list):
    """ [(1,2), (3,4)] -> [1, 2, 3, 4]"""
    return sum([list(item) for item in _list], [])


def _is_verb(word):
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
    trees = []
    filenames = []
    for dirname, dirs, files in os.walk(path, topdown=True):
        filenames = _get_py_file_names(dirname, files)
    logger.debug('total %s files' % len(filenames))

    for filename in filenames:
        with open(filename, 'r', encoding='utf-8') as attempt_handler:
            main_file_content = attempt_handler.read()
        if with_filenames:
            trees.append(filename)
        data_about_file = _get_file_data(main_file_content, with_file_content)
        trees.extend(data_about_file)
    logger.debug('trees generated')
    return trees


def _get_all_names(tree):
    return [node.id for node in ast.walk(tree) if isinstance(node, ast.Name)]


def _get_verbs_from_function_name(function_name):
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
    logger.debug('functions extracted')
    verbs = _flat([_get_verbs_from_function_name(function_name) for function_name in functions])
    return collections.Counter(verbs).most_common(top_size)


def _get_top_functions_names_in_path(path, top_size=10):
    t = _get_trees(path)
    nms = [f for f in _flat([[node.name.lower() for node in ast.walk(t) if isinstance(node, ast.FunctionDef)] for t in t]) if not (f.startswith('__') and f.endswith('__'))]
    return collections.Counter(nms).most_common(top_size)


def _print_statistics(words, most_common_limit=200):
    logger.info('total number of words: %s; (unique: %s)' % (len(words), len(set(words))))
    logger.info('By words statistic')
    for word, occurence in collections.Counter(words).most_common(most_common_limit):
        # logger.info(word, occurence)
        print(word, occurence)


def set_logging(level, is_using_formatter=False, is_remove_existing_handlers=True,
                log_format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'):
    """
    Set logging parameters manually for library
    :param str level: 'DEBUG', 'INFO', ...
    :param bool is_using_formatter: if True log_format parameter will be used for formatting handler messages
    :param bool is_remove_existing_handlers: if True current handlers for logger will be removed
    :param str log_format: format for logging messages
    :return:
    """
    if is_remove_existing_handlers:
        logger.handlers = []  # remove existing handlers for logging
    handler = logging.StreamHandler(sys.stdout)
    level = logging.getLevelName(level)
    handler.setLevel(level)
    if is_using_formatter:
        formatter = logging.Formatter(log_format)
        handler.setFormatter(formatter)
    logger.addHandler(handler)
    level = logging.getLevelName('INFO')
    logger.setLevel(level)


def check_projects(path, projects):
    if not projects:
        projects = (x[0] for x in os.walk(path))
    return projects


def count_verbs(path='./', projects=tuple(), top_size=TOP_SIZE):
    """
    Count verbs in code for gotten path
    :param str path: system path to directory where counting will be executed.
    :param tuple projects: list of projects (directories) where search will be done
    (by default search in all directories)
    :param int top_size: number of most common verbs that will be printed
    :return:
    """
    try:
        logger.debug(u"Input arguments: path: {}; projects: {}; "
                     u"top_size: {}".format(path, projects, top_size))
        download('averaged_perceptron_tagger')
        words = []
        projects = check_projects(path, projects)
        for project in projects:
            project_path = os.path.join(path, project)
            words += _get_top_verbs_in_path(project_path)
        _print_statistics(words, top_size)
    except Exception as e:
        print(e)
