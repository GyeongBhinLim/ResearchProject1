import os
import sys
import shutil
import json
import xml.etree.ElementTree as ET

from xml.etree.ElementTree import Element, ElementTree
from tqdm import tqdm
from PIL import Image

PADDING = 20

dataset_path = sys.argv[1]
option = sys.argv[2]    # options : {'2x2','3x3'}

if option == '2x2':
    option_num = 1
elif option == '3x3':
    option_num = 4
else:
    raise ValueError('[Error] option must be either 2x2 or 3x3.')

IMAGE_FOLDER = "JPEGImages"
ANNOTATIONS_FOLDER = "Annotations"
JSON_ANNOTATIONS_FOLDER = "annotations"
IMAGE_SET_FOLDER = os.path.join("ImageSets", "Main")

ann_root, ann_dir, ann_files = next(os.walk(os.path.join(dataset_path, ANNOTATIONS_FOLDER)))
json_root, json_dir, json_files = next(os.walk(os.path.join(dataset_path, JSON_ANNOTATIONS_FOLDER)))
img_root, img_dir, img_files = next(os.walk(os.path.join(dataset_path, IMAGE_FOLDER)))
img_set_root, img_set_dir, img_set_files = next(os.walk(os.path.join(dataset_path, IMAGE_SET_FOLDER)))

#print(img_root)
#print(img_dir)
#print(img_files)

for img_file in img_files:
    
    # for debugging
    # if img_file == '000002.jpg': break
    
    print('processing ',img_file,'...')
    
    img_original_name = img_file.split('.')[0]
    img_id = img_original_name[-4:]
    anno_name = img_original_name + '.xml'
    img = Image.open(os.path.join(img_root, img_file))
    img_size = img.size
    
    if option == '2x2':
        
        x = img_size[0]
        y = img_size[1]
        x_1_2 = x / 2
        y_1_2 = y / 2
        
        for i in range(4):
            
            # crop an image and save with proper name
            
            x_start = int((i%2) * x_1_2)
            x_end = int(x_start + x_1_2)
            y_start = int((i//2) * y_1_2)
            y_end = int(y_start + y_1_2)
            
            cropped_img_name = str(option_num)+ str(i) + img_id + '.jpg'
        
            cropped_img = img.crop((x_start,y_start,x_end,y_end))
            cropped_img.save(os.path.join(img_root, cropped_img_name))
            
            # make new annotations
        
            cropped_anno_name =  str(option_num)+ str(i) + img_id + '.xml'
            
            shutil.copy(os.path.join(ann_root, anno_name),os.path.join(ann_root, cropped_anno_name))
            target_xml_path = os.path.join(ann_root, cropped_anno_name)
            target_xml = open(target_xml_path,'rt',encoding='UTF8')
            
            # modify object information
            tree = ET.parse(target_xml)
            anno = tree.getroot()
            
            # <filename>
            filename_tag = anno.find("filename")
            filename_tag.text = cropped_img_name
            
            # <size>
            cropped_img_open = Image.open(os.path.join(img_root, cropped_img_name))
            
            cropped_img_width = cropped_img_open.size[0]
            cropped_img_height = cropped_img_open.size[1]
            
            cropped_img_open.close()
            
            size_tag = anno.find('size')
            width_tag = size_tag.find('width')
            width_tag.text = str(cropped_img_width)
            height_tag = size_tag.find('height')
            height_tag.text = str(cropped_img_height)
            
            # <object>
            for object in anno.findall('object'):
                
                bndbox_tag = object.find('bndbox')
                xmin_tag = bndbox_tag.find('xmin')
                xmax_tag = bndbox_tag.find('xmax')
                ymin_tag = bndbox_tag.find('ymin')
                ymax_tag = bndbox_tag.find('ymax')
                
                if int(xmax_tag.text) - PADDING < x_start:
                    anno.remove(object)
                    continue
                if x_end < int(xmin_tag.text) + PADDING:
                    anno.remove(object)
                    continue
                if int(ymax_tag.text) - PADDING < y_start:
                    anno.remove(object)
                    continue
                if y_end < int(ymin_tag.text) + PADDING:
                    anno.remove(object)
                    continue
                
                xmin_tag.text = str(max(int(xmin_tag.text)-x_start, 0))
                xmax_tag.text = str(min(int(xmax_tag.text)-x_start, cropped_img_width))
                ymin_tag.text = str(max(int(ymin_tag.text)-y_start, 0))
                ymax_tag.text = str(min(int(ymax_tag.text)-y_start, cropped_img_height))

            #print(type(tree))
            tree.write(os.path.join(ann_root, cropped_anno_name))
            
            # todo : /Imageset/Main의 각 파일들에 대해 정보 추가
            
            object_list = []
            
            for object in anno.findall('object'):
                    
                name_tag = object.find('name')
                #print(name_tag.text)
                object_list.append(name_tag.text)
                
            #print(object_list)
            
            for txt_filename in img_set_files:
                
                txt_file = open(os.path.join(img_set_root, txt_filename),"a")
                cropped_num = str(option_num)+ str(i) + img_id
                
                if txt_filename == 'test.txt': 
                    txt_file.write('\n'+cropped_num)
                    continue
                
                txt_file_target = txt_filename.split('_')[0]
                #print(txt_file_target)
                
                if txt_file_target in object_list : 
                    txt_file.write('\n'+cropped_num+'  1')
                else:
                    txt_file.write('\n'+cropped_num+' -1')
                
                txt_file.close()
        
            target_xml.close()
            
        img.close()
            
    else:
        # to be implemented
        print()