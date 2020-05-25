import os
import sys

ROOT_PATH = os.path.dirname(__file__)
env = os.environ
PATH = env['PATH']

if not gd_path in PATH:
	env['PATH'] = ROOT_PATH + ';' + PATH 
	print("PATH variable updated.")

sys.exit()