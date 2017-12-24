import os.path
import tensorflow as tf
import helper
import warnings
from distutils.version import LooseVersion
import project_tests as tests

import time     #time counting
from datetime import timedelta

# Check TensorFlow Version
assert LooseVersion(tf.__version__) >= LooseVersion('1.0'), 'Please use TensorFlow version 1.0 or newer.  You are using {}'.format(tf.__version__)
print('TensorFlow Version: {}'.format(tf.__version__))

# Check for a GPU
if not tf.test.gpu_device_name():
    warnings.warn('No GPU found. Please use a GPU to train your neural network.')
else:
    print('Default GPU Device: {}'.format(tf.test.gpu_device_name()))


def load_vgg(sess, vgg_path):
    """
    Load Pretrained VGG Model into TensorFlow.
    :param sess: TensorFlow Session
    :param vgg_path: Path to vgg folder, containing "variables/" and "saved_model.pb"
    :return: Tuple of Tensors from VGG model (image_input, keep_prob, layer3_out, layer4_out, layer7_out)
    """
    # TODO: Implement function
    #   Use tf.saved_model.loader.load to load the model and weights
    vgg_tag = 'vgg16'
    vgg_input_tensor_name = 'image_input:0'
    vgg_keep_prob_tensor_name = 'keep_prob:0'
    vgg_layer3_out_tensor_name = 'layer3_out:0'
    vgg_layer4_out_tensor_name = 'layer4_out:0'
    vgg_layer7_out_tensor_name = 'layer7_out:0'

    tf.saved_model.loader.load(sess, [vgg_tag], vgg_path)
    graph = tf.get_default_graph()
    w1 = graph.get_tensor_by_name(vgg_input_tensor_name)
    keep = graph.get_tensor_by_name(vgg_keep_prob_tensor_name)
    vgg_layer3_out = graph.get_tensor_by_name(vgg_layer3_out_tensor_name)
    vgg_layer4_out = graph.get_tensor_by_name(vgg_layer4_out_tensor_name)
    vgg_layer7_out = graph.get_tensor_by_name(vgg_layer7_out_tensor_name)

    return w1, keep, vgg_layer3_out, vgg_layer4_out, vgg_layer7_out
tests.test_load_vgg(load_vgg, tf)


def layers(vgg_layer3_out, vgg_layer4_out, vgg_layer7_out, num_classes):
    """
    Create the layers for a fully convolutional network.  Build skip-layers using the vgg layers.
    :param vgg_layer7_out: TF Tensor for VGG Layer 3 output
    :param vgg_layer4_out: TF Tensor for VGG Layer 4 output
    :param vgg_layer3_out: TF Tensor for VGG Layer 7 output
    :param num_classes: Number of classes to classify
    :return: The Tensor for the last layer of output
    """
    # TODO: Implement function

    # call tf.stop_gradient on the 3 VGG16 layers
    # vgg_layer7_out = tf.stop_gradient(vgg_layer7_out)
    # vgg_layer4_out = tf.stop_gradient(vgg_layer4_out)
    # vgg_layer3_out = tf.stop_gradient(vgg_layer3_out)

    new_layers7_conv_1x1 = tf.layers.conv2d(vgg_layer7_out, num_classes, 1, padding='same',
                                kernel_regularizer = tf.contrib.layers.l2_regularizer(1e-3),
                                kernel_initializer=tf.truncated_normal_initializer(stddev=0.01),
                                name = "new_layers7_conv_1x1")
    new_upsample_2 = tf.layers.conv2d_transpose(new_layers7_conv_1x1, num_classes, 4, 2, padding='same',
                                kernel_regularizer = tf.contrib.layers.l2_regularizer(1e-3),
                                kernel_initializer=tf.truncated_normal_initializer(stddev=0.01),
                                name = "new_upsample_2")

    new_layer4_out_scaled = tf.multiply(vgg_layer4_out, 0.01, name='new_layer4_out_scaled')
    new_layers4_conv_1x1 = tf.layers.conv2d(new_layer4_out_scaled, num_classes, 1, padding='same',
                                kernel_regularizer = tf.contrib.layers.l2_regularizer(1e-3),
                                kernel_initializer=tf.truncated_normal_initializer(stddev=0.01),
                                name = "new_layers4_conv_1x1")
    new_add_2 = tf.add(new_upsample_2, new_layers4_conv_1x1, name="new_add_2")
    new_upsample_4 = tf.layers.conv2d_transpose(new_add_2, num_classes, 4, 2, padding='same',
                                kernel_regularizer = tf.contrib.layers.l2_regularizer(1e-3),
                                kernel_initializer=tf.truncated_normal_initializer(stddev=0.01),
                                name = "new_upsample_4")

    new_layer3_out_scaled = tf.multiply(vgg_layer3_out, 0.0001, name='new_layer3_out_scaled')
    new_layers3_conv_1x1 = tf.layers.conv2d(new_layer3_out_scaled, num_classes, 1, padding='same',
                                kernel_regularizer = tf.contrib.layers.l2_regularizer(1e-3),
                                kernel_initializer=tf.truncated_normal_initializer(stddev=0.01),
                                name = "new_layers3_conv_1x1")
    new_add_4 = tf.add(new_upsample_4, new_layers3_conv_1x1, name="new_add_4")
    new_upsample_32 = tf.layers.conv2d_transpose(new_add_4, num_classes, 16, 8, padding='same',
                                kernel_regularizer = tf.contrib.layers.l2_regularizer(1e-3),
                                kernel_initializer=tf.truncated_normal_initializer(stddev=0.01),
                                name = "new_upsample_32")

    tf.Print(new_upsample_32, [tf.shape(new_upsample_32)[1:3]])

    return new_upsample_32
tests.test_layers(layers)


def optimize(nn_last_layer, correct_label, learning_rate, num_classes):
    """
    Build the TensorFLow loss and optimizer operations.
    :param nn_last_layer: TF Tensor of the last layer in the neural network
    :param correct_label: TF Placeholder for the correct label image
    :param learning_rate: TF Placeholder for the learning rate
    :param num_classes: Number of classes to classify
    :return: Tuple of (logits, train_op, cross_entropy_loss)
    """
    # TODO: Implement function
    print(tf.trainable_variables())

    #if not reshape what do i need to do?
    logits = tf.reshape(nn_last_layer, (-1, num_classes))
    correct_label = tf.reshape(correct_label, (-1,num_classes))

    cross_entropy_loss = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(
        logits=logits, labels=correct_label))
    regularization_loss = tf.reduce_sum(tf.get_collection(tf.GraphKeys.REGULARIZATION_LOSSES))
    cross_entropy_loss += regularization_loss

    #set trainable variables (and not training the original VGG16 layers 
    trainable_variables = []
    for variable in tf.trainable_variables():
        if "new_" in variable.name:
            trainable_variables.append(variable)

    optimizer = tf.train.AdamOptimizer(learning_rate = learning_rate)
    #train_op = optimizer.minimize(cross_entropy_loss, var_list=trainable_variables)
    train_op = optimizer.minimize(cross_entropy_loss)

    return logits, train_op, cross_entropy_loss
tests.test_optimize(optimize)


def train_nn(sess, epochs, batch_size, get_batches_fn, train_op, cross_entropy_loss, input_image,
             correct_label, keep_prob, learning_rate):
    """
    Train neural network and print out the loss during training.
    :param sess: TF Session
    :param epochs: Number of epochs
    :param batch_size: Batch size
    :param get_batches_fn: Function to get batches of training data.  Call using get_batches_fn(batch_size)
    :param train_op: TF Operation to train the neural network
    :param cross_entropy_loss: TF Tensor for the amount of loss
    :param input_image: TF Placeholder for input images
    :param correct_label: TF Placeholder for label images
    :param keep_prob: TF Placeholder for dropout keep probability
    :param learning_rate: TF Placeholder for learning rate
    """
    # TODO: Implement function
    sess.run(tf.global_variables_initializer())
    print("Start training...")
    print()
    # correct_prediction = tf.equal(tf.argmax(logits, 1), tf.argmax(one_hot_y, 1))
    # accuracy_op = tf.reduce_mean(tf.cast(correct_prediction, tf.float32))

    #only initialize variables that need to be trained
    # my_variable_initializers = [var.initializer for var in tf.global_variables() if 'new_' in var.name]
    # sess.run(my_variable_initializers)
    rate = 0.001
    for ep in range(epochs):
        # total_accuracy = 0
        # total_size = 0
        l_rate = rate * (1 - int(epochs/10)*0.2)
        start_time = time.time()
        for image, label in get_batches_fn(batch_size):
            #Trainging
            _, loss = sess.run([train_op, cross_entropy_loss],
                feed_dict={input_image: image, correct_label: label, keep_prob: 0.5, learning_rate: l_rate})
        # for image, label in get_batches_fn(batch_size):
        #     #Evaluating
        #     accuracy = sess.run(accuracy_op, feed_dict={input_image: image, correct_label: label})
        #     total_accuracy += (accuracy * len(image))
        #     total_size += len(image)
        # total_accuracy = total_accuracy / total_size
        end_time = time.time()
        time_dif = end_time - start_time
        time_cost = str(timedelta(seconds=int(round(time_dif))))

        print("EPOCH {} ...".format(ep+1))
        print("Loss = {:.3f}, run time: {}s".format(loss, time_cost))

        if (ep > 0 and ep%10 == 0):
            tf.train.Saver().save(sess, ".checkpoints/fcn{}".format(ep/10))
            print("Model saved")
        print()


tests.test_train_nn(train_nn)


def run():
    num_classes = 2
    image_shape = (160, 576)
    data_dir = './data'
    runs_dir = './runs'

    epochs = 30
    batch_size = 6

    tests.test_for_kitti_dataset(data_dir)

    # Download pretrained vgg model
    helper.maybe_download_pretrained_vgg(data_dir)

    # OPTIONAL: Train and Inference on the cityscapes dataset instead of the Kitti dataset.
    # You'll need a GPU with at least 10 teraFLOPS to train on.
    #  https://www.cityscapes-dataset.com/

    with tf.Session() as sess:

        # Path to vgg model
        vgg_path = os.path.join(data_dir, 'vgg')
        # Create function to get batches
        get_batches_fn = helper.gen_batch_function(os.path.join(data_dir, 'data_road/training'), image_shape)

        # OPTIONAL: Augment Images for better results
        #  https://datascience.stackexchange.com/questions/5224/how-to-prepare-augment-images-for-neural-network

        # TODO: Build NN using load_vgg, layers, and optimize function
        input_image, keep_prob, layer3_out, layer4_out, layer7_out  = load_vgg(sess, vgg_path)
        layer_output = layers(layer3_out, layer4_out, layer7_out, num_classes)

        correct_label = tf.placeholder(tf.int32, (None, None, None, num_classes))
        learning_rate = tf.placeholder(tf.float32, name='learning_rate')

        logits, train_op, cross_entropy_loss = optimize(layer_output, correct_label,
                                                        learning_rate, num_classes)

        # TODO: Train NN using the train_nn function
        train_nn(sess, epochs, batch_size, get_batches_fn, train_op, cross_entropy_loss, input_image,
                 correct_label, keep_prob, learning_rate)

        # TODO: Save inference data using helper.save_inference_samples
        helper.save_inference_samples(runs_dir, data_dir, sess, image_shape, logits, keep_prob, input_image)

        # OPTIONAL: Apply the trained model to a video

def continue_trainning():
    sess=tf.Session()    
    #First let's load meta graph and restore weights
    saver = tf.train.import_meta_graph('.checkpoints/my_test_model-1000.meta')
    saver.restore(sess,tf.train.latest_checkpoint('./'))

    # Now, let's access and create placeholders variables and
    # create feed-dict to feed new data

    graph = tf.get_default_graph()
    image_input = graph.get_tensor_by_name("image_input:0")
    keep_prob = graph.get_tensor_by_name("keep_prob:0")
    learning_rate = graph.get_tensor_by_name("learning_rate:0")
    correct_label = graph.get_tensor_by_name("correct_label:0")
    train_op = graph.get_operation_by_name("train_op")
    cross_entropy_loss = graph.get_operation_by_name("cross_entropy_loss")
    #feed_dict ={w1:13.0,w2:17.0}

    #Now, access the op that you want to run. 
    op_to_restore = graph.get_tensor_by_name("op_to_restore:0")

    print sess.run(op_to_restore,feed_dict)

if __name__ == '__main__':
    run()
