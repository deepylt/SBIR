from torch.utils import data
import numpy as np
from torchvision import transforms
from util.util import to_rgb, load_bndboxs_size
import os
import re
from PIL import Image
import json
import cv2
import pickle
import time
from collections import defaultdict
"""Sketch Dataset"""


class CoCoHEDDataset(data.Dataset):
    # augment_types=[""], levels="cs", mode="train",flag="two_loss", train_split=20,  pair_inclass_num=5,pair_outclass_num=0,edge_map=True):
    def __init__(self,  opt):
        # parameters setting
        self.opt = opt
        self.root = opt.data_root
        photo_types = opt.sketchy_photo_types
        sketch_types = opt.sketchy_sketch_types
        mode = opt.phase
        self.photo_imgs = []
        self.photo_neg_imgs = []
        self.fg_labels = []
        self.labels = []
        self.bndboxes = []
        self.sizes = []
        tri_mode = mode
        if mode == 'test':
            mode = 'val'  
        save_filename = mode+"_coco_hed_list.pkl"  
        self.creat_transform() 
        if os.path.exists(save_filename):
            data = pickle.load(open(save_filename, 'rb'))
            self.photo_imgs = data['photo_imgs']
            self.photo_neg_imgs = data['photo_neg_imgs']
            self.fg_labels = data['fg_labels']
            self.labels = data['labels']
            self.bndboxes = data['bndboxes']
            self.n_labels = data['n_labels']
            self.n_fg_labels = data['n_fg_labels'] 
            self.sizes = data['sizes']
        else:
            root = os.path.join(self.root, mode + '2017')
            annotation_root = os.path.join(self.opt.annotation_root, 'instances_'+mode+"2017.json")

            self.creat_index(annotation_root)
            
            for i, img_id in enumerate(self.anns.keys()):
                self.photo_imgs.append(self.id2path(img_id, root))
                self.photo_neg_imgs.append(self.id2path(img_id, root))
                self.fg_labels.append(i)
                self.labels.append(self.cats[img_id])
                self.bndboxes.append(self.anns[img_id]['bbox'])
                self.sizes.append({'width':self.imgs[img_id]['width'], "height":self.imgs[img_id]['height']})
            self.n_labels = len(self.catToImgs)
            self.n_fg_labels = len(self.fg_labels)


            self.filter_bndbox()
            pickle.dump({'photo_imgs': self.photo_imgs, 'photo_neg_imgs': self.photo_neg_imgs,
                     'fg_labels': self.fg_labels, 'labels': self.labels, 'bndboxes': self.bndboxes,
                     'n_labels': self.n_labels, 'n_fg_labels': self.n_fg_labels, 'sizes':self.sizes}, open(save_filename, 'wb'))


            
        print('Total COCO Class:{} Total Num:{}'.format(self.n_labels, self.n_fg_labels))



        
        
        pair_inclass_num, pair_outclass_num = self.opt.pair_num

        if tri_mode == "train" and not self.opt.model == 'cls_model':
            self.generate_triplet(pair_inclass_num, pair_outclass_num)

        print("{} pairs loaded. After generate triplet".format(len(self.photo_imgs)))

    def id2path(self, img_id, root):
        path = os.path.join(root, '0' * (12 - len(str(img_id))) + str(img_id) + '_000.png')
        return path

    def creat_transform(self):
        transforms_list = []
        if self.opt.random_crop:
            transforms_list.append(transforms.Resize((256, 256)))
            transforms_list.append(transforms.RandomCrop(
                (self.opt.scale_size, self.opt.scale_size)))
        else:
            transforms_list.append(transforms.Resize(
                (self.opt.scale_size, self.opt.scale_size)))
        if self.opt.flip:
            transforms_list.append(transforms.RandomVerticalFlip())
        #transforms_list.append(transforms.Resize((self.opt.scale_size, self.opt.scale_size)))
        transforms_list.append(transforms.ToTensor())
        self.transform_fun = transforms.Compose(transforms_list)
        self.test_transform_fun = transforms.Compose([transforms.Resize(
            (self.opt.scale_size, self.opt.scale_size)), transforms.ToTensor()])

    def creat_index(self, annotation_file):
        print('loading annotations into memory...')
        tic = time.time()
        annotations = json.load(open(annotation_file, 'r'))
        print('Done (t={:0.2f}s)'.format(time.time()- tic))

        print('creating index...')
        anns, cats, imgs = {}, {}, {}
        imgToAnns,catToImgs = defaultdict(list),defaultdict(list)
        if 'annotations' in annotations:
            for ann in annotations['annotations']:
                imgToAnns[ann['image_id']].append(ann)
                anns[ann['image_id']] = ann
                cats[ann['image_id']] = ann['category_id']
            print('annotations and categroy_id load done')
        if 'images' in annotations:
            for img in annotations['images']:
                imgs[img['id']] = img
            print('images load done')    
        #if 'categories' in annotations:
        #    for cat in annotations['categories']:
        #        cats[cat['image_id']] = cat
        #    print('cats load done')
        if 'annotations' in annotations and 'categories' in annotations:
            for ann in annotations['annotations']:
                catToImgs[ann['category_id']].append(ann['image_id'])

        print('index created!')

        self.anns = anns
        self.cats = cats
        #print(self.anns, self.cats)
        self.catToImgs = catToImgs
        self.imgToAnns = imgToAnns

    def transform(self, pil, bndbox):

        # print(np.array(pil).shape)
        if self.opt.image_type == 'GRAY':
            pil = pil.convert('L')
        else:
            pil = pil.convert('RGB')
        pil_numpy = np.array(pil)
        pil_numpy = self.crop(pil_numpy, bndbox)
        #pil_numpy = cv2.resize(pil_numpy,(self.opt.scale_size,self.opt.scale_size))

        # if self.opt.image_type == 'GRAY':
        #    pil_numpy = pil_numpy.reshape(pil_numpy.shape + (1,))
        if self.transform_fun is not None:
            pil = Image.fromarray(pil_numpy)
            pil_numpy = self.transform_fun(pil)

        return pil_numpy
    def resize_bndbox(self, ori_bndbox, ori_size, new_size):
        x1, x2, y1, y2 = [bb[0], bb[0]+bb[2], bb[1], bb[1]+bb[3]]

        new_bndbox = []
        new_bndbox.append(ori_bndbox[0] * new_size['width'] / ori_size['width'])
        new_bndbox.append(ori_bndbox[1] * new_size['height'] / ori_size['height'])
        new_bndbox.append(ori_bndbox[2] * new_size['width'] / ori_size['width'])
        new_bndbox.append(ori_bndbox[3] * new_size['height'] / ori_size['height'])
        #uprint(ori_size, new_size)
        return new_bndbox
    def filter_bndbox(self):

        photo_imgs, photo_neg_imgs, fg_labels, labels, bndboxes = [], [], [], [], []
        for photo_img, photo_neg_img, fg_label, label, bndbox, size in zip(self.photo_imgs, self.photo_neg_imgs, self.fg_labels, self.labels, self.bndboxes, self.sizes):
            photo_pil = Image.open(photo_img)
            photo_pil = photo_pil.convert('L')
            pil_numpy = np.array(photo_pil)
            new_size = {'width':pil_numpy.shape[1], 'height':pil_numpy.shape[0]}
            bndbox = self.resize_bndbox(bndbox, size, new_size)
            # if bndbox['ymax'] < pil_numpy.shape[0] - 1  and bndbox['xmax'] < pil_numpy.shape[1] - 1 and bndbox['ymax'] - bndbox['ymin'] > 1 and bndbox['xmax'] - bndbox['xmin'] > 1 :
            pil_numpy = self.crop(pil_numpy, bndbox)
            pil_numpy = cv2.Canny(pil_numpy, 0, 200)
            # print(pil_numpy.shape)
            # np.all(np.array(pil_numpy.shape) > 0):
            if pil_numpy is not None:
                if pil_numpy.shape[0] > 0 and pil_numpy.shape[1] > 0 :
                    photo_imgs.append(photo_img)
                    photo_neg_imgs.append(photo_neg_img)
                    fg_labels.append(fg_label)
                    labels.append(label)
                    bndboxes.append(bndbox)
        self.photo_imgs, self.photo_neg_imgs, self.fg_labels, self.labels, self.bndboxes = photo_imgs, photo_neg_imgs, fg_labels, labels, bndboxes
    def crop(self, pil_numpy, bb):
        # print(pil_numpy.shape)
        x1, x2, y1, y2 = [bb[0], bb[0]+bb[2], bb[1], bb[1]+bb[3]]

        x1, x2, y1, y2 = int(x1), int(x2), int(y1), int(y2)
        #print(x1,x2,y1,y2, pil_numpy.shape)
        if x2 == pil_numpy.shape[1]:
            x2 = x2 - 1
        if y2 == pil_numpy.shape[0]:
            y2 = y2 - 1
        if len(pil_numpy.shape) == 3:

            return pil_numpy[y1:y2, x1:x2, :]
        elif len(pil_numpy.shape) == 2:
            return pil_numpy[y1:y2, x1:x2]

    def load_sketch(self, pil, bndbox):
        if self.opt.sketch_type == 'RGB':
            pil = pil.convert('RGB')
        else:
            pil = pil.convert('L')
        pil_numpy = np.array(pil)
        # print(pil_numpy.shape)
        pil_numpy_ori = pil_numpy
        pil_numpy = self.crop(pil_numpy, bndbox)
            
        # print(pil_numpy.shape)
        if not self.opt.sketch_type == 'RGB':
            pil_numpy = cv2.Canny(pil_numpy, 0, 200)
        if pil_numpy is None:
            print(pil_numpy_ori.shape)
        # print(pil_numpy.shape)
        #pil_numpy = cv2.resize(pil_numpy,(self.opt.scale_size,self.opt.scale_size))
        # if self.opt.sketch_type == 'RGB':
        #    pil_numpy = to_rgb(pil_numpy)
        # elif self.opt.sketch_type == 'GRAY':
        #    pil_numpy = pil_numpy.reshape(pil_numpy.shape + (1,))
        if self.transform_fun is not None:
            pil_numpy = Image.fromarray(pil_numpy)
            pil_numpy = self.transform_fun(pil_numpy)

        return pil_numpy

    def __len__(self):
        return len(self.photo_imgs)

    def __getitem__(self, index):
        photo_img, photo_neg_img, fg_label, label = self.photo_imgs[
            index], self.photo_neg_imgs[index], self.fg_labels[index], self.labels[index]
        bndbox = self.bndboxes[index]

        photo_pil, photo_neg_pil = Image.open(
            photo_img), Image.open(photo_neg_img)
        # if self.transform is not None:
        sketch_pil = self.load_sketch(photo_pil, bndbox)
        photo_pil = self.transform(photo_pil, bndbox)
        photo_neg_pil = self.transform(photo_neg_pil, bndbox)
        #print(sketch_pil.size(), photo_pil.size())
        #print(label, fg_label)
        return sketch_pil, photo_pil, photo_neg_pil, label, fg_label, label

    def generate_triplet(self, pair_inclass_num, pair_outclass_num=0):
        photo_neg_imgs, photo_imgs, fg_labels, labels = [], [], [], []

        labels_dict = [[] for i in range(self.n_labels)]
        for i, label in enumerate(self.labels):
            labels_dict[label].append(i)
        fg_labels_dict = [[] for i in range(self.n_fg_labels)]
        for i, fg_label in enumerate(self.fg_labels):
            fg_labels_dict[fg_label].append(i)

        for i, (photo_img, fg_label, label) in enumerate(zip(self.photo_imgs, self.fg_labels, self.labels)):
            num = len(labels_dict[label])
            inds = [labels_dict[label].index(i)]
            for j in range(pair_inclass_num):
                ind = np.random.randint(num)
                while ind in inds or ind in fg_labels_dict[fg_label]:
                    ind = np.random.randint(num)
                inds.append(ind)
                photo_neg_imgs.append(self.photo_imgs[labels_dict[label][ind]])
                photo_imgs.append(photo_img)
                fg_labels.append(fg_label)
                labels.append(label)

        num = len(self.photo_imgs)
        for i, (photo_img, fg_label, label) in enumerate(zip(self.photo_imgs, self.fg_labels, self.labels)):
            inds = [i]
            for j in range(pair_outclass_num):
                ind = np.random.randint(num)
                while ind in inds or ind in fg_labels_dict[fg_label] or ind in labels_dict[label]:
                    ind = np.random.randint(num)
                inds.append(ind)
                photo_neg_imgs.append(self.photo_imgs[ind])
                photo_imgs.append(photo_img)
                fg_labels.append(fg_label)
                labels.append(label)

        self.photo_neg_imgs, self.photo_imgs, self.fg_labels, self.labels = photo_neg_imgs, photo_imgs, fg_labels, labels
