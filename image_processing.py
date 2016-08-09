import numpy as np
import caffe


class PredictNet(caffe.Net):
    def __init__(self, model_file, pretrained_file, mean_file=None, channel_swap=[2, 1, 0]):
        caffe.Net.__init__(self, model_file, pretrained_file, caffe.TEST)

        # configure pre-processing
        in_ = self.inputs[0]
        self.transformer = caffe.io.Transformer({in_: self.blobs[in_].data.shape})
        self.transformer.set_transpose(in_, (2, 0, 1))
        if mean_file is not None:
            # blob = caffe.proto.caffe_pb2.BlobProto()
            # data = open(mean_file, 'rb').read()
            # blob.ParseFromString(data)
            # arr = np.array(caffe.io.blobproto_to_array(blob))
            # out = arr[0]
            # self.transformer.set_mean('data', out)

            self.transformer.set_mean('data', np.load(mean_file))
        if channel_swap is not None:
            self.transformer.set_channel_swap(in_, channel_swap)

    def predict(self, image_list):
        in_ = self.inputs[0]
        caffe_in = np.zeros((len(image_list), image_list[0].shape[2]) + self.blobs[in_].data.shape[2:],
                            dtype=np.float32)
        for i, image in enumerate(image_list):
            caffe_in[i] = self.transformer.preprocess(in_, image)
        out = self.forward_all(**{in_: caffe_in})
        predictions = out[self.outputs[0]]

        return predictions


class ImageProcessor:
    def __init__(self, style_model, style_pretrained, style_mean):
        self.style_net = PredictNet(style_model, style_pretrained, style_mean)

    # Style cnn
    def process_styles(self, img):
        styles_prob = self.style_net.predict([img])
        return styles_prob
