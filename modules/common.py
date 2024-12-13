import os
def create_project_directory(base_path, directory_name):
    path = os.path.join(base_path, directory_name)
    # 判断是否存在目录
    if not os.path.exists(path):
        # 创建目录
        os.makedirs(path)
        print(path+"创建目录成功！")
    else:
        print(path+"目录已存在！")
        return path

    # 工程id下的一级子目录
    subdirectories = ["wave", "png"]
    
    for subdir in subdirectories:
        subdir_path = os.path.join(path, subdir)
        if not os.path.exists(subdir_path):
            os.makedirs(subdir_path)
            print(f"创建子目录 {subdir_path} 成功！")
        else:
            print(f"子目录 {subdir_path} 已存在！")
     
     # 定义二级子目录（仅针对 png 子目录）
    if "png" in subdirectories:
        png_path = os.path.join(path, "png")
        second_level_subdirs = [
            "mesh_coastline", "amplitude", "flow", "flow_nodepth", 
            "flow_tide", "griddepth", "lagtrack", "pollutant"
        ]
        for subdir in second_level_subdirs:
            subdir_path = os.path.join(png_path, subdir)
            if not os.path.exists(subdir_path):
                os.makedirs(subdir_path)
                print(f"创建二级子目录 {subdir_path} 成功！")
            else:
                print(f"二级子目录 {subdir_path} 已存在！")
    
    return path

    