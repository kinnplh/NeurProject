import numpy as np
import cv2
from flask import Flask
from flask import render_template
from flask import request
from flask import jsonify
import os
import time
import random
import json


app = Flask(__name__)

def get_timestamp():
    return int(time.time() * 1000)

class_name_to_data_info_cache = {}
def get_data_info_by_class(class_name):
    if class_name not in class_name_to_data_info_cache:
        dataset_root = os.path.join("101_ObjectCategories", class_name)
        file_names = list(filter(lambda x: x.endswith('.jpg'), os.listdir(dataset_root)))
        data_info = list(map(lambda name: {
            "class_name": class_name, 
            "file_path": os.path.join("101_ObjectCategories", class_name, name)
        }, file_names))
        class_name_to_data_info_cache[class_name] = data_info

    return class_name_to_data_info_cache[class_name]

def generate_task(user_name, class_list, length, last_time, noise_center, noise_size):
    task_name = "{}_{}".format(user_name, get_timestamp())
    task_info_list_dir = os.path.join("static", "task_info", task_name)
    os.makedirs(task_info_list_dir)

    all_possible_data = []
    for class_name in class_list:
        all_possible_data.extend(get_data_info_by_class(class_name))
    random.shuffle(all_possible_data)
    random.shuffle(all_possible_data)
    data_list = random.sample(all_possible_data, length)
    random.shuffle(data_list)
    random.shuffle(data_list)

    for index, one_data in enumerate(data_list):
        task_info_dir = os.path.join(task_info_list_dir, str(index))
        os.makedirs(task_info_dir)

        # 读取图片并对图片进行一定的修改
        img = cv2.imread(one_data['file_path'])
        width = img.shape[0]
        height = img.shape[1]

        if noise_center is None:
            noise_center = (0.5, 0.5)
        noise_center_x = int(width * noise_center[0])
        noise_center_y = int(height * noise_center[1])

        if noise_size is None:
            noise_size = 100
        
        if noise_size < 1:
            noise_size = int(noise_size * height)

        noise_left = max(0, int(noise_center_x - noise_size / 2))
        noise_top = max(0, int(noise_center_y - noise_size / 2))
        noise_right = min(int(noise_center_x + noise_size / 2), width)  # exclude
        noise_bottom = min(int(noise_center_y + noise_size / 2), height)  # exclude

        noise_patch = (np.random.rand(noise_right - noise_left, noise_bottom - noise_top) * 255).astype(np.uint8)
        img[noise_left: noise_right, noise_top:noise_bottom, 0] = noise_patch
        img[noise_left: noise_right, noise_top:noise_bottom, 1] = noise_patch
        img[noise_left: noise_right, noise_top:noise_bottom, 2] = noise_patch

        pic_path = os.path.join(task_info_dir, "img.jpg")
        cv2.imwrite(pic_path, img)

        noise_path = os.path.join(task_info_dir, "noise.jpg")
        get_white_noise_pic(500, 500, noise_path)

        other_candidates = class_list[:]
        other_candidates.remove(one_data['class_name'])
        task_info = {
            'class_label': one_data['class_name'],
            'other_candidates': other_candidates,
            'index': index,
            'task_name': task_name,
            'last_time': last_time,
            'img_path': pic_path,
            'noise_path': noise_path
        }

        info_path = os.path.join(task_info_dir, 'info.json')
        with open(info_path, 'w') as f:
            json.dump(task_info, f)
    return task_name


def get_white_noise_pic(width, height, save_path):
    pic = np.random.rand(width, height) * 255
    pic = pic.astype(np.uint8)
    cv2.imwrite(save_path, pic)

@app.route('/generate_task', methods=['GET'])
def generate_task_view():
    class_list = []
    data_root = "101_ObjectCategories"
    dir_content = os.listdir(data_root)
    for class_name in dir_content:
        dir_path = os.path.join(data_root, class_name)
        if not os.path.isdir(dir_path):
            continue
        class_list.append({
            'name': class_name,
            'default': False
        })

    return render_template("generate_task.html", class_list=class_list)

@app.route('/generate_from_html', methods=['POST'])
def generate_from_html():
    user_name = request.json.get('user_name')
    task_length = int(request.json.get('task_length'))
    show_time = int(request.json.get('show_time'))
    noise_cx_ratio = float(request.json.get('noise_cx_ratio'))
    noise_cy_ratio = float(request.json.get('noise_cy_ratio'))
    noise_size = int(request.json.get('noise_size'))
    selected_class_list = request.json.get('selected_class_list')
    task_name = generate_task(user_name, selected_class_list, task_length, show_time, (noise_cx_ratio, noise_cy_ratio), noise_size)

    return jsonify(state='success', task_name=task_name)
    

@app.route('/task', methods=['GET'])
def show_task():
    task_name = request.args.get('tn')
    task_dir = os.path.join('static', 'task_info', task_name)
    if not os.path.exists(task_dir):
        return "不存在的任务"
    task_info_json_p = os.path.join(task_dir, 'info.json')
    if not os.path.exists(task_info_json_p):
        with open(task_info_json_p, 'w') as f:
            json.dump({'next_index': 0}, f)
    with open(task_info_json_p, 'r') as f:
        task_info_json = json.load(f)
    task_detail_path = os.path.join(task_dir, str(task_info_json['next_index']), 'info.json')
    if not os.path.exists(task_detail_path):
        return "任务已经完成"
    with open(task_detail_path, 'r') as f:
        task_info = json.load(f)

    task_info['choises'] = task_info['other_candidates'][:]
    task_info['choises'].append(task_info['class_label'])
    task_info['choises'].append('Dont_Know')

    random.shuffle(task_info['choises'])

    return render_template('main.html', task_info=task_info)

@app.route('/confirm', methods=['POST'])
def confirm_answer():
    answer = request.json.get('answer')
    print(answer)
    index = int(request.json.get('index'))
    task_name = request.json.get('tn')
    random_wait = request.json.get('randomWaitTime')
    result_path = os.path.join('static', 'task_info', task_name, str(index), 'res.json')
    with open(result_path, 'w') as f:
        json.dump({
            'answer': answer,
            'random_wait': random_wait
        }, f)
    
    task_dir = os.path.join('static', 'task_info', task_name)
    task_info_json_p = os.path.join(task_dir, 'info.json')
    with open(task_info_json_p, 'w') as f:
        json.dump({'next_index': index + 1}, f)
    
    return jsonify(state='success')

animals = ["llama", "cougar_body", "kangaroo", "wild_cat"]
insect = ["ant", "scorpion", "crab", "crayfish"]
buildings = ["buddha", "pyramid", "minaret", "pagoda"]
furniture = ["menorah", "ewer", "wheelchair", "chair"]
plants = ["water_lilly", "lotus", "bonsai", "strawberry"]

name_to_list = {
    'animals': animals,
    'insect': insect,
    'buildings': buildings,
    'furniture': furniture,
    'plants': plants
}
@app.route('/generate_task_for_user', methods=['GET'])
def generate_task_for_user():
    user_name = request.args.get('u')
    task_info_dir = os.path.join('static', 'task_info')
    all_crt_task_names = os.listdir(task_info_dir)
    task_names =[]
    for crt_tn in all_crt_task_names:
        if crt_tn.startswith(user_name):
            task_names.append(crt_tn)
    
    result = ""
    if len(task_names) == 0:
        class_names = list(name_to_list.keys())
        last_times = [20, 30, 40, 80, 160]
        random.shuffle(class_names)
        random.shuffle(last_times)
        noise_size = [0, 1/3]

        for i in range(5):
            class_name = class_names[i]
            last_time = last_times[i]

            tn1 = generate_task("{}_{}_{}_33".format(user_name, class_name, last_time), name_to_list[class_name], 20, last_time, None, 1/3)
            task_names.append(tn1)

            tn2 = generate_task("{}_{}_{}_0".format(user_name, class_name, last_time), name_to_list[class_name], 20, last_time, None, 0)
            task_names.append(tn2)
    else:
        result = "<p>已有生成结果</p>"

    for tn in task_names:
        result = result + "<p><a href='/task?tn={}' target='_blank'>{}</a></p>\n".format(tn, tn)

    return result

@app.route('/show_result', methods=['GET'])
def show_result():
    task_main_dir = task_dir = os.path.join('static', 'task_info')
    task_name_list = os.listdir(task_main_dir)
    result = ""
    for tn in task_name_list:
        task_root_dir = os.path.join(task_main_dir, tn)
        if not os.path.isdir(task_root_dir):
            continue
        tn_info_path = os.path.join(task_root_dir, 'info.json')
        if not os.path.exists(tn_info_path):
            continue
        with open(tn_info_path, 'r') as f:
            tn_info = json.load(f)
        next_index = tn_info['next_index']
        count_all = next_index
        count_right = 0
        for task_index in range(count_all):
            one_task_root = os.path.join(task_root_dir, str(task_index))
            with open(os.path.join(one_task_root, 'info.json'), 'r') as f:
                label = json.load(f)['class_label']
            with open(os.path.join(one_task_root, 'res.json'), 'r') as f:
                answer = json.load(f)['answer']
            if label == answer:
                count_right += 1
        if count_all == 0:
            continue
        score = count_right / count_all * 100
        result = result + "{},{},{},{}\n".format(tn, count_right, count_all, score)
    
    result = "task_name, right_num, tried_num, score\n" + result
    
    return'<pre>'+ result + '</pre>'


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=12123, debug=True)
