from .gd import *

ROOT_PATH = os.path.dirname(__file__)
if not 'gd' in os.listdir(ROOT_PATH):
	shutil.copyfile(os.path.join(ROOT_PATH, 'gd.py'), os.path.join(ROOT_PATH, 'gd'))