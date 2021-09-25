import os, sys, math
import re
from copy import deepcopy
import math
from files_manage import *
from progressbar import progressbar


def rad_to_deg(rad):    return math.degrees(float(rad))

def deg_to_rad(deg):    return math.radians(float(deg))

def ready_the_input(s):
    for i in range(2,10):
        to_rep = ' ' * i
        if not to_rep in s: break
        s = s.replace(to_rep, ' ')
    s = s.replace('\n ', '\n')
    s = s.replace(' \n', '\n')
    s = s.replace(',', '.')
    return s

def zeros_str(s):
    t = str(s)
    if t == '0.0' or t == '-0.0':
        return '0'
    else:
        return t.upper()


def smd_file_to_json(file):
    data_s = ready_the_input(open(file, 'r').read())
    data = data_s.split('\n')
    size = len(data)
    res = {
        "version": 0,
        "bones": {},
        "frames": [],
    }
    res['version'] = data[0].split(' ')[-1]
    i = 2
    while True:
        if 'end' == data[i][:3]: break
        line = data[i].split(' ')
        new_bone = line[1].replace('\"','')
        res['bones'][new_bone] = [line[0],line[-1]]
        i += 1
    n_bones = len(res['bones'])
    bones = [''] * n_bones
    for bone in res['bones']:
        bones[int(res['bones'][bone][0])] = bone

    i+=2
    frame = -1
    cur_frame = {}
    for z in progressbar(range(i, size, 1)):
        if 'end' in data[z]: break
        if 'time' in data[z]:
            frame += 1
            #cur_frame['frame'] = str(frame)
            if cur_frame: res['frames'].append(dict(cur_frame))
            cur_frame = {}
        else:
            line = data[z].split(' ')
            #print(str(res))
            cur_bone = bones[int(line[-7])]
            cur_frame[cur_bone] = {
                'Translate': [(float(line[-6])),(float(line[-5])),(float(line[-4]))],
                'Rotate': [rad_to_deg(line[-3]),rad_to_deg(line[-2]),rad_to_deg(line[-1])]
            }


    return res


def json_to_smd_str(res, file, commas=False):
    out_s = ''
    out_s += f'version {res["version"]}\n'
    out_s += f'nodes\n'
    for bone in res['bones']:
        out_s += f'{res["bones"][bone][0]} \"{bone}\" {res["bones"][bone][1]}\n'
    out_s += f'end\nskeleton\n'
    size = get_frames_count(res)
    #for frame in res['frames']:
    for i in progressbar(range(size)):
        frame = res['frames'][i]
        out_s += f'time {str(i)}\n'
        for bone in frame:
            id = res['bones'][bone][0]
            out_s += id + ' '
            out_s += f'{zeros_str(frame[bone]["Translate"][0])} '
            out_s += f'{zeros_str(frame[bone]["Translate"][1])} '
            out_s += f'{zeros_str(frame[bone]["Translate"][2])} '

            out_s += f'{deg_to_rad(frame[bone]["Rotate"][0])} '
            out_s += f'{deg_to_rad(frame[bone]["Rotate"][1])} '
            out_s += f'{deg_to_rad(frame[bone]["Rotate"][2])}\n'
    out_s += f'end\n'
    if commas:
        out_s = out_s.replace('.',',')
    open(file, 'w').write(out_s)
    return out_s

def get_frames_count(res): return len(res['frames'])

def scale_animation(res, x):
    r = float(x)
    for frame in res['frames']:
        for bone in frame:
            for i in range(3):
                frame[bone]['Translate'][i] *= r
    return res

def insert_frame(dict_frame, res, index):
    if index > len(res['frames']): return res
    res['frames'].insert(index, dict(dict_frame))
    return res

def append_frame(dict_frame, res):
    size = len(res['frames'])
    return insert_frame(dict_frame, res, size)

def remove_frame(res, index):
    if index > len(res['frames']): return res
    res['frames'].pop(index)
    return res

def reverse_frames(res):
    res['frames'].reverse()
    return res

def double_frames(res):
    for i in range(get_frames_count(res)): res['frames'].append(dict(res['frames'][i]))
    return res

def dict_to_json_file(res, file):
    output = json.dumps(res, indent=4)
    output2 = re.sub(r'": \[\s+', '": [', output)
    output3 = re.sub(r',\s+', ', ', output2)
    output4 = re.sub(r'\s+\]', ']', output3)
    open(file, 'w').write(output4)

def move_bone_in_all_frames(res, bone_name, offsets):
    size = get_frames_count(res)
    for frame in res['frames']:
        if bone_name in frame:
            for k in range(3):
                frame[bone_name]['Translate'][k] += offsets[k]
    return res

def clear_json(res):
    for frame in res['frames']:
        for bone in frame:
            frame[bone] = {
                'Translate': [0.0, 0.0, 0.0],
                'Rotate': [0.0, 0.0, 0.0]
            }
    return res

def leave_one_frame(res):
    res['frames'] = res['frames'][:1]
    return res


def rename_all_bones(res, s):
    bones_names = list(res['bones'])
    for bone in bones_names:
        res['bones'][bone + s] = deepcopy(res['bones'][bone])
        del res['bones'][bone]
    for frame in res['frames']:
        for bone in frame:
            frame[bone + s] = deepcopy(frame[bone])
            del frame[bone]
    return res

def get_bones_tree(res):
    bones_tree = {}
    bones_names = list(res['bones'])
    for bone_name in bones_names: bones_tree[bone_name] = []
    for bone_name in list(bones_names):
        ID = res['bones'][bone_name][0]
        for bone in bones_names:
            if res['bones'][bone][1] == ID:
                bones_tree[bone_name].append(bone)
        bones_names.remove(bone_name)
    return bones_tree

def animation_to_anim(res):
    out_s = """animVersion 1.1;
mayaVersion 2022;
timeUnit pal;
linearUnit cm;
angularUnit deg;
startTime 0;\n"""
    size = len(res['frames'])
    out_s += f'endTime {str(size)};\n'
    bones_tree = get_bones_tree(res)
    dims = ['X','Y','Z']
    for bone in bones_tree:
        if bone:
            for dim in dims:
                out_s += f'anim scale.scale{dim} scale{dim} {bone} 0 {str(len(bone))} 0;\n'
                out_s += 'animData {\n  input time;\n  output unitless;\n  weighted 0;\n  preInfinity constant;\n'
                out_s += '  keys {\n'
                for i,frame in enumerate(res['frames']): pass
    #for bone in bones:
