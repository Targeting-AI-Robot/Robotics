import os,time,cv2, sys, math
import tensorflow as tf
import numpy as np

from utils import utils, helpers
from builders import model_builder


def predict_segment(images, save=False):
    checkpoint_path = "./weights/weight3/DeepLabV3_plus_CamVid_people_weight3.ckpt"
    model = "DeepLabV3_plus"
    dataset = "CamVid_people"
    crop_height = 512
    crop_width = 512
    

    class_names_list, label_values = helpers.get_label_info(os.path.join(dataset, "class_dict.csv"))

    num_classes = len(label_values)
    #num_classes = 2

    print("\n***** Begin prediction *****")
    print("Dataset -->", dataset)
    print("Model -->", model)
    print("Crop Height -->", crop_height)
    print("Crop Width -->", crop_width)
    print("Num Classes -->", num_classes)
    print("Image -->", images)

    # Initializing network
    config = tf.ConfigProto()
    config.gpu_options.allow_growth = True
    sess=tf.Session(config=config)

    net_input = tf.placeholder(tf.float32,shape=[None,None,None,3])
    net_output = tf.placeholder(tf.float32,shape=[None,None,None,num_classes]) 

    network, _ = model_builder.build_model(model, net_input=net_input,
                                            num_classes=num_classes,
                                            crop_width=crop_width,
                                            crop_height=crop_height,
                                            is_training=False)

    sess.run(tf.global_variables_initializer())

    print('Loading model checkpoint weights')
    saver=tf.train.Saver(max_to_keep=1000)
    saver.restore(sess, checkpoint_path)


    print("Testing image", images)

    input_image = [cv2.resize(utils.load_image(image), (crop_width, crop_height))[:crop_height, :crop_width] for image in images]
    input_image = np.array(input_image, dtype = np.float32)/255.0
  
    st = time.time()
    output_images = sess.run(network,feed_dict={net_input:input_image})

    run_time = time.time()-st

    output_images = helpers.reverse_one_hot(output_images)
    out_vis_images = helpers.colour_binary_segmentation(output_images)

    if save:
        for i in range(len(images)):
            out_vis_image = np.array(out_vis_images[i,:,:])
            #output_image = helpers.reverse_one_hot(output_image)
            #out_vis_image = helpers.colour_code_segmentation(output_image, label_values)
            image = images[i]
            file_name = utils.filepath_to_name(image)            
            cv2.imwrite("%s_pred.png"%(file_name),cv2.cvtColor(np.uint8(out_vis_image), cv2.COLOR_RGB2BGR))
            print("Wrote image " + "%s_pred.png"%(file_name))

    #output_images = helpers.reverse_one_hot(output_images)
    #out_vis_images = helpers.colour_binary_segmentation(output_images)
    print("")
    print("segment Finished!")
    print("time elapsed",run_time)
    return out_vis_images

if __name__ == '__main__':
    save = True
    files_path = './image/'
    file_list = os.listdir(files_path)
    file_list = [files_path+filename for filename in file_list]
    print(file_list)
    #input("")
    predict_segment(file_list, save=True)
