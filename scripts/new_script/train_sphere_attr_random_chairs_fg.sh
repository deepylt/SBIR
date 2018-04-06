python train.py --data_root /home/lhy/sbir_cvpr2016_release/sbir_cvpr2016/chairs --name new_expriment/densenet169_sphere_attr_random_chairs_fg --dataset_type sketchx --load_only_feat_network --model sphere_model --feature_model densenet169 --feat_size 512 --phase train --num_epoch 20 --n_fg_labels 200 --n_labels 15 --n_attrs 15 --scale_size 225 --loss_type 'triplet|sphere_cls|attr,two_loss' --loss_rate "0,1.0,1.0" --image_type RGB --sketch_type RGB --batch_size 20 --gpu_ids 0,1 --triplet_type random  --random_crop --flip \
2>&1 |tee -a log/new_log/train_densenet169_sphere_attr_random_chairs_fg.log
