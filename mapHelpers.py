import os
import shutil

def js_var(filename, var_name):
    with open(filename, 'r', encoding='utf-8') as file:
        data = file.readlines()

        data[0] = 'var {0} = {1}\n'.format(var_name, '{')

        with open(filename, 'w', encoding='utf-8') as file:
            file.writelines(data)

def file_copy(in_folder, out_folder, files):
    for file in files:
        shutil.copyfile(os.path.join(in_folder, file), os.path.join(out_folder, file))
