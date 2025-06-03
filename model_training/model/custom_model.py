from tensorflow.keras.applications import ResNet50, MobileNet, MobileNetV2, VGG16, VGG19, Xception
from tensorflow.keras.models import Sequential

import tensorflow.keras as keras
from tensorflow.keras import layers
from tensorflow import data as tf_data

import tensorflow as tf
from tensorflow.keras.layers import Dense, Flatten
from tensorflow.keras.optimizers import Adam


class Model:
    def __init__(self, num_classes):
        self.num_classes = num_classes
        
    def load_fortraining(self, model, h, w, lr):
        self.input_shape = (h,w,3)
        self.model = self.custom_enb7(self.input_shape, self.num_classes)
        self.model.compile(
            optimizer=Adam(learning_rate=lr), 
            loss='categorical_crossentropy', 
            metrics=['accuracy']
        )
    
    def is_model_validated(self, accuracy=0.5):
        if accuracy < self.final_val_accuracy:
            return True
        return False
    
    def save(self, model_path):
        self.model.save(model_path, options=tf.saved_model.SaveOptions(experimental_custom_gradients=False))

    def load_frompretrained(self, model_path, lr):
        model = keras.models.load_model(model_path)
        model.compile(optimizer=Adam(learning_rate=lr), loss='categorical_crossentropy', metrics=['accuracy'])
        self.model = model

    def train(self, train_ds, val_ds, epochs):
        self.history = self.model.fit(
            train_ds,
            epochs=epochs,
            validation_data=val_ds,
        )

    def get_val_test_accuracy(self):
        val_accuracy = self.history.history['val_accuracy']
        self.final_val_accuracy = val_accuracy[-1]

    def custom_enb7_block(self, x, filters, kernel_size=3, stride=1):
        x = layers.Conv2D(filters, kernel_size, strides=stride, padding="same")(x)
        x = layers.BatchNormalization()(x)
        x = layers.Activation("swish")(x)  # Swish activation function
        return x

    def custom_enb7(self, input_shape, num_classes):
        inputs = keras.Input(shape=input_shape)

        # Stem
        x = self.custom_enb7_block(inputs, 64, kernel_size=3, stride=2)

        # Blocks
        for filters in [64, 128, 256, 512, 1280]:
            x = self.custom_enb7_block(x, filters)
            x = self.custom_enb7_block(x, filters, stride=2)

        # Top
        x = layers.GlobalAveragePooling2D()(x)
        if num_classes == 2:
            units = 1
            activation = 'sigmoid'
        else:
            units = num_classes
            activation = 'softmax'
        x = layers.Dropout(0.25)(x)
        outputs = layers.Dense(units, activation=None)(x)

        return keras.Model(inputs, outputs)
