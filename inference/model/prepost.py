import base64
import numpy as np 
import tensorflow as tf 

class PrePost:
    def __init__(self):
        pass


    def img_proc(self, file, shape, dtype):

        file = bytes(file, encoding='utf-8')         
        image = base64.b64decode(file)         
        image_np = np.frombuffer(image, dtype=dtype)         
        #image_np = image_np.astype("float32")         
        image_np = np.reshape(image_np, (shape[0], shape[1])) / np.iinfo(dtype).max         
        image_np = image_np.astype('float32')         
        img = np.zeros((224,224, 3), dtype="float32")         
        img[:,:, 0] = image_np         
        img[:,:, 1] = image_np         
        img[:,:, 2] = image_np         
        image_np = np.expand_dims(img, axis=0)
        input = tf.convert_to_tensor(image_np, dtype="float32")

        return input

    def get_argmax_res(self, result):
        for key in result:
            pred = result[key]
        
        res = int(np.argmax(pred, axis=1)[0])
        return res