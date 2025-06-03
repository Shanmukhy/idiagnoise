from tensorflow.python.compiler.tensorrt import trt_convert as trt
import tensorflow as tf

class TFTRTCompile:
    def __init__(self, model_path, quantize_type):
        self.model_path = model_path
        self.quantize_type = quantize_type
 
    def compile(self):
        # Instantiate the TF-TRT converter
        if self.quantize_type == "fp32":
            converter = trt.TrtGraphConverterV2(
            input_saved_model_dir=self.model_path,
            precision_mode=trt.TrtPrecisionMode.FP32
            )
        elif self.quantize_type == "fp16":
            converter = trt.TrtGraphConverterV2(
            input_saved_model_dir=self.model_path,
            precision_mode=trt.TrtPrecisionMode.FP16
            )
        elif self.quantize_type == "int8":
            converter = trt.TrtGraphConverterV2(
            input_saved_model_dir=self.model_path,
            precision_mode=trt.TrtPrecisionMode.INT8
            )
        else:
            raise ValueError
        
        # Convert the model into TRT compatible segments
        if self.quantize_type == "int8":
            self.predictor = converter.convert(calibration_input_fn=self.input_fn)
        else:
            self.predictor = converter.convert()
 
        self.converter = converter
 
    
    def input_fn(self):
        MAX_BATCH_SIZE=32
        batch_size = MAX_BATCH_SIZE
        for image_batch, labels_batch in self.val_ds:
            x = image_batch
            yield [x]
 
    def build(self, val_ds):
        self.val_ds = val_ds
        self.converter.build(input_fn=self.input_fn)
 
    def save(self, save_path):
        self.converter.save(output_saved_model_dir=save_path)
 
    def print_summary(self):
        self.converter.summary()