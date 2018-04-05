python train_dual_hard_neg.py --data_root /home/lhy/datasets/hair_tmp_sketch --name new_experiment/densenet169_dual_hard_hairs_fg --dataset_type hairstyle   --trained_model checkpoints/new_expriment/densenet169_from_coco_imagenet_cls_sketchy_fg --start_epoch_label epoch_6 --load_only_feat_network --model tripletsiamese --feature_model densenet169 --feat_size 128 --phase train --num_epoch 20 --n_labels 40 --n_attrs 50 --n_fg_labels 784 --scale_size 225 --loss_type 'triplet,one_loss' --image_type RGB --sketch_type RGB --batch_size 20 --gpu_ids 0,3,2   \
2>&1 |tee -a log/new_log/train_densenet169_dual_hard_hairs_fg.log
