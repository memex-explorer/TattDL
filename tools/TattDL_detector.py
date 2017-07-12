#!/usr/bin/env python

"""
TattDL detector
harry.sun@kitware.com
paul.tunison@kitware.com
"""
from __future__ import print_function
import _init_paths
from fast_rcnn.config import cfg
from fast_rcnn.test import im_detect
from fast_rcnn.nms_wrapper import nms
from utils.timer import Timer
#import matplotlib.pyplot as plt
import csv
import numpy as np
import scipy.io as sio
import caffe, os, sys, cv2
import argparse
import glob

CLASSES = ('__background__', # always index 0, total 22
           'aeroplane', 'bicycle', 'bird', 'boat',
           'bottle', 'bus', 'car', 'cat', 'chair',
           'cow', 'diningtable', 'dog', 'horse',
           'motorbike', 'person', 'pottedplant',
           'sheep', 'sofa', 'train', 'tvmonitor',
           'tattoo')

NETS = {'vgg16': ('VGG16',
                  'VGG16_faster_rcnn_final.caffemodel'),
        'tattc': ('tattc',
                  'tattc.caffemodel'),
        'tattc_voc': ('tattc_voc',
                  'tattc_voc.caffemodel'),
        'zf': ('ZF',
                  'ZF_faster_rcnn_final.caffemodel')}

#def vis_detections(im, class_name, dets, thresh=0.5):
#    """Draw detected bounding boxes."""
#    if len(dets) == 0:
#        return
#
#    im = im[:, :, (2, 1, 0)]
#    ax=plt.gca()
#    ax.imshow(im, aspect='equal')
#
#    for i in range(len(dets)):
#        bbox = dets[i, :4]
#        score = dets[i, -1]
#
#        print(bbox, score)
#
#        ax.add_patch(
#            plt.Rectangle((bbox[0], bbox[1]),
#                          bbox[2] - bbox[0],
#                          bbox[3] - bbox[1], fill=False,
#                          edgecolor='red', linewidth=3.5)
#            )
#        ax.text(bbox[0], bbox[1] - 2,
#                '{:s} {:.3f}'.format(class_name, score),
#                bbox=dict(facecolor='blue', alpha=0.5),
#                fontsize=14, color='white')
#
#    ax.set_title(('{} detections with '
#                  'p({} | box) >= {:.1f}').format(class_name, class_name, thresh), fontsize=14)
#    plt.axis('off')
#    plt.tight_layout()
#    plt.draw()


def draw_annotations(filename, annotations):
    from PIL import Image, ImageDraw

    source_img = Image.open(filename)
    draw = ImageDraw.Draw(source_img)

    for annotation in annotations:
        draw.rectangle(annotation, fill=None, outline='red')

    return source_img

def tattoo_detection(net, image_name, args):
    """Detect object classes in an image using pre-computed object proposals."""

    im_in = cv2.imread(image_name)

    if im_in is None:
        raise ValueError('cannot open %s for read' % image_name )

    rows,cols = im_in.shape[:2]
    #print([rows,cols])

    min_w, min_h = (args.min_width, args.min_height)
    if rows < min_h or cols < min_w:
        raise ValueError('Image dimensions too small on one or more axes: (%d, %d)' % (rows, cols))

    scale=1.0
    if rows >= cols:
        scale = float(args.longdim) / float(rows)
        im = cv2.resize( im_in, (int(0.5 + float(cols)*scale), args.longdim) )
    else:
        scale = float(args.longdim) / float(cols)
        im = cv2.resize( im_in, (args.longdim, int(0.5 + float(rows)*scale)) )

    # Detect all object classes and regress object bounds
    timer = Timer()
    timer.tic()
    scores, boxes = im_detect(net, im)
    timer.toc()
    seconds = '%.3f' % timer.total_time
    print('Detection took {:.3f}s for {:d} object proposals'.format(timer.total_time, boxes.shape[0]),
          file=sys.stderr)

    max_scores = scores.max(axis=0)
    #print(max_scores)
    #print(boxes.shape)

    # Visualize detections for each class
    CONF_THRESH = args.threshold
    NMS_THRESH  = args.nms_thresh

    tattoo_dets=[]
    for cls_ind, cls in enumerate(CLASSES[1:]):
        cls_ind += 1 # because we skipped background
        cls_boxes = boxes[:, 4*cls_ind:4*(cls_ind + 1)]
        cls_scores = scores[:, cls_ind]
        dets = np.hstack((cls_boxes, cls_scores[:, np.newaxis])).astype(np.float32)
        keep = nms(dets, NMS_THRESH)
        dets = dets[keep, :]

        inds = np.where(dets[:, -1] >= CONF_THRESH)[0]
        dets_filter = dets[inds]

        #vis_detections(im, cls, dets_filter, thresh=CONF_THRESH)

        if cls == 'tattoo' and len(dets_filter)>0:
            #plt.savefig(os.path.join(args.output, os.path.splitext(os.path.basename(image_name))[0] + '_det.png'))
            tattoo_dets = dets_filter

    #if args.inspect == 'v':
    #    plt.show()
    #plt.clf()

    return tattoo_dets, max_scores, seconds, scale

def parse_args():
    """Parse input arguments."""
    parser = argparse.ArgumentParser(description='tattoo detection')
    parser.add_argument('--gpu', dest='gpu_id', help='GPU device id to use [0]',
                        default=0, type=int)
    parser.add_argument("-i", "--image", dest="fname", help="image name",
                        default="step5.jpg", action="store")
    parser.add_argument("--list", help="Path to line separate image file paths. If both this and `-i` "
                                       "are given, this option is used.")
    parser.add_argument("-o", "--output", dest="output", help="output path",
                        default=".", action="store")
    parser.add_argument('-t', '--threshold', dest='threshold', help='detection threshold', default=0.3, type=float)
    parser.add_argument('-n', '--nms_thresh', dest='nms_thresh', help='nms threshold', default=0.3, type=float)
    parser.add_argument('-r', '--longdim', dest='longdim', help='resize to longdim (500)', default=500, type=int)
    parser.add_argument('--cpu', dest='cpu_mode',
                        help='Use CPU mode (overrides --gpu)',
                        action='store_true')
    parser.add_argument('-s', '--save-annotations', dest='save_annotations', help='Draw detections found to filename.annotated',
                        default=False, action='store_true')
    parser.add_argument("-v", "--results", dest="inspect", help="v: visualize; w: write to detection file",
                        default="w", action="store")
    parser.add_argument('--net', dest='demo_net', help='Network to use [tattc_voc]',
                        choices=NETS.keys(), default='tattc_voc')
    parser.add_argument('--min-width', help='Minimum image width constraint in pixels [64]',
                        default=64)
    parser.add_argument('--min-height', help='Minimum image height constraint in pixels [64]',
                        default=64, type=int)

    args = parser.parse_args()
    return args

if __name__ == '__main__':
    cfg.TEST.HAS_RPN = True  # Use RPN for proposals
    cfg.TEST.BBOX_REG = True #False
    cfg.TEST.NMS=0.3 #0.50
    cfg.TEST.RPN_NMS_THRESH=0.50
    cfg.TEST.RPN_POST_NMS_TOP_N = 5000 #20000

    args = parse_args()
    print(args, file=sys.stderr)

    prototxt = os.path.join(cfg.ROOT_DIR, 'models', NETS[args.demo_net][0], 'faster_rcnn_end2end', 'test.prototxt')
    print(prototxt, file=sys.stderr)

    caffemodel = os.path.join(cfg.ROOT_DIR, 'data', 'faster_rcnn_models', NETS[args.demo_net][1])
    print(caffemodel, file=sys.stderr)

    if not os.path.isfile(caffemodel):
        raise IOError(('{:s} not found.\nDid you run ./data/script/'
                       'fetch_faster_rcnn_models.sh?').format(caffemodel))

    if args.cpu_mode:
        caffe.set_mode_cpu()
    else:
        caffe.set_mode_gpu()
        caffe.set_device(args.gpu_id)
        cfg.GPU_ID = args.gpu_id
    net = caffe.Net(prototxt, caffemodel, caffe.TEST)

    print('\n\nLoaded network {:s}'.format(caffemodel), file=sys.stderr)

    # Warmup on a dummy image
    im = 128 * np.ones((300, 500, 3), dtype=np.uint8)
    for i in xrange(2):
        _, _= im_detect(net, im)

    writer = csv.writer(sys.stdout, delimiter=',', lineterminator='\n')
    writer.writerow(['filename', 'confidence', 'xmin', 'ymin', 'xmax', 'ymax'])

    for root, dirs, files in os.walk('/images'):
        for filename in files:
            im_name = os.path.join(root, filename)

            try:
                dets, _, _, scale = tattoo_detection(net, im_name, args)
            except ValueError, ex:
                print("! Error processing image: %s" % str(ex), file=sys.stderr)
                continue

            row = [os.path.basename(im_name)]
            annotations = []

            for d in dets:
                roi = d[:4]
                r = [int(0.5+x/scale) for x in roi]
                score = d[-1]

                writer.writerow([os.path.basename(im_name), score] + r)

                if args.save_annotations:
                    annotations.append(((r[0], r[1]), (r[2], r[3])))

            if args.save_annotations and len(annotations) > 0:
                annotated_image = draw_annotations(im_name, annotations)
                annotated_image.save('%s.annotated' % im_name, format=annotated_image.format)
