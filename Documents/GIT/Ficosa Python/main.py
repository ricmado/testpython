from lib.doors import Client as Doors

import lib.db_interface as db_interface
import lib.glob as glob
import lib.synect as synect
import lib.jira_class as jira_class
from lib.data_processing import ConfigFile
import os

#Ric: Parameters for main
import sys


class Interface(object):
    """
    Class to manage the server automatically, involving different platforms such as DOORS, SYNECT or METABASE
    """

    def __init__(self, config_path='config.ini', projects_list=[]):

        # Config parameters
        glob.config = ConfigFile(config_path)

        # Project settings
        glob.projects = {}
        self.load_project_configs(projects_list)

        # Data structure
        self.load_data_structure()

        self.db = None
        self.doors = None
        self.synect =None

        # self.init_database()
        # self.init_doors()
        # self.init_synect()

    def init_database(self):

        # Database initialization
        self.db = db_interface.Database(glob.config['database_connector'], glob.config['database_config'])

    def init_doors(self):
        # DOORS handler to manage DOORS from DXL Server.
        self.doors = Doors(glob.config['doors'])
        self.doors.stop_doors_server()
        self.doors.start_doors_server()

    def deinit_doors(self):
        self.doors.stop_doors_server()

    def init_synect(self):
        # SYNECT handler to manage synect from API and SQL db.
        self.synect = synect.SynectClient()

    @staticmethod
    def load_project_configs(projects_list):

        # Append projects to current project settings
        project_dir = glob.config['projects']['directory']

        for file_name in os.listdir(project_dir):

            print file_name

            # Append project settings dictionary to project list
            if '.proj' in file_name and file_name.replace('.proj', '') in projects_list:
                proj_file = open(project_dir + '/' + file_name, 'r')
                proj_data = eval(proj_file.read())
                proj_file.close()

                glob.projects[file_name.replace('.proj', '')] = proj_data

    @staticmethod
    def load_data_structure():
        glob.data_structure = eval(open(glob.config['common']['data_structure_path'], 'r').read())

    def reset_database(self):
        self.db.remove_database(glob.config['database_config']['database'])
        self.db.create_database(glob.config['database_config']['database'])
        self.db.init_database()

    @staticmethod
    def get_baselines_to_sync(baseline, module_baselines):

        baselines_to_sync = []
        module_baselines.sort()

        if baseline.lower() == 'last':
            baselines_to_sync.append(module_baselines[-1])

        else:
            module_baselines.append('current')

            for module_baseline in module_baselines:
                if baseline.lower() in module_baseline.lower() or baseline.lower() == 'all':
                    baselines_to_sync.append(module_baseline)

        return baselines_to_sync

    def get_hours_jira(self):
        s_user = glob.config['jira']['user']
        s_pwd = glob.config['jira']['pwd']
        auth_jira = jira_class.JiraClass(s_user, s_pwd)

        s_jql = '(project = "Test and Validation VW" OR project = "ADAEX VW eX 2019" OR project = "TVAUCMS") AND worklogAuthor in (FV4ALC0, FV4JVO0, FV4JGC0, FV4JAT0, FV4AML0, FV4DJG0, "rodrigo.delacal@idneo.com", FV4JSC0, FV4RMC0, FV4MBP0, FV4CMA0, FV4JRA0, FV4JHR1, FV4CL00, FN5JMA0) '

        if auth_jira is not None:
            # dict of issue:[(worklog1), (worklog2), ...]
            d_issues = auth_jira.get_issues(s_jql, issue_fields="worklog")

            for s_issue, d_values in d_issues.items():
                l_worklogs = d_values["worklog"]
                for t_worklog in l_worklogs:
                    s_id, s_author, i_time_spend_seconds, s_start_date = t_worklog
                    i_time_spend_seconds = int(i_time_spend_seconds)
                    query = "REPLACE INTO external_data.jira_worklogs (`id`, `issue_key`, `author`, `started`, `timeSpentSeconds`) VALUES ('{}', '{}', '{}', '{}', {})".format(s_id, s_issue, s_author, s_start_date, i_time_spend_seconds)
                    self.db.execute_queries(query)

            self.db.commit()

            print "Worklogs imported from JIRA".format()

    def sync_project_requirements(self, project_config, baseline):
        """
        Synchorinze all requirements belonging to a project and a baseline passed. 
        :param project_config: dictionary with all needed config scrutrure.
        :return: 
        """

        columns = project_config['doors_column_map'].keys()

        # For each folder with relevant requirements to the project
        for root_folder in project_config['root_folders']:
            modules = self.doors.get_modules_from_folder(root_folder)

            # For each module in folder
            for module_id in modules.keys():

                if 'deprecated' not in modules[module_id].lower():
                    print modules[module_id]
                    # Module baselines
                    module_baselines = self.doors.get_baselines_from_module(module_id)

                    baselines_to_sync = self.get_baselines_to_sync(baseline, module_baselines)

                    for baseline_to_sync in baselines_to_sync:
                        content = self.doors.get_content_from_module_id(module_id, columns, baseline_to_sync)
                        self.db.add_requirements(modules[module_id], project_config['project_name'], columns, content)

    def sync_all(self, baseline):

        for project in glob.projects.keys():
            # For each project config stored glob.projects syncrhonize all current data from doors to mySQL.
            self.sync_project_requirements(glob.projects[project], baseline)


if __name__ == '__main__':

    projects_list = []

    # projects_list.append('ADAEX_Repository')
    # projects_list.append('091_ADAEX_V5_EC')
    # projects_list.append('091_ADAEX_V9_ECU')
    # projects_list.append('091_ADAEX_V5_ESR')
    # projects_list.append('091_ADAEX_V5_ETV')
    # projects_list.append('092_BEVQ6_V7')

    i = Interface(projects_list=projects_list)

    i.init_database()
    # i.init_doors()
    # i.deinit_doors()
    # i.init_synect()
    # i.sync_all('all')

    # i.get_hours_jira()
	
	#Ric: Parameters for main
    i.db.import_test_cases_directory(sys.argv[1])

	# i.db.import_test_cases_directory(r"D:\04_Test_Cases\092_BEVQ6_V7")
    # i.db.import_test_cases_directory(r"D:\04_Test_Cases\ADAEX")

    # i.reset_database()

    # i.db.test_sql()
    # i.sync_project_requirements('092_BEVQ6_V7')
    # i.synect.generate_ecxml_reqif_templates(r"D:\03_Requirements\00_DOORS_ReqIf_Import\092_BEVQ6_V7\TV_C1R400_MS2.xml"
