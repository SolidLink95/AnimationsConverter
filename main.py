import os, sys, time
from files_manage import *
import re
from smd_to_json import *
os.system('cls')



file = 'Octarock1_ANIMS_for_Maya.smd'
res = smd_file_to_json(file)
res['frames'] = res['frames'][:10]
res = scale_animation(res, 0.5)

print(str(get_bones_tree(res)))
json_to_smd_str(res,'_test.smd', commas=True)
dict_to_json_file(res, '_test.json')

