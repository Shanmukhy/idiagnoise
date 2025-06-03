from tensorflow.keras.applications import ResNet50, MobileNet, MobileNetV2, VGG16, VGG19, Xception
from tensorflow.keras.models import Sequential

import tensorflow.keras as keras
from tensorflow.keras import layers
from tensorflow import data as tf_data

import tensorflow as tf
from tensorflow.keras.layers import Dense, Flatten
from tensorflow.keras.optimizers import Adam

# Custom layer to replace ModuleWrapper
class CustomModuleWrapper(tf.Module):
    def __init__(self, module, **kwargs):
        super(CustomModuleWrapper, self).__init__(**kwargs)
        self.module = module

    def __call__(self, inputs, training=False):
        return self.module(inputs, training=training)

class RapidModel:
    def __init__(self, num_classes):
        self.model_list = [ResNet50, MobileNet, MobileNetV2, VGG16, VGG19, Xception]
        self.model_name_lst = ["resnet50", "mobilenet", "mobilenetv2", "vgg16", "vgg19", "xception"]
        self.num_classes = num_classes
        
    def get_val_test_accuracy(self):
        val_accuracy = self.history.history['val_accuracy']
        self.final_val_accuracy = val_accuracy[-1]
        
    
    def is_model_validated(self, accuracy=0.5):
        if accuracy < self.final_val_accuracy:
            return True
        return False

    def load_fortraining(self, model_name, img_h, img_w, lr):
        if model_name in self.model_name_lst:
            model_indx = self.model_name_lst.index(model_name)
            backbone = self.model_list[model_indx]
            print("Selected model:", model_name[model_indx])
        else:
            print(f"Invalid model name: {model_name}")
            raise ValueError
        
        # Training the model
        model = Sequential()

        pretrained_model = backbone(
            include_top=False,
            input_shape=(img_h, img_w, 3),
            pooling='avg',
            classes=self.num_classes,
            weights='imagenet'
        )

        # Replace ModuleWrapper with CustomModuleWrapper
        for i, layer in enumerate(pretrained_model.layers):
            if isinstance(layer, tf.Module):
                pretrained_model.layers[i] = CustomModuleWrapper(layer)

        for layer in pretrained_model.layers:
            layer.trainable = False

        model.add(pretrained_model)
        model.add(Flatten())
        model.add(Dense(512, activation='relu'))
        model.add(Dense(self.num_classes, activation='softmax'))

        # Compile the model
        model.compile(optimizer=Adam(learning_rate=lr), loss='categorical_crossentropy', metrics=['accuracy'])

        self.model = model

    def train(self, train_ds, val_ds, epochs):
        # Train the model
        self.history = self.model.fit(
            train_ds,
            validation_data=val_ds,
            epochs=epochs
        )

    def save(self, model_path):
        self.model.save(model_path)

    def load_frompretrained(self, model_path, lr):
        model = tf.keras.models.load_model(model_path)
        for layer in model:
            layer.trainable = True
        
        # Compile the model
        model.compile(optimizer=Adam(learning_rate=lr), loss='categorical_crossentropy', metrics=['accuracy'])

        self.model = model
