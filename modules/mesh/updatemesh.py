def reindex_mesh(input_file, output_file):
    # 读取输入文件
    with open(input_file, 'r') as f:
        lines = f.readlines()

    # 处理第二部分：重新编号点位信息
    point_section_start = 1
    point_section_end = None

    # 寻找第四部分的开始标识行，即带有三个数字的行
    for idx, line in enumerate(lines):
        parts = line.strip().split()
        if len(parts) == 3 and parts[0].isdigit() and parts[1].isdigit() and parts[2].isdigit():
            point_section_end = idx
            break

    if point_section_end is None:
        raise ValueError("Could not find the end of point section.")

    point_mapping = {}
    point_index = 1
    points_section = []

    # 处理点位信息，并建立映射关系
    for line in lines[point_section_start:point_section_end]:
        parts = line.strip().split()
        if len(parts) >= 3:  # 假设至少有三列
            original_index = int(parts[0])
            point_mapping[original_index] = point_index
            parts[0] = str(point_index)
            points_section.append(' '.join(parts) + '\n')
            point_index += 1
        else:
            points_section.append(line)

    # 处理第四部分：更新三角形点位的索引信息
    triangle_section_start = point_section_end
    triangles_section = []
        # 记录新的三角形索引
    triangle_index = 1
   
    # 处理三角形点位索引信息，并根据映射关系更新
    for line in lines[triangle_section_start:]:
        parts = line.strip().split()
        if len(parts) == 4:
            triangle_indices = [int(parts[1]), int(parts[2]), int(parts[3])]
            updated_indices = [str(point_mapping[idx]) for idx in triangle_indices]
            # updated_line = f"{parts[0]} {' '.join(updated_indices)}\n"
            updated_line = f"{triangle_index} {' '.join(updated_indices)}\n"
            triangle_index += 1
            triangles_section.append(updated_line)
        else:
            triangles_section.append(line)

    # 写入输出文件
    with open(output_file, 'w') as f:
        f.write(lines[0])  # 写入头文件信息
        f.write(''.join(points_section))  # 写入重新编号的点位信息
        # f.write(f"{len(triangles_section)} 3 21\n")  # 写入动态确定的三角形数量
        f.write(''.join(triangles_section))  # 写入更新后的三角形点位索引信息



def reindex_mesh_data(mesh_data):
    """
    重新编号网格中的点和三角形索引，输入数据为字符串格式，输出数据为字符串格式。
    
    :param input_data: 包含输入网格数据的字符串
    :param output_data: 用于存储处理后数据的字符串（或其他输出方式）
    :return: 更新后的网格数据
    """
    # 将输入数据分行
    lines = mesh_data.splitlines()

    # 处理第二部分：重新编号点位信息
    point_section_start = 1
    point_section_end = None

    # 寻找第四部分的开始标识行，即带有三个数字的行
    for idx, line in enumerate(lines):
        parts = line.strip().split()
        if len(parts) == 3 and parts[0].isdigit() and parts[1].isdigit() and parts[2].isdigit():
            point_section_end = idx
            break

    if point_section_end is None:
        raise ValueError("Could not find the end of point section.")

    point_mapping = {}
    point_index = 1
    points_section = []

    # 处理点位信息，并建立映射关系
    for line in lines[point_section_start:point_section_end]:
        parts = line.strip().split()
        if len(parts) >= 3:  # 假设至少有三列
            original_index = int(parts[0])
            point_mapping[original_index] = point_index
            parts[0] = str(point_index)
            points_section.append(' '.join(parts))
            point_index += 1
        else:
            points_section.append(line)

    # 处理第四部分：更新三角形点位的索引信息
    triangle_section_start = point_section_end
    triangles_section = []
    triangle_index = 1
    # 处理三角形点位索引信息，并根据映射关系更新
    for line in lines[triangle_section_start:]:
        parts = line.strip().split()
        if len(parts) == 4:
            triangle_indices = [int(parts[1]), int(parts[2]), int(parts[3])]
            updated_indices = [str(point_mapping[idx]) for idx in triangle_indices]
            # updated_line = f"{parts[0]} {' '.join(updated_indices)}"
            updated_line = f"{triangle_index} {' '.join(updated_indices)}"
            triangle_index += 1
            triangles_section.append(updated_line)
        else:
            triangles_section.append(line)
    
    # 将处理后的数据合并并返回
    output_data = lines[0] + '\n'  # 写入头文件信息
    output_data += '\n'.join(points_section) + '\n'  # 写入重新编号的点位信息
    output_data += '\n'.join(triangles_section)  # 写入更新后的三角形点位索引信息

    return output_data

#示例用法
def reindex_mesh_nofile(mesh_data):
    return reindex_mesh_data(mesh_data)
    
def reindex_mesh_withfile(input_file, output_file):

    input_file = input_file
    output_file = output_file
    reindex_mesh(input_file, output_file)



# reindex_mesh("F:/Desktop/【LTGK】海洋一所/240531084643LTX/1开发域-2022/3编码实现/后端/Python-Flask/tempfile/临时mesh-zdy.mesh",
#               "F:/Desktop/【LTGK】海洋一所/240531084643LTX/1开发域-2022/3编码实现/后端/Python-Flask/tempfile/临时mesh-zdy-res.mesh")