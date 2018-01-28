import ast
import collections
import logging
import os
import re
import sys

import nltk


# Used logging for debug purposes:
logging.basicConfig(stream=sys.stderr,
                    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
                    level=logging.INFO)


class WordsCounterError(Exception):
    pass


def check_projects(path, projects):
    """
    :param str path:
    :param projects: list or tuple
    :return: list or tuple
    """
    if not projects:
        projects = (x[0] for x in os.walk(path))
    return projects


def _get_py_files_text_from_dir(dir_path, file_names):
    """
    :param str dir_path:
    :param list file_names:
    :return str:
    """
    raw_data = ''
    for file_name in file_names:
        if not file_name.endswith(".py"):
            continue
        file_path = os.path.join(dir_path, file_name)
        with open(file_path, 'r') as f:
            raw_data += f.read()
    return raw_data


def _get_necessary_type_of_words(stats_for_words, type_of_speach):
    results = []
    if type_of_speach == 'verb':
        token = 'VB'
    elif type_of_speach == 'noun':
        token = 'NN'
    else:
        raise WordsCounterError('token for searching words of certain type was not found.')
    for word, frequency in stats_for_words:
        pos_info = nltk.pos_tag([word])
        if pos_info[0][1].startswith(token):
            results.append((word, frequency))
    return results


def _calculate_words_frequency(dir_path: str, params: tuple) -> dict:
    """
    :param dir_path:
    :param tuple params: stats function type - type of speach - top size number.
    Ex.: ('words_frequency', 'noun', 100)
    :return:
    """
    _, word_type, top_size = params
    all_text = ''
    for root, sub_dirs, files in os.walk(dir_path):
        one_dir_text = _get_py_files_text_from_dir(root, files)
        all_text += one_dir_text
    # logging.debug(u"_calculate_words_frequency Part of raw text: {}".format (all_text[:4000]))
    pattern = re.compile("[a-z]+")
    all_words = re.findall(pattern, all_text.lower())
    logging.debug(u"_calculate_words_frequency words (len: {}) {}".format(len(all_words), all_words[:100]))
    stats_for_all_words = collections.Counter(all_words).most_common()
    stats_for_type_of_speach = _get_necessary_type_of_words(stats_for_all_words, word_type)
    logging.debug(u"_calculate_words_frequency unique_words (len: {})".format(len(set(all_words))))
    results = dict()
    report_name = "{}_words_frequency".format(word_type)
    results[report_name] = dict(stats=stats_for_type_of_speach[:top_size],  top_size=top_size,
                                description='Words frequency for all py files')
    return results


def _get_py_file_names(dirname, files):
    """
    :param str dirname: path to dir
    :param list files:
    :return list: list of paths to files
    """
    filenames = []
    for file in files:
        if not file.endswith('.py'):
            continue
        filenames.append(os.path.join(dirname, file))
    return filenames


def _get_tree_from_py_file(py_filename):
    with open(py_filename, 'r', encoding='utf-8') as attempt_handler:
        main_file_content = attempt_handler.read()
        tree = ast.parse(main_file_content)
    return tree


def _get_trees(path):
    """
    :param str path:
    :return list: list of ast-objects
    """
    trees = []
    logging.debug(u"Get_trees - path: {}".format(path))
    for dirname, dirs, files in os.walk(path, topdown=True):
        py_filenames = _get_py_file_names(dirname, files)
        logging.debug('total %s files' % len(py_filenames))
        for py_filename in py_filenames:
            tree = _get_tree_from_py_file(py_filename)
            trees.append(tree)
    logging.debug('trees generated')
    return trees


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
    stats = collections.Counter(public_func_names).most_common(top_size)
    results = dict(
        functions_ast_names_frequency=dict(
            stats=stats, top_size=top_size, description='Functions frequency for all py files counted with ast'
        )
    )
    return results


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
    stats = collections.Counter(names).most_common(top_size)
    results = dict(
        local_variables_ast_names_frequency=dict(
            stats=stats, top_size=top_size, description='Local variables frequency for all py files with ast'
        )
    )
    return results


def _calculate_python_ast_names_frequency(dir_path, entity_type, top_size):
    all_results = dict()
    trees = _get_trees(dir_path)
    if entity_type == 'func_names':
        results = _get_top_functions_names(trees, top_size)
        all_results.update(results)
    elif entity_type == 'func_local_var_names':
        results = _get_top_names(trees, top_size)
        all_results.update(results)
    return all_results


def _calculate_ast_names_frequency(dir_path, params):
    _, ast_entity_type, top_size, code_language = params
    all_results = dict()
    if code_language == 'python':
        results = _calculate_python_ast_names_frequency(dir_path, ast_entity_type, top_size)
        all_results.update(results)
    return all_results


def calculate_statistics(dir_path, stats_params_collection):
    all_results = dict()
    logging.debug(u"calculate_statistics: {} -- {}".format(dir_path, stats_params_collection))
    for stats_params in stats_params_collection:
        if stats_params[0] == 'words_frequency':
            results = _calculate_words_frequency(dir_path, stats_params)
            all_results.update(results)
        elif stats_params[0] == 'ast_names_frequency':
            results = _calculate_ast_names_frequency(dir_path, stats_params)
            all_results.update(results)
    return all_results

