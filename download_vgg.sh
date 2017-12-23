1. layers and weights of pretrained VGG-16 should keep frozen or should keep trainable? 
2. there is no need reshaped the model’s output tensor needs to be reshaped into 2D, but I got an error in this code.
    cross_entropy_loss = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(
        logits=nn_last_layer, labels=correct_label))

TensorFlow’s softmax function (and tf.nn.softmax_cross_entropy_with_logits, for that matter) 
accepts tensors of any shape and will apply the softmax function on the last axis of the tensor. 
There is hence no need to reshape the output of the model, 
especially because you only end up reshaping it back into the image dimensions after applying softmax anyway, 
so it’s just clock cycles wasted for your GPU.
You should NOT reshape your model output. 