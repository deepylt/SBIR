python train_dual.py --data_root /home/lhy/sbir_cvpr2016_release/sbir_cvpr2016/chairs --name new_experiment/densenet169_dual_sphere_triplet_chairs_fg --dataset_type sketchx --trained_model checkpoints/new_expriment/densenet169_from_coco_imagenet_cls_sketchy_fg --start_epoch_label epoch_6 --load_only_feat_network --model tripletsiamese --feature_model densenet169 --feat_size 512 --phase train --num_epoch 20 --n_labels 15 --n_attrs 15 --n_fg_labels 200 --scale_size 225 --loss_type 'triplet|sphere_cls|attr,one_loss' --loss_rate '3.0,0,1' --image_type RGB --sketch_type RGB --batch_size 20 --gpu_ids 0,2,3   \
2>&1 |tee -a log/new_log/train_densenet169_dual_sphere_triplet_chairs_fg.log
