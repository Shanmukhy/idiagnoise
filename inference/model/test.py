import tensorflow as tf

class TestModel:
    def __init__(self):
        pass
    
        
    def preprocess_data(self, image, label):
            label = tf.one_hot(label, 15)  # Assuming you have 5 classes
            return image, label

    def get_val_data(self, batch_size,data):
            # Validation dataset
            self.val_ds = tf.keras.preprocessing.image_dataset_from_directory(
                data,
                validation_split=0.2,
                subset="validation",
                seed=123,
                image_size=(224, 224),
                batch_size=batch_size
            )

            self.val_ds = self.val_ds.map(self.preprocess_data)
            return self.val_ds
    
    def test(self, model_path):
        model = tf.saved_model.load(model_path)
        res = model.evaluate(self.val_ds[0], self.val_ds[1], batch_size=16)

        return res


