import ast
import os
import collections
import logging
import sys

from nltk import download, pos_tag

TOP_SIZE = 10
# Used logging for debug purposes:
logging.basicConfig(stream=sys.stderr,
                    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
                    level=logging.INFO)


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
    """
    :param str path:
    :param bool with_filenames:
    :param bool with_file_content:
    :return list: list of ast-objects
    """
    trees = []
    logging.debug(u"Get_trees - path: {}".format(path))
    for dirname, dirs, files in os.walk(path, topdown=True):
        logging.debug(u'path parts: {} - {} -- {}'.format(dirname, dirs, files))
        filenames = _get_py_file_names(dirname, files)
        logging.debug('total %s files' % len(filenames))
        batch_results = _parse_batch_of_filenames(filenames, with_filenames, with_file_content)
        trees.extend(batch_results)
    logging.debug('trees generated')
    return trees


def _parse_batch_of_filenames(filenames, with_filenames, with_file_content):
    """
    :param list filenames: list of paths
    :param bool with_filenames: flag to take file names for search
    :param bool with_file_content: flag to take file content for search
    :return list: list of strings
    """
    batch_results = []
    for filename in filenames:
        with open(filename, 'r', encoding='utf-8') as attempt_handler:
            main_file_content = attempt_handler.read()
        if with_filenames:
            batch_results.append(filename)
        data_about_file = _get_file_data(main_file_content, with_file_content)
        batch_results.extend(data_about_file)
    return batch_results


def _get_top_names(trees, top_size=10):
    """
    :param list trees: list of ast-tree objects
    :param int top_size:
    :return list: list of tuples
    """
    names = []
    for tree in trees:
        nms_batch = [node.id for node in ast.walk(tree) if isinstance(node, ast.Name)]
        names.extend(nms_batch)
    return collections.Counter(names).most_common(top_size)


def _get_verbs_from_function_name(function_name):
    return [word for word in function_name.split('_') if _is_verb(word)]


def _parse_function_names(trees):
    """
    :param list trees: list of ast objects
    :return list: list of str (function names)
    """
    results = []
    for t in trees:
        results += [node.name.lower() for node in ast.walk(t) if isinstance(node, ast.FunctionDef)]
    functions = [f for f in results if not (f.startswith('__') and f.endswith('__'))]
    return functions


def _get_top_verbs_in_path(trees, top_size=10):
    """
    :param list trees: list of ast-trees
    :param int top_size:
    :return list: list of tuples
    """
    functions = _parse_function_names(trees)
    verbs = _flat([_get_verbs_from_function_name(function_name) for function_name in functions])
    return collections.Counter(verbs).most_common(top_size)


def _get_top_functions_names(trees, top_size=10):
    """
    :param list trees: list of ast-tree objects
    :param int top_size:
    :return list: list of tuples
    """
    func_names = []
    for tree in trees:
        func_nms_batch = [node.name.lower() for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        func_names.extend(func_nms_batch)
    public_func_names = [f for f in func_names if not (f.startswith('__') and f.endswith('__'))]
    return collections.Counter(public_func_names).most_common(top_size)


def _print_statistics(words, entity_name='entity'):
    """
    :param list words: list of tuples. Ex.: [('get', 53), ('make', 30), ('find', 3), ('add', 2), ...]
    :param entity_name:
    :return:
    """
    print('\ntotal number of words: %s; (unique: %s)' % (len(words), len(set(words))))
    print('By {} statistic'.format(entity_name))
    for word in words:
        print(u"{}: {}".format(word[0], word[1]))


def check_projects(path, projects):
    """
    :param str path:
    :param projects: list or tuple
    :return: list or tuple
    """
    if not projects:
        projects = (x[0] for x in os.walk(path))
    return projects


def calculate_statistics(path='./', projects=tuple(), top_size=TOP_SIZE, with_filename=False,
                         with_file_content=False):
    """
    Count verbs in code for gotten path
    :param str path: system path to directory where counting will be executed.
    :param tuple projects: list of projects (directories) where search will be done
    (by default search in all directories)
    :param bool with_filename: if True - get stats also about file names
    :param bool with_file_content: if True - get stats also about file contents
    :param int top_size: number of most common verbs that will be printed
    :return:
    """
    try:
        logging.debug(u"Input arguments: path: {}; projects: {}; "
                      u"top_size: {}".format(path, projects, top_size))
        download('averaged_perceptron_tagger')
        names = []
        verbs = []
        function_names = []
        projects = check_projects(path, projects)
        for project in projects:
            project_path = os.path.join(path, project)
            trees = _get_trees(project_path)
            names += _get_top_names(trees, top_size=top_size)
            verbs += _get_top_verbs_in_path(trees, top_size=top_size)
            function_names += _get_top_functions_names(trees, top_size=top_size)
        _print_statistics(names, entity_name='names')
        _print_statistics(verbs, entity_name='verbs')
        _print_statistics(function_names, entity_name='functions')
    except Exception as e:
        print(e)
        raise e
