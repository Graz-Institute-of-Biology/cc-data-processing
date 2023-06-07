import os
import time
import shutil
import yaml
from PIL import Image
from PIL.ExifTags import TAGS

def file_info(file_path):
    results = {}
    i = Image.open(file_path)
    info = i._getexif()
    for tag, value in info.items():
        decoded = TAGS.get(tag, tag)
        results[decoded] = value

    date = "".join(results["DateTimeOriginal"].split(" ")[0][2:].split(":")[::-1])
    return date

def check_number_delete(path, max_num=100):
    edit_img_list = os.listdir(path)

    if len(edit_img_list) > max_num:
        n = int(len(edit_img_list)/max_num)
        del edit_img_list[::n]
        [os.remove(os.path.join(path, f)) for f in edit_img_list]
        print("reduced to: ", len(edit_img_list))
        

def rename_edit(path):
    edit_img_list = os.listdir(path)

    for f in edit_img_list:
        old_path = os.path.join(path, f)
        # date_changed = time.strftime("%d%m%y",time.localtime(os.path.getmtime(old_path)))
        date_created = file_info(old_path)
        new_path = os.path.join(path, date_created+"_"+f)
        os.rename(old_path, new_path)
        print("--------------------------")
        print(old_path)
        print("--->")
        print(new_path)
        print("--------------------------")



def work_dir(src_path, single_tree=False):
    jpg_img_list = [os.path.join(src_path, f) for f in os.listdir(src_path) if f.endswith(".JPG")]

    if single_tree:
        denom = 4
    else:
        denom = 20
    n = max(int(len(jpg_img_list)/denom), 2)
    reduced_list = jpg_img_list[::n]

    print("Reduced List to:")
    print("copying {0} files".format(len(reduced_list)))

    # [print(os.path.join(dst_path, r.split("\\")[-1])) for r in reduced_list]
    [shutil.copyfile(r, os.path.join(dst_path, r.split("\\")[-1])) for r in reduced_list]


with open("paths.yaml") as f:
    yaml_file = yaml.safe_load(f)

src_path = yaml_file["src_path"]
dst_path = yaml_file["dst_path"]

folder_items = os.listdir(src_path)
if folder_items[0] == "Tree_1":
    for sub_dir in folder_items:
        print(sub_dir)
        path = os.path.join(src_path, sub_dir)
        work_dir(path)

elif folder_items[0].endswith(".JPG") or folder_items[0].endswith(".DNG"):
    work_dir(src_path)

check_number_delete(dst_path)

rename_edit(dst_path)

