import zipfile
import os

class ZipManager:
    def __init__(self, data):
        self.data = data
        self.filename = None
        self.path = None
        
    def write(self, filename):
        self.filename = filename
        self.data.save(filename)
                
    def list_zip_data(self):
        with zipfile.ZipFile(self.filename, 'r') as zip:
            file_list = zip.namelist()
        return file_list

    def extract(self, path):
        self.path = path
        try:
            with zipfile.ZipFile(self.filename, 'r') as zip:
                zip.extractall(path)
                self.set_num_classes(path)
        except Exception as e:
            print("Error:",e)
        
    def set_num_classes(self, path):
        self.NUM_CLASSES = len(os.listdir(path))
            
    def validate_dataset(self):
        L = []
        # Traversing through Test
        for root, dirs, files in os.walk(self.path):
            L.append((root, dirs, files))
        
        print("List of all sub-directories and files:")
        for i in L:
            # Should have main-folder at extracted path.
            if len(i[1]) == 1:
                print("Dataset: ", i[1])
                continue
            # Should have sub-folders at extracted path.
            elif len(i[1]) == self.NUM_CLASSES:
                if len(i[2]) == 0:
                    print("Class Folders are validated.")
                else:
                    ValueError("Root folder should not consist of any file.")
            elif len(i[1]) == 0:
                if len(i[2]) >= 2:
                    for name in i[2]:
                        if (name.lower()).endswith('.jpg') or (name.lower()).endswith('.png') or (name.lower()).endswith('.bmp') or (name.lower()).endswith('.dcm'):
                            continue
                        else:
                            raise ValueError("Wrong data format")
                else:
                    raise ValueError("Wrong data format")
            else:
                raise ValueError("Wrong dataset directory structure!")