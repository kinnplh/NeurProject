import os
import json
import matplotlib.pyplot as plt


task_info_path = os.path.join('static', 'task_info')
task_names = os.listdir(task_info_path)
task_conf_to_result = {}
for task_name in task_names:
    task_conf_split = task_name.split('_')
    if len(task_conf_split) != 5:
        continue
    
    task_class = task_conf_split[1]
    last_time = int(task_conf_split[2])
    has_noise = (task_conf_split[3] != '0')

    task_path = os.path.join(task_info_path, task_name)
    print(task_path)

    crt_task_label = (task_class, last_time, has_noise)
    if not crt_task_label in task_conf_to_result:
        task_conf_to_result[crt_task_label] = {
            'correct_num': 0,
            'total_num': 0,
            'unknown_num': 0
        }

    crt_task_res_info = task_conf_to_result[crt_task_label]
    for i in range(20):
        task_res_dir = os.path.join(task_path, str(i))
        if not os.path.exists(task_res_dir):
            continue
        res_path = os.path.join(task_res_dir, 'res.json')
        if not os.path.exists(res_path):
            continue
        with open(os.path.join(task_res_dir, 'info.json'), 'r') as f:
            task_conf = json.load(f)
        with open(os.path.join(task_res_dir, 'res.json'), 'r') as f:
            task_result = json.load(f)
        
        crt_task_res_info['total_num'] += 1
        if task_conf['class_label'] == task_result['answer']:
            crt_task_res_info['correct_num'] += 1
        elif task_result['answer'] == "Dont_Know":
            crt_task_res_info['correct_num'] += 0.25
            crt_task_res_info['unknown_num'] += 1

print('data read finish')
last_time_list = [20, 30, 40, 80, 160]
classes = ['animals', 'buildings', 'furniture', 'insect', 'plants']
class_to_accu = {}
class_to_noise_accu = {}
for c in classes:
    class_to_accu[c] = []
    class_to_noise_accu[c] = []
class_to_accu['all'] = []
class_to_noise_accu['all'] = []
class_to_unknow = {
    'all': []
}
class_to_noise_unknow = {
    'all': []
}

for last_time in last_time_list:
    count_no_noise_all = 0
    count_no_noise_correct = 0
    count_no_noise_unknown = 0
    
    count_noise_all = 0
    count_noise_correct = 0
    count_noise_unknown = 0

    for c in classes:
        task_label_no_noise = (c, last_time, False)
        if task_label_no_noise not in task_conf_to_result:
            class_to_accu[c].append(-1)
            class_to_noise_accu[c].append(-1)
            continue
        task_res = task_conf_to_result[task_label_no_noise]
        count_no_noise_all = count_no_noise_all + task_res['total_num']
        count_no_noise_correct = count_no_noise_correct + task_res['correct_num']
        count_no_noise_unknown = count_no_noise_unknown + task_res['unknown_num']
        if task_res['total_num'] != 0:
            no_noise_ratio = task_res['correct_num'] / task_res['total_num']
            class_to_accu[c].append(no_noise_ratio)
        else:
            class_to_accu[c].append(-1)

        task_label_noise = (c, last_time, True)
        task_res_noise = task_conf_to_result[task_label_noise]
        count_noise_all = count_noise_all + task_res_noise['total_num']
        count_noise_correct = count_noise_correct + task_res_noise['correct_num']
        count_noise_unknown = count_noise_unknown + task_res_noise['unknown_num']

        if task_res_noise['total_num'] != 0:
            noise_ratio = task_res_noise['correct_num'] / task_res_noise['total_num']
            class_to_noise_accu[c].append(noise_ratio)
        else:
            class_to_noise_accu[c].append(-1)

    class_to_noise_accu['all'].append(count_noise_correct / count_noise_all)
    class_to_accu['all'].append(count_no_noise_correct / count_no_noise_all)
    class_to_unknow['all'].append(count_no_noise_unknown / count_no_noise_all)
    class_to_noise_unknow['all'].append(count_noise_unknown / count_noise_all)



print('finish')
print(class_to_noise_accu['all'])
print(class_to_accu['all'])

print(class_to_unknow['all'])
print(class_to_noise_unknow['all'])

plt.figure(1)
plt.plot(last_time_list, class_to_accu['all'], color="r", linestyle="-", marker="^", linewidth=1, label='without noise')
plt.plot(last_time_list, class_to_noise_accu['all'], color="b", linestyle="-", marker="s", linewidth=1, label='with noise')
plt.legend()
plt.xlabel('time(ms)')
plt.ylabel('accuracy')

plt.savefig('res.png')
plt.show()

plt.figure(1)
plt.plot(last_time_list, class_to_unknow['all'], color="r", linestyle="-", marker="^", linewidth=1, label='without noise')
plt.plot(last_time_list, class_to_noise_unknow['all'], color="b", linestyle="-", marker="s", linewidth=1, label='with noise')

plt.legend()
plt.xlabel('time(ms)')
plt.ylabel('Dnot_Know ratio')

plt.savefig('res_unknow.png')
plt.show()
    

