import ast
import collections
import csv
import logging
import os
import shutil
import sys
import time
import ujson

from nltk import download

from stats_logic import calculate_statistics

# Used logging for debug purposes:
logging.basicConfig(stream=sys.stderr,
                    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
                    level=logging.INFO)


class WordsCounterError(Exception):
    pass


def _flat(_list):
    """ [(1,2), (3,4)] -> [1, 2, 3, 4]"""
    return sum([list(item) for item in _list], [])


def _parse_function_names(trees):
    """
    :param list trees: list of ast objects
    :return list: list of str (function names)
    """
    results = []
    for tree in trees:
        results += [node.name.lower() for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
    functions = [f for f in results if not (f.startswith('__') and f.endswith('__'))]
    return functions


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


def _get_git_data(data_dir, git_path, extra_params=''):
    """
    :param str data_dir:
    :param str git_path:
    :param str extra_params:
    :return:
    """
    command = "git clone {} {}".format(git_path, data_dir)
    logging.debug(u"Git command: {}".format(command))
    os.system(command)


def _get_remote_data_for_analyze(working_dir, remote_resource_type,
                                 remote_paths_tuple=tuple(), extra_params=''):
    """
    :param str working_dir:
    :param str remote_resource_type:
    :param tuple remote_paths_tuple:
    :param str extra_params:
    :return:
    """
    if remote_resource_type == 'git':
        for remote_path in remote_paths_tuple:
            subdir = os.path.join(working_dir, str(int(time.time())))
            _get_git_data(subdir, remote_path, extra_params)


def _print_to_console(data):
    for key in data.keys():
        print("\n\nReport: {} (top size: {})\ndescription: {}".format(
            key, data[key].get('top_size', ''), data[key]['description'])
        )
        for element in data[key]['stats']:
            print(u"{} - {}".format(element[0], element[1]))


def _save_results_to_json(data, report_file):
    with open(report_file, 'w') as f:
        f.write(ujson.dumps(data))


def _save_csv_file(data, report_file):
    with open(report_file, 'w') as f:
        writer = csv.writer(f)
        for row in data:
            writer.writerow(row)
        writer.writerow(['word', 'frequency'])


def _save_results_to_csv(data, base_report_file):
    for report in data.keys():
        report_file = base_report_file.replace(".csv", "_{}.csv".format(report))
        _save_csv_file(data[report]['stats'], report_file)
        print(u"CSV file was saved: {}".format(report_file))


def _create_report(data, report_type, report_file):
    if report_file and not os.path.isabs(report_file):
        os.path.join(os.path.dirname(os.path.realpath(__file__)), report_file)
    if report_type == 'cli':
        _print_to_console(data)
    elif report_type == 'json':
        _save_results_to_json(data, report_file)
    elif report_type == 'csv':
        _save_results_to_csv(data, report_file)
    else:
        raise WordsCounterError("Was not able to write data with method: {}".format(report_type))


def _make_dirs_to_process(data_dir, projects):
    processing_dirs = []
    if not projects:
        projects = (x[0] for x in os.walk(data_dir))
    for project in projects:
        processing_dirs.append(os.path.join(data_dir, project))
    return processing_dirs


def _prepare_input_local_data(data_dir: str, projects: tuple, working_dir: str):
    if not data_dir:
        raise WordsCounterError('Cannot find data_dir for local data')
    if not os.path.isabs(data_dir):
        data_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), data_dir)
    if projects:
        for project in projects:
            prj_old_path = os.path.join(data_dir, project)
            prj_new_path = os.path.join(working_dir, project)
            shutil.copytree(prj_old_path, prj_new_path)
    else:
        shutil.copytree(data_dir, working_dir)


def _prepare_input_data(data_dir: str, projects: tuple, working_dir: str, is_local_data: bool,
                        remote_resource_type: str, remote_paths_tuple: tuple,
                        is_data_already_in_working_dir: bool,
                        extra_remote_resourse_params: str) -> str:
    if not os.path.isabs(working_dir):
        working_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), working_dir)

    if is_data_already_in_working_dir:
        return working_dir

    shutil.rmtree(working_dir)
    if is_local_data:
        _prepare_input_local_data(data_dir, projects, working_dir)
    else:
        _get_remote_data_for_analyze(
            working_dir, remote_resource_type, remote_paths_tuple, extra_remote_resourse_params
        )
    return working_dir


def make_stats_report(data_dir='', projects=tuple(), working_dir='input_data', is_local_data=True,
                      remote_paths_tuple=tuple(), remote_resource_type='git',
                      is_data_already_in_working_dir=False, extra_remote_resourse_params=None,
                      stats_params_collection=(
                              ('words_frequency', 'verb', 100),
                              ('words_frequency', 'noun', 100),
                              ('ast_names_frequency', 'func_names', 10, 'python'),
                              ('ast_names_frequency', 'func_local_var_names', 10, 'python')
                      ),
                      report_type='cli', report_file=None):
    # download('punkt')
    download('averaged_perceptron_tagger')
    working_dir = _prepare_input_data(
        data_dir=data_dir, projects=projects, working_dir=working_dir,
        is_local_data=is_local_data, remote_resource_type=remote_resource_type,
        remote_paths_tuple=remote_paths_tuple,
        is_data_already_in_working_dir=is_data_already_in_working_dir,
        extra_remote_resourse_params=extra_remote_resourse_params
    )
    results = calculate_statistics(
        dir_path=working_dir, stats_params_collection=stats_params_collection
    )
    _create_report(results, report_type=report_type, report_file=report_file)




